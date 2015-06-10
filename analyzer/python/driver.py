#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#          sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

# System imports

import sys
import os
from threading import Thread, RLock, Semaphore
import time
import copy
from subprocess import call
import yaml
import argparse
import importlib
import warnings

# ROOT import

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True # Necessary to avoid clash between ROOT's and this program's command-line options
ROOT.gROOT.SetBatch(ROOT.kTRUE) # Tell ROOT to shut the hell up

# Project imports

from utils import PConfig
from utils import valueToString

from treeStructure import MISTree
from treeStructure import MISBox
from treeStructure import MISAnalysis

# This is needed because using TTreeFormula::EvalInstance() produces a Python warning,
# while everything runs absolutely fine.
# See https://root.cern.ch/phpBB3/viewtopic.php?f=14&t=14213
warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='creating converter.*' )

######## ARGUMENTS ##############################################################

usage = """%(prog)s -c config -t tmva -s strategyModule"""
description = """Build tree of boxes separating processes from each other."""

myParser = argparse.ArgumentParser(usage=usage, description=description, add_help=True)
myParser.add_argument("-c", "--config",
        required = True,
        help = "Driver configuration file in YML format."
        )
myParser.add_argument("-t", "--tmva",
        required = True,
        help = "Relative path to tmva executable."
        )
myParser.add_argument("-s", "--strategy",
        required = True,
        help = "Name of the trategy module."
        )
myArgs = myParser.parse_args()

cfgFile = myArgs.config
tmvaExec = myArgs.tmva
strategyPath = myArgs.strategy

if not os.path.isfile(cfgFile):
    raise RunTimeError("Invalid config file.")
if not os.path.isfile(tmvaExec):
    raise RunTimeError("Invalid tmva executable.")
strategyModule = importlib.import_module(strategyPath)

######## CLASS TRYMISCHIEF #####################################################

class tryMisChief(Thread):

    def __init__(self, box, locks):
        Thread.__init__(self)
        self.box = box
        self.locks = locks

    def run(self):
        self.box.log("Starting try.")

        if not os.path.isdir(self.box.cfg.mvaCfg["outputdir"]):
            os.makedirs(self.box.cfg.mvaCfg["outputdir"])

        # Define new configurations based on the one passed to this "try":
        strategyModule.defineNewCfgs(self.box, self.locks)

        if len(self.box.MVA) == 0:
            self.box.log("Something went wrong in defining the tmva's.")
            with self.locks["stdout"]:
                print "== Level {0}, box {1}: Something went wrong when defining the tmva's.".format(self.box.level, self.box.name)
        
        # Define threads with the new configurations
        threads = []
        for thisMVA in self.box.MVA:
            myThread = launchMisChief(thisMVA, self.locks)
            threads.append(myThread)
        
        self.box.log("Will start " + str(len(threads)) + " threads.")
        with self.locks["stdout"]:
            print "== Level {0}, box {1}: Starting {2} mva threads.".format(self.box.level, self.box.name, len(threads))

        # Launching the analyses and waiting for them to finish
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        self.box.log("Threads finished.")

        # Exclude the ones that didn't end successfully (no result tuple)
        goodMVAs = [ mva for mva in self.box.MVA if mva.result is not None ]
        if len(goodMVAs) == 0:
            self.box.log("All analysis failed. Stopping branch.")
            self.box.isEnd = True
            with self.locks["stdout"]:
                print "== Level {0}, box {1}: All analyses seem to have failed. Stopping branch.".format(self.box.level, self.box.name)
            return 0

        # Decide what to do next and define next boxes. Boxes which are not "isEnd" will define new tries.
        strategyModule.analyseResults(self.box, self.locks)
        nextBoxes = [ box for box in self.box.daughters if not box.isEnd ]

        # Launch and define next threads, if any
        if len(nextBoxes) != 0:
            nextThreads = []

            for thisBox in nextBoxes:
                thisThread = tryMisChief(thisBox, self.locks)
                nextThreads.append(thisThread)

                self.box.log("Will launch " + str(len(nextThreads)) + " new tries and pass the hand.")

            for thread in nextThreads:
                thread.start()

            for thread in nextThreads:
                thread.join()

        self.box.log("Try finished successfully.")

######## CLASS LAUNCHMISCHIEF #####################################################
# Launch a MVA based on a configuration passed by tryMisChief

