#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#          sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

import ROOT
import pickle
import sys
import os
import copy

from utils import weightsToString, getEntriesEffentriesYieldTuple

######## CLASS ANALYSIS #####################################################

class MISAnalysis:

    def __init__(self, box, cfg):
        self.cfg = cfg # PConfig object
        self.name = box.name + "/" + self.cfg.mvaCfg["name"]
        self.box = box # MISBox object
        self.outcode = 0
        self.result = None
        self.cutValue = 0.
        self.entries = {} # Holds the number of entries for sig and bkg-like subsets
        self.effEntries = {} # Holds the effective number of entries (sum of weights) for sig and bkg-like subsets
        self.yields = {} # Holds the yields for sig and bkg-like subsets
        self.yieldsErrors = {} # Holds the yields errors for sig and bkg-like subsets
        self.sigLike = None # MISBox object
        self.bkgLike = None # MISBox object
        self._log = ""

    def fetchResults(self, locks):
        sigEff = 0.
        bkgEff = 0.
        cut = 0.

        with open(self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["log"], "r") as logFile:
            logResults = [ line for line in logFile.read().split("\n") if line != "" ]
            sigEff = float(logResults[0])
            bkgEff = float(logResults[1])
            cut = float(logResults[2])
            
            self.log("Analysis result: " + str(sigEff) + " sig. efficiency vs. " + str(bkgEff) + " bkg. efficiency at MVA cut value = " + str(cut) + ".")
            
        if bkgEff > 0. and bkgEff < 1. and sigEff > 0. and sigEff < 1.:
            # Everything seems alright. Fetch signal and background efficiencies, and the tree entries and yields for all the processes.

            self.result = (sigEff, bkgEff)
            self.cutValue = cut

            for split in ["Sig", "Bkg"]:
                self.log("Results for " + split + "-Like part.")
                self.entries[split] = {}
                self.effEntries[split] = {}
                self.yields[split] = {}
                self.yieldsErrors[split] = {}

                for name, proc in self.cfg.procCfg.items():

                    fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["outputname"] + "_" + split + "Like_proc_" + name + ".root"
                    yieldTuple = getEntriesEffentriesYieldTuple(fileName, proc, self.cfg.mvaCfg["lumi"])

                    if yieldTuple is None:
                        print "== Couldnt retrieve yield histogram from file " + fileName + "."
                        self.log("Couldnt retrieve yield histogram from file " + fileName + ".")
                        sys.exit(1)
                        
                    self.entries[split][name] = yieldTuple[0]
                    self.effEntries[split][name] = yieldTuple[1]
                    self.yields[split][name] = yieldTuple[2]
                    self.yieldsErrors[split][name] = yieldTuple[3]

                    self.log("Process " + name + ": " + str(self.entries[split][name]) + " MC events, " + "{0:.1f}".format(self.yields[split][name]) + " expected events.")
                
                self.log("")

        else:
            # Something went wrong. Leave self.result = None, meaning that the MVA will not be considered anymore => investigate what went wrong.
            print "== Level " + str(self.box.level) + ": Something went wrong in analysis " + self.name + "."
            self.log("Analysis failed: efficiencies don't make sense.")

    def __str__(self):
        return "MVA " + self.name

    def printLog(self):
        print "MVA " + self.name + ":\n" + self._log

    def log(self, line = ""):
        self._log += line + "\n"

######## CLASS BOX ##########################################################

