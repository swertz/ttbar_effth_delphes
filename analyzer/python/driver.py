#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#          sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

argConf = 1
argExec = 2

from ROOT import gROOT, kTRUE
import sys
import os
from threading import Thread
from threading import RLock
import time
import copy
from subprocess import call

from utils import PConfig
import treeStrategyOps
import treeStrategyMIS

from treeStructure import MISTree
from treeStructure import MISBox
from treeStructure import MISAnalysis

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
        defineNewCfgs(self.box, self.locks)
        
        # Define threads with the new configurations
        threads = []
        for thisMVA in self.box.MVA:
            myThread = launchMisChief(thisMVA, self.locks)
            threads.append(myThread)
        
        with self.locks["stdout"]:
            self.box.log("Will start " + str(len(threads)) + " threads.")
            print "== Level {0}: Starting {1} mva threads.".format(self.box.level, len(threads))

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
                print "== Level {0}: All analyses seem to have failed. Stopping branch.".format(self.box.level)
            return 0

        # Decide what to do next and define next boxes. Boxes which are not "isEnd" will define new tries.
        analyseResults(self.box, self.locks)
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

######## MODULAR TREE ############################################################
# Define new configuration objects based on chosen tree-building strategy 

def defineNewCfgs(box, locks):

    if box.cfg.mvaCfg["mode"] == "operators":
        return treeStrategyOps.defineNewCfgs(box, locks)

    elif box.cfg.mvaCfg["mode"] == "MIS":
        return treeStrategyMIS.defineNewCfgs(box, locks)

    else:
        print "== Tree building strategy not properly defined."
        sys.exit(1)

# Decide what to based on the results of the tmvas:

def analyseResults(box, locks):

    if box.cfg.mvaCfg["mode"] == "operators":
        return treeStrategyOps.analyseResults(box, locks)

    elif box.cfg.mvaCfg["mode"] == "MIS":
        return treeStrategyMIS.analyseResults(box, locks)

    else:
        print "== Tree building strategy not properly defined."
        sys.exit(1)

######## CLASS LAUNCHMISCHIEF #####################################################
# Launch a MVA based on a configuration passed by tryMisChief

class launchMisChief(Thread):
    def __init__(self, MVA, locks):
        Thread.__init__(self)
        self.MVA = MVA
        self.locks = locks

    def run(self):
        def valueToString(value):
            if isinstance(value, list):
                return ','.join(str(x) for x in value)
            else:
                return str(value)

        # write the config file that will be used for this analysis
        with open(self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + ".conf", "w") as configFile:

            self.MVA.log("Writing config file.")

            i = 0
            for name, proc in self.MVA.cfg.procCfg.items():

                configFile.write("[proc_" + str(i) + "]\n")
                configFile.write("name = %s\n" % name)

                for key, value in proc.items():
                    configFile.write(key + " = " + valueToString(value) + "\n")

                configFile.write("\n")
                i += 1

            configFile.write("[analysis]\n")

            for key, value in self.MVA.cfg.mvaCfg.items():
                configFile.write(key + " = " + valueToString(value) + "\n")

        # launch the program on this config file
        commandString = sys.argv[argExec] + " " + self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + ".conf"
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

######## MAIN #############################################################

def driverMain(cfgFile):
    print "============================================="
    print "================= MISchief =================="
    print "============================================="
    
    print "== Reading configuration file {0}".format(cfgFile)
    myConfig = PConfig(cfgFile)
    myTree = MISTree(myConfig)
   
    # A locked RLock will force other threads to wait for the lock to be released before going on.
    # This will for instance avoid printing output to be mixed between the threads.
    locks = {}
    locks["stdout"] = RLock()
    
    # Define main thread object
    mainThread = tryMisChief(myTree.firstBox, locks)
    
    # Tell ROOT to shut the hell up
    gROOT.SetBatch(kTRUE);
    
    print "== Starting main thread."
    mainThread.start()
    mainThread.join()
    print "== Main thread stopped."
    
    print myTree
    myTree.write()
    myTree.plotResults()
    myTree.save()
    
    print "============================================="

if __name__ == "__main__":
    driverMain(sys.argv[argConf])