class launchMisChief(Thread):
    def __init__(self, MVA, locks):
        Thread.__init__(self)
        self.MVA = MVA
        self.locks = locks

    def run(self):
        self.locks["semaph"].acquire()
        
        # write the config file that will be used for this analysis
        configFileName = os.path.join(self.MVA.cfg.mvaCfg["outputdir"], self.MVA.cfg.mvaCfg["name"] + ".yml")
        with open(configFileName, "w") as configFile:

            self.MVA.log("Writing config file.")

            mvaConfig = {}
            mvaConfig["datasets"] = self.MVA.cfg.procCfg
            mvaConfig["analysis"] = self.MVA.cfg.mvaCfg

            yaml.dump(mvaConfig, configFile)

        # launch the program on this config file
        commandString = tmvaExec + " " + configFileName
        commandString += " > " + self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + ".log 2>&1"

        # it would be annoying if, say, outputdir was "&& rm -rf *"
        if commandString.find("&&") >= 0 or commandString.find("|") >= 0:
            with self.locks["stdout"]:
                print "== Looks like a security issue..."
            sys.exit(1)

        self.MVA.log("Calling " + commandString + ".")

        result = call(commandString, shell=True)

        self.MVA.log("Finished. Output code = " + str(result) + ".")
        self.MVA.outcode = result
        if result != 0:
            with self.locks["stdout"]:
                print "== Something went wrong (error code " + str(result) + ") in analysis " + self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + "."
        else:
            self.MVA.fetchResults(self.locks)
        
        self.locks["semaph"].release()

######## APPLY SKIMMING #####################################################
# Apply the skimming of the input rootFiles before to launch the whole process. Redefines also the cfg with the skimmedRootFiles as input files

def applySkimming(config):

    stringFormula = config.mvaCfg["skimmingFormula"] 
    skimmedRootFilesDir = config.mvaCfg["outputdir"] + "/skimmedRootFiles/"
    if not os.path.isdir(skimmedRootFilesDir): os.system("mkdir " + skimmedRootFilesDir)

    print "== Skimming the input rootFiles (if not already done) with the following formula : \n {0}".format(stringFormula)
    for name,process in config.procCfg.items():

        skimFileName = skimmedRootFilesDir + name + "_skimmed_" + str(hash(stringFormula)) + ".root" 
        if not os.path.isfile(skimFileName):

            inChain = ROOT.TChain(process["treename"])
            for rootFile in process["path"]:
                inChain.Add(rootFile)
            inEntries = inChain.GetEntries()

            print "== Start skimming "+ name + " having ", inEntries, " entries..."
            formulaName = stringFormula.replace(' ', '_')
            formula = ROOT.TTreeFormula(formulaName, stringFormula, inChain)
            inChain.SetNotify(formula)
            
            skimFile = ROOT.TFile(skimFileName, "recreate")
            skimChain = inChain.CloneTree(0)
            
            for entry in xrange(inEntries):
                inChain.GetEntry(entry)
                if formula.EvalInstance():
                    skimChain.Fill()

            skimChain.Write()
            skimmedEntries = skimChain.GetEntries()
            print "== Skimmed rootFile written under " + skimFileName + ". It has now ", skimmedEntries, " entries."
            skimFile.Close()
        process["path"] = [skimFileName]

######## MAIN #############################################################

def driverMain(cfgFile):
    print "============================================="
    print "================= MISchief =================="
    print "============================================="

    print "== Reading configuration file {0}".format(cfgFile)

    myConfig = PConfig(cfgFile)

    if myConfig.mvaCfg["applySkimming"]:
        applySkimming(myConfig)
    
    myTree = MISTree(myConfig)
   
    # A locked RLock will force other threads to wait for the lock to be released before going on.
    # This will for instance avoid printing output to be mixed between the threads.
    # The semaphore will enable limiting the total number of tmva instances
    locks = {}
    locks["stdout"] = RLock()
    locks["semaph"] = Semaphore(myConfig.mvaCfg["maxTMVA"])
    
    # Define main thread object
    mainThread = tryMisChief(myTree.firstBox, locks)
    
    print "== Starting main thread."
    mainThread.start()
    mainThread.join()
    print "== Main thread stopped."
    
    print myTree
    myTree.write()
    myTree.plotResults()
    myTree.save()
    myTree.drawTreeStructure()
    
    print "============================================="

if __name__ == "__main__":
    driverMain(cfgFile)