class MISBox:

    def __init__(self, parent = None, cfg = None, type = ""):
        """ Build new box.
        A PConfig object cfg MUST be given as argument.
        If no parent is specified, the box is taken to be the first one. 
        If a parent is specified, the relation of this box the parent ("Sig" or "Bkg") must be specified. """

        if cfg is None:
            print "== Error: A PConfig object must be specified to build the box!"
            sys.exit(1)

        self.cfg = cfg
        self.parent = parent # Another MISBox
        self.MVA = [] # MISAnalysis objects
        self.goodMVA = None # MISAnalysis object
        self.daughters = [] # MISBox objects
        self.isEnd = False
        self._log = ""
        self.effEntries = {}
        self.entries = {}
        self.yields = {}
        self.yieldsErrors = {}
        
        if self.parent is not None:
            self.level = self.parent.level + 1
            self.parent.daughters.append(self)
            if self.parent.goodMVA is None:
                print "== Error: A parent box must have a goodMVA."
                sys.exit(1)
            self.name = self.parent.name + "/" + self.parent.goodMVA.cfg.mvaCfg["name"]
            if type == "Sig":
                self.name += "_SigLike"
            elif type == "Bkg":
                self.name += "_BkgLike"
            else:
                print "== Error: If a parent box is specified, the relation (Sig/Bkg) must also be specified."
                sys.exit(1)
            self.type = type
            self.effEntries = self.parent.goodMVA.effEntries[type]
            self.entries = self.parent.goodMVA.entries[type]
            self.yields = self.parent.goodMVA.yields[type]
            self.yieldsErrors = self.parent.goodMVA.yieldsErrors[type]
        
        else:
            self.cfg = cfg
            self.level = 1
            self.name = self.cfg.mvaCfg["name"]

    def __str__(self):
        _str = "=="
        
        for i in range(self.level):
            _str += "="
        _str += " Box " + self.name + ", level " + str(self.level) + ":\n"
        
        for name in self.cfg.procCfg.keys():
            _str += "==="
            for i in range(self.level):
                _str += "="
            _str += " Process {}: {} MC events, {:.2f} expected events.\n".format(name, self.entries[name], self.yields[name])
        _str += "\n"
        
        return _str

    def printBelow(self):
        print self
        
        if not self.isEnd:
            for box in self.daughters:
                box.printBelow()
    
    def returnByPath(self, path):
        path = path.strip()
        path = path.strip("/")

        for configurable in self.daughters + self.MVA:
            if path == configurable.name:
                return configurable
            elif configurable.name in path:
                return configurable.returnByPath(path)

        raise Exception("Could not find object {} in {}.".format(path, self.name))

    def fillEndBoxes(self, endBoxes):
        if self.isEnd:
            endBoxes.append(self)
        else:
            for box in self.daughters:
                box.fillEndBoxes(endBoxes)

    def write(self, outFile):
        if self.isEnd:
            outFile.write(":" + self.name + ":")
            for name, proc in self.cfg.procCfg.items():
                outFile.write(name + "=" + str(proc["yield"]) + ",")
            outFile.write("\n")
        else:
            for box in self.daughters:
                box.write(outFile)
    
    def printLog(self):
        print "Box " + self.name + ", level" + str(self.level) + ":\n" + self._log + "\n"

    def printLogBelow(self):
        self.printLog()
        
        if not self.isEnd:
            for box in self.daughters:
                box.printLogBelow()

    def log(self, line = ""):
        self._log += line + "\n"

######## CLASS TREE #########################################################

