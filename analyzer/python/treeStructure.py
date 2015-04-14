#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#          sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

import ROOT
import pickle

######## CLASS ANALYSIS #####################################################

class MISAnalysis:

    def __init__(self, box, cfg):
        self.cfg = cfg # PConfig object
        self.box = box # MISBox object
        self.outcode = 0
        self.result = None
        self.cutValue = 0.
        self.entries = {}
        self.yields = {}
        self.sigLike = None # MISBox object
        self.bkgLike = None # MISBox object
        self._log = ""

    def fetchResults(self):
        logResults = []
        minMCEventsSig = 0
        minMCEventsBkg = 0
        sigEff = 0.
        bkgEff = 0.
        cut = 0.

        with open(self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["log"], "r") as logFile:
            logResults = [ line for line in logFile.read().split("\n") if line != "" ]
            sigEff = float(logResults[0])
            bkgEff = float(logResults[1])
            cut = float(logResults[4])
            
        if bkgEff > 0.:
            # Everything seems alright. Fetch signal and background efficiencies, and the tree entries and yields for all the processes.

            self.result = (sigEff, bkgEff)
            self.cutValue = cut
            self.log("Analysis result: " + str(sigEff) " sig. efficiency vs. " + str(bkgEff) + " bkg. efficiency at MVA cut value = " + str(cut) + ".")

            for split in ["sig", "bkg"]:
                self.log("Results for " + split + "-like part.")
                self.entries[split] = {}
                self.yields[split] = {}

                for proc in self.cfg.procCfg:

                    file = ROOT.TFile(self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["outputname"] + "_" + split + "like_proc_" + proc["name"] + ".root", "READ")
                    if file.IsZombie():
                        print "== Error opening " + fileName + "."
                        self.log("Error opening " + fileName + ".")
                        sys.exit(1)

                    myTree = file.Get(proc["treename"])
                    self.entries[split][ proc["name"] ] = myTree.GetEntries()

                    histName = "tempHist_" + self.cfg.mvaCfg["name"] + "_" + split + "_" + str(self.box.level)
                    myTree.Draw("This->GetReadEntry()>>" + histName, proc["evtweight"], "goff")
                    tempHist = ROOT.TH1F(ROOT.gDirectory.Get(histName))
                    effEntries = tempHist.Integral()
                    self.yields[split][ proc["name"] ] = float(self.cfg.mvaCfg["lumi"])*float(proc["xsection"])*effEntries/int(proc["genevents"])
                    del tempHist
                    
                    file.Close()

                    self.log("Process " + proc["name"] + ": " + str(self.entries[split][ proc["name"] ]) + "MC events, " + "{0:.1f}".format(self.yields[split][ proc["name"] ]) + " expected events.")
                self.log("")

        else:
            # Something went wrong. Leave self.result = None, meaning that the MVA will not be considered anymore => investigate what went wrong.

            with self.locks["stdout"]:
                print "== Level " + str(self.box.level) + ": Something went wrong in analysis " + self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "."
            self.log("Analysis FAILED!")

    def printLog(self):
        print "MVA " + self.cfg.mvaCfg["name"] + ":"
        print _log
        print "\n\n"

    def log(self, line = ""):
        self._log += line + "\n"

######## CLASS BOX ##########################################################

class MISBox:

    def __init__(self, parent = None, cfg = None):
        self.parent = parent # Another MISBox
        if self.parent is not None:
            self.cfg = copy.deepcopy(self.parent.cfg) # PConfig object
            self.level = self.parent.level + 1
            self.parent.daughters.append(self)
        if self.cfg is not None:
            self.cfg = cfg
        else
            self.cfg = None
            self.level = 1
            self.name = ""
        self.MVA = [] # MISAnalysis objects
        self.goodMVA = None # MISAnalysis object
        self.daughters = [] # MIXBox objects
        self.isEnd = False
        self._log = ""

    def __str__(self):
        _str = ""
        if self.isEnd:
            _str = "=="
            for i in range(self.level):
                _str += "="
            _str += " Box " + self.name + ", level" + str(self.level) + ":\n"
                for proc in self.cfg.procCfg:
                    _str = "==="
                    for i in range(self.level):
                        _str += "="
                    _str += " Process " + proc["name"] + ": " + proc["entries"] + " MC events, " + proc["yield"] + " expected events.\n"
                _str += "\n"
        else:
            for box in daugthers:
                _str += box.__str__() + "\n"
        return _str

    def write(self, outFile, count):
        if self.isEnd:
            count += 1
            outFile.write(str(count) + ":" + box.name + ":")
            for proc in self.cfg.procCfg:
                outFile.write(proc["name"] + "=" + proc["yield"] + ",")
            outFile.write("\n")
        else:
            for box in daughters:
                box.write(outFile, count)
    
    def printLog(self):
        print "Box " + self.name + ", level" + str(self.level) + ":"
        print _log
        print "\n\n"

        for mva in self.MVA:
            mva.printLog()
            print "\n\n"

        for box in daughters:
            box.printLog()

    def log(self, line = ""):
        self._log += line + "\n"

######## CLASS TREE #########################################################

class MISTree:
    
    def __init__(self, cfg):
        self.cfg = cfg # PConfig object
        self.firstBox = MISBox() # MISBox object
        self.firstBox.cfg = copy.deepcopy(self.cfg) # PConfig object
        self.firstBox.cfg = self.cfg.mvaCfg["name"]
        self._log = ""

    def __str__(self):
        return firstBox.__str__()

    def printLog(self):
        print "Tree Log:"
        print _log
        print "\n\n"
        self.firstBox.printLog()

    def save(self, fileName=""):
        if fileName == "":
            fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "_tree.p"

        self.log("Saving analysis results to pickle file " + fileName + ".")
        
        with open(fileName, "wb") as outFile:
            myPickler = pickle.Pickler(outFile)
            myPickler.dump(self)

    def write(self, fileName=""):
        count = 0
        
        if fileName == "":
            fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "_results.out"
        
        self.log("Writing analysis results to " + fileName + ".")
        
        with open(fileName, "w") as outFile:
            self.firstBox.write(outFile, count)

    def log(self, line = ""):
        self._log += line + "\n"
        