class MISTree:
    
    def __init__(self, cfg = None, fileName = ""):
        if cfg is not None:
            self.cfg = cfg # PConfig object
            self.firstBox = MISBox(cfg = copy.deepcopy(self.cfg)) # MISBox object
            for name, proc in cfg.procCfg.items():
                yieldTuple = getEntriesEffentriesYieldTuple(proc["path"], proc, cfg.mvaCfg["lumi"])
                self.firstBox.entries[name] = yieldTuple[0]
                self.firstBox.effEntries[name] = yieldTuple[1]
                self.firstBox.yields[name] = yieldTuple[2]
                self.firstBox.yieldsErrors[name] = yieldTuple[3]
            self._log = ""
        elif fileName != "":
            with open(fileName, "rb") as outFile:
                myPickler = pickle.Unpickler(outFile)
                self = myPickler.load()
        else:
            print "== Error: MISTree must be initialized from either a PConfig object, or a Pickle file."
            sys.exit(1)

    def __str__(self):
        return "= Tree " + self.cfg.mvaCfg["name"] + "\n"
    
    def printBelow(self):
        print self
        self.firstBox.printBelow()

    # ====> Maybe keep a variable in MISTree, updated each time a box is set to "isEnd"?
    def getEndBoxes(self):
        endBoxes = []
        self.firstBox.fillEndBoxes(endBoxes)
        return endBoxes

    def returnByPath(self, path):
        path = path.strip()
        path = path.strip("/")

        if path == self.firstBox.name:
            return self.firstBox
        else:
            return self.firstBox.returnByPath(path)

    def printLog(self):
        print "Tree Log:\n" + self._log

    def printLogBelow(self):
        self.printLog()
        self.firstBox.printLogBelow()

    ######## PLOT RESULTS #############################################################
    # Create ROOT file with, for each process, plots:
    # - one bin/branch (=yields)
    # - 2D plot with efficiencies for each branch
    # - to do: juxtaposing the MVA outputs for each branch
    
    def plotResults(self, fileName = ""):
        if fileName == "":
            fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "_hists.root"
        self.log("Writing histograms to " + fileName + ".")
        print "== Writing histograms to " + fileName + "."

        file = ROOT.TFile(fileName, "RECREATE")

        # Retrieve all the final boxes
        endBoxes = self.getEndBoxes()
        endBoxes.sort(key = lambda box: box.name)

        nBr = len(endBoxes)
        nProc = len(self.cfg.procCfg)
        nDataSample = self.cfg.countProcesses([-5])
        nProcForBrComp = nProc - nDataSample
        nBins = int(self.cfg.mvaCfg["histbins"])
        nFitBins = int(self.cfg.mvaCfg["fitbins"])

        branchTotals = ROOT.TH1D("branch_tot", "Branch totals", nBr, 0, nBr)
        lst = ROOT.TList()

        branchEffs = ROOT.TH2D("branch_effs", "Branch efficiencies (%)", nBr, 0, nBr, nProc, 0, nProc)
        branchYields = ROOT.TH2D("branch_yields", "Branch yields", nBr, 0, nBr, nProc, 0, nProc)
        branchComps = ROOT.TH2D("branch_comps", "Branch compositions (%)", nBr, 0, nBr, nProcForBrComp, 0, nProcForBrComp)
        branchYieldsForComp = ROOT.TH2D("branch_yieldsForComp", "Branch yields for comp", nBr, 0, nBr, nProcForBrComp, 0, nProcForBrComp)
        treeYields = {} # Key = process name, entry = histogram of branch yields
        treeMVAs = {} # Key = process name, entry = histogram of juxtaposed MVA outputs
 
        # Sorting the processes by name
        processes = self.cfg.procCfg.items()
        processes.sort(key = lambda item: item[0], reverse = True)
        i = 0
        countForComp = 0

        for name, proc in processes:
    
            treeYields[name] = ROOT.TH1D(name + "_yields", "Branch yields for " + name, nBr, 0, nBr)
            treeYields[name].Sumw2()
            
            #treeMVAs[name] = TROOT.H1D(name + "_MVAs", "MVA histograms for " + name, nBrSkimmed*nFitBins, 0, nBrSkimmed*nFitBins)
            #treeMVAs[name].Sumw2()
    
            # FIXME: Support multiple input files (maybe not needed)?
            procFile = ROOT.TFile(proc["path"][0], "READ")
            procTree = procFile.Get(proc["treename"])
            procTree.Draw("Entries$>>tempHist", "abs(%s)" % proc["evtweight"], "goff")
            tempHist = ROOT.TH1F(ROOT.gDirectory.Get("tempHist"))
            procTotEffEntriesAbs = 0.
            # This has to be done because TH1F::Integral() sometimes mysteriously returns 0.0
            for k in range(1, tempHist.GetNbinsX()):
                procTotEffEntriesAbs += tempHist.GetBinContent(k)
            del tempHist
            procTotEntries = procTree.GetEntries()
            procFile.Close()

            branchYields.GetYaxis().SetBinLabel(i+1, name)
            branchEffs.GetYaxis().SetBinLabel(i+1, name)
 
            for j,box in enumerate(endBoxes):

                branchEffEntries = box.effEntries[name]
                branchYield = box.yields[name]
                branchYieldError = box.yieldsErrors[name]
            
                branchEffs.SetBinContent(j+1, i+1, 100.*branchEffEntries/procTotEffEntriesAbs)
                branchEffs.GetXaxis().SetBinLabel(j+1, box.name)
    
                treeYields[name].SetBinContent(j+1, branchYield)
                treeYields[name].SetBinError(j+1, branchYieldError)
                treeYields[name].GetXaxis().SetBinLabel(j+1, box.name)
    
                branchYields.SetBinContent(j+1, i+1, branchYield)
                branchYields.GetXaxis().SetBinLabel(j+1, box.name)

            #for j,branch in enumerate(skimmedTree):
    
            #    branchFile = ROOT.TFile(branch + ".root", "READ")
            #    procHist = branchFile.Get(proc["name"] + "_output").Rebin(nBins/nFitBins)
            #    
            #    for k in range(1, nFitBins+1):
            #        treeMVAs[ proc["name"] ].SetBinContent(j*nFitBins+k, procHist.GetBinContent(k))
    
            #    branchFile.Close()
    
            file.cd()
    
            treeYields[name].SetEntries(procTotEntries)
            treeYields[name].Write()

            if proc["signal"] != -5 :
                branchComps.GetYaxis().SetBinLabel(countForComp+1, name)
                for j,box in enumerate(endBoxes):
                    branchYieldsForComp.SetBinContent(j+1, countForComp+1, box.yields[name]) 
                    branchComps.GetXaxis().SetBinLabel(j+1, box.name)
                lst.Add(treeYields[name])
                countForComp += 1

            #treeMVAs[ proc["name"] ].Write()
            i += 1
    
        branchTotals.Merge(lst)
        for j in range(1, nBr+1):
            for i in range(1, nProcForBrComp+1):
                    branchComps.SetBinContent(j, i, 100.* branchYieldsForComp.GetBinContent(j, i) / branchTotals.GetBinContent(j) )
    
        file.cd()

        if ROOT.gROOT.GetVersionInt() >= 60400:
            ROOT.gStyle.SetPalette(57)
        else:
            ROOT.gStyle.SetPalette(54)
   
        branchEffs.Write()
        cnv = ROOT.TCanvas("cnv_branch_effs", "Branch Efficiencies", 900, 600)
        pad = ROOT.TPad("branch_effs", "Branch Efficiencies", 0, 0, 1, 1, 0)
        pad.Draw()
        pad.cd()
        branchEffs.SetStats(ROOT.kFALSE)
        if nBr <= 15:
            branchEffs.Draw("COL,TEXT,Z")
        else:
            branchEffs.Draw("COL,Z")
        cnv.Write()
        cnv.Print(os.path.join(self.cfg.mvaCfg["outputdir"], self.cfg.mvaCfg["name"] + "_" + cnv.GetName() + ".png"), "png")
        del pad
        del cnv
    
        branchYields.Write()
        cnv = ROOT.TCanvas("cnv_branch_yield", "Branch Yields", 900, 600)
        pad = ROOT.TPad("branch_yield", "Branch Yields", 0, 0, 1, 1, 0)
        pad.Draw()
        pad.cd()
        branchYields.SetStats(ROOT.kFALSE)
        pad.SetLogz()
        if nBr <= 15:
            branchYields.Draw("COL,TEXT,Z")
        else:
            branchYields.Draw("COL,Z")
        cnv.Write()
        cnv.Print(os.path.join(self.cfg.mvaCfg["outputdir"], self.cfg.mvaCfg["name"] + "_" + cnv.GetName() + ".png"), "png")
        del pad
        del cnv
    
        branchComps.Write()
        cnv = ROOT.TCanvas("cnv_branch_comps", "Branch Compositions", 900, 600)
        pad = ROOT.TPad("branch_comps", "Branch Compositions", 0, 0, 1, 1, 0)
        pad.Draw()
        pad.cd()
        branchComps.SetStats(ROOT.kFALSE)
        pad.SetLogz()
        if nBr <= 15:
            branchComps.Draw("COL,TEXT,Z")
        else:
            branchComps.Draw("COL,Z")
        cnv.Write()
        cnv.Print(os.path.join(self.cfg.mvaCfg["outputdir"], self.cfg.mvaCfg["name"] + "_" + cnv.GetName() + ".png"), "png")
        del pad
        del cnv

        file.Close()

    def save(self, fileName = ""):
        if fileName == "":
            fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "_tree.p"

        print "== Saving tree to pickle file " + fileName + "."
        self.log("Saving analysis results to pickle file " + fileName + ".")
        
        with open(fileName, "wb") as outFile:
            myPickler = pickle.Pickler(outFile)
            myPickler.dump(self)

    def write(self, fileName = ""):
        if fileName == "":
            fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "_results.out"
        
        print "== Writing box yields to " + fileName + "."
        self.log("Writing box yields to " + fileName + ".")
        
        with open(fileName, "w") as outFile:
            self.firstBox.write(outFile)

    def log(self, line = ""):
        self._log += line + "\n"

    def drawTreeStructure(self, node = None):
        start = False
        if node is None:
            start = True
            node = self.firstBox
            self._graphviz_header = 'digraph tree {\n'
            self._graphviz_header += '\tgraph [fontname = "helvetica"];'
            self._graphviz_header += '\tedge [fontname = "helvetica"];'
            self._graphviz_header += '\tnode [fontname = "helvetica", style=filled];'
            self._graphviz_content = ''

        if start:
            color = '#ECE5CE'
        elif node.type == "Sig":
            color = '#C5E0DC'
        else:
            color = '#E08E79'

        if node.isEnd:
            self._graphviz_header += '\t"%s" [color="%s", fontcolor="#000000", label="End node"];\n' % (node.name, color)
            return
        
        for child in node.daughters:
            label = child.name.split('/')[-1].replace('_', ' ').replace('SigLike', '').replace('BkgLike', '')
            self._graphviz_content += '\t"%s" -> "%s";\n' % (node.name, child.name)

        self._graphviz_header += '\t"%s" [color="%s", fontcolor="#000000", label="%s"];\n' % (node.name, color, label)

        for child in node.daughters:
            self.drawTreeStructure(child)

        if start:
            fileName = self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "_tree.dot"

            print "== Saving tree structure to " + fileName + "."
            print "== Run 'dot -Tpdf %s -o %s' to produce a PDF file of the tree structure" % (fileName, fileName.replace('.dot', '.pdf'))
            print "== Run 'dot -Tpng %s -o %s' to produce a PNG file of the tree structure" % (fileName, fileName.replace('.dot', '.png'))
            self.log("Saving tree structure to " + fileName + ".")
            
            with open(fileName, "wb") as outFile:
                outFile.write(self._graphviz_header)
                outFile.write('\n')
                outFile.write(self._graphviz_content)
                outFile.write('}')

            del self._graphviz_header
            del self._graphviz_content

