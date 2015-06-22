#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#          sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

import copy
import sys
import ROOT
import yaml

######## valueToString #####################################################

def valueToString(value):
    if isinstance(value, list):
        return ','.join(str(x) for x in value)
    else:
        return str(value)

######## CLASS MC STUDY CONFIG #####################################################

class PMCConfig:

    def __init__(self, cfgFileName):

        self.cfg = {}
        self.params = []

        with open(cfgFileName, "r") as cfgFile:
            
            # splitting the lines, skipping empty lines and comment lines (starting with a "#")
            cfgContent = cfgFile.read()
            lines = [ line for line in cfgContent.split("\n") if line is not "" ]
            lines = [ line for line in lines if line[0] is not "#" ]
            # splitting between the ":"
            lines = [ line.split("=") for line in lines ]
            for line in lines:
                # removing blank spaces before and after the "="
                line = [ item.strip() for item in line ]
                if line[0].find("param") >= 0:
                        paramSet = {}
                        paramList = line[1].split(";")
                        for param in paramList:
                            name = param.split(":")[0]
                            name = name.strip()
                            value = param.split(":")[1]
                            value = value.strip()
                            value = float(value)
                            paramSet[name] = value
                        self.params.append(paramSet)
                else:
                    self.cfg[line[0]] = line[1]

######## CLASS PRESULT #############################################################
# Class contains a list containing, for each branch:
# [id, branch name, {proc1: yield, proc2: yield, ...}]
# It can be initialize from a result file given by driver.py,
# Or from an already existing PResult (giving the structure of the tree),
# and a RDS giving yields for each process in each branch.

class PResult:

    def __init__(self):
        self.branches = []

    def iniFromFile(self, cfgFileName):

        with open(cfgFileName, "r") as cfgFile:
            # splitting the lines, skipping empty lines and comment lines (starting with a "#")
            cfgContent = cfgFile.read()
            lines = [ line for line in cfgContent.split("\n") if line is not "" ]
            lines = [ line for line in lines if line[0] is not "#" ]
            # splitting between the ":"
            self.branches = [ line.split(":") for line in lines ]
            for branch in self.branches:
                if len(self.branches) < 3:
                    print "== Error in the result file syntax."
                    sys.exit(1)
                # splitting the process entries to get name and expected number of events
                processes = branch[2].split(",")
                processes = [ proc for proc in processes if proc != "" ]
                processes = [ proc.split("=") for proc in processes ]
                processes = [ (proc[0], float(proc[1])) for proc in processes ]
                branch[2] = dict(processes)
    
    def iniFromRDS(self, mcResult, rdsRow):
        self.branches = copy.deepcopy(mcResult.branches)

        for branch in self.branches:
            branch[2] = {}
            branch[2]["data"] = rdsRow.find(branch[1] + "_var").getVal()

######## CLASS PCONFIG #####################################################

class PConfig:

    def __init__(self, cfgFileName):
        self.mvaCfg = {}

        # key is process / dataset name, value is process configuration
        self.procCfg = {}

        with open(cfgFileName, "r") as cfgFile:

            configuration = yaml.load(cfgFile)

            if not 'datasets' in configuration:
                print('You must have at leat one dataset...')
                sys.exit(1)

            self.procCfg = configuration['datasets']
            self.mvaCfg = configuration['analysis']

    def countProcesses(self, signal):
        count = 0
        for name, proc in self.procCfg.items():
            if proc["signal"] in signal:
                count += 1
        return count

######## CONVERT COLOR #####################################################

def convertColor(name):
    nameContent = name.split("+")
    
    if len(nameContent) > 2:
        print "converColor: invalid color specified."
        sys.exit(1)
    
    range = nameContent[0]
    add = 0
    if len(nameContent) == 2:
        add = int(nameContent[1].strip())

    colorMap = {}
    colorMap["kWhite"] = ROOT.kWhite
    colorMap["kBlack"] = ROOT.kBlack
    colorMap["kGray"] = ROOT.kGray
    colorMap["kRed"] = ROOT.kRed
    colorMap["kGreen"] = ROOT.kGreen
    colorMap["kBlue"] = ROOT.kBlue
    colorMap["kYellow"] = ROOT.kYellow
    colorMap["kMagenta"] = ROOT.kMagenta
    colorMap["kCyan"] = ROOT.kCyan
    colorMap["kOrange"] = ROOT.kOrange
    colorMap["kSpring"] = ROOT.kSpring
    colorMap["kTeal"] = ROOT.kTeal
    colorMap["kAzure"] = ROOT.kAzure
    colorMap["kViolet"] = ROOT.kViolet
    colorMap["kPink"] = ROOT.kPink

    color = colorMap[range.strip()] + add

    return color

######## CONVERT WEIGHTED LEAST SQUARE CFG TO TEMPLATE CFG ###################
# To be able to use the NLL fit used for the template fits
# with the configurations from a MVA tree.
#
# MVA tree weighted least square fit has:
# - a configuration object of the MVA tree (treeCfg)
# - a training result object of the MVA tree (MCResult)
# - a mode (fix the background or fit on the background)
#
# Template fit expects a configuration object,
# containing the information for the fit, including 
# the histograms to fit on (MC and data).
#
# These are filled here and saved to a file (histFileName) which will 
# then be an input file to the template fit. 

def convertWgtLstSqToTemplate(treeCfg, MCResult, histFileName, mode="fixBkg"):

    templateCfg = copy.deepcopy(treeCfg)

    # Convert "signal" ("1") or "background" ("0") (MVA tree)
    # to "fit on" ("1") or "don't fit on" ("1") (Template)

    nBins = len(MCResult.branches)

    varVec = []

    for proc in templateCfg.procCfg:
        if mode is not "fixBkg":
            if proc["signal"] == "0":
                proc["signal"] = "1"
        if proc["signal"] == "1":
            varVec.append(proc["name"])

    templateCfg.mvaCfg["inputvar"] = "Branch"
    templateCfg.mvaCfg["nbins"] = str(nBins)
    templateCfg.mvaCfg["varmin"] = str(0)
    templateCfg.mvaCfg["varmax"] = str(nBins)
    templateCfg.mvaCfg["options"] = "get"
    templateCfg.mvaCfg["histfile"] = histFileName
    templateCfg.mvaCfg["numcpu"] = "1"

    outFile = ROOT.TFile(histFileName, "RECREATE")
    if outFile.IsZombie():
        print "== In convertWgtLstSqToTemplate: file " + histFileName + " could not be created."
        sys.exit(1)

    for proc in templateCfg.procCfg:
        
        procFile = ROOT.TFile(proc["path"], "READ")
        if procFile.IsZombie():
            print "== In convertWgtLstSqToTemplate: file " + proc["path"] + " could not be opened."
            sys.exit(1)
        procTree = procFile.Get(proc["treename"])
        procTotEntries = procTree.GetEntries()
        procFile.Close()
        
        proc["histname"] = proc["name"] + "_Branch"

        outFile.cd()
        hist = ROOT.TH1D(proc["name"] + "_Branch", proc["name"] + " Branch yields", nBins, 0, nBins)
        hist.Sumw2()
        
        for i,branch in enumerate(MCResult.branches):
            branchName = branch[1]
            branchName = "/".join( branchName.split("/")[1:] )
            hist.GetXaxis().SetBinLabel(i+1, branchName)
            hist.SetBinContent(i+1, float(branch[2][ proc["name"] ]))

        hist.SetEntries(procTotEntries)
        hist.Write()

    outFile.Close()

    return templateCfg

def weightsToString(weights):
    """Convert a list of weights to a string representation"""

    return " * ".join(weights)

def getEntriesEffentriesYieldTuple(fileName, procDict, lumi):

    entriesEffEntriesYield = []
    myChain = ROOT.TChain(procDict["treename"])
    if type(fileName) is list:
        for file in fileName:
            myChain.Add(file)
    else:
        myChain.Add(fileName) 
    entries = int(myChain.GetEntries())
    entriesEffEntriesYield.append(entries)
    #histName = str(hash(fileName[0]))
    #myChain.Draw("Entries$>>" + histName, procDict["evtweight"], "goff")
    #gotHist = ROOT.gDirectory.Get(histName)
    #if gotHist is None:
    #    return None
    #tempHist = ROOT.TH1F(gotHist)
    ## This has to be done because otherwise TH1F::Integral() might return 0.0 (bug reported, fix shipped in next ROOT release)
    #tempHist.BufferEmpty()
    #effEntries = tempHist.Integral()
    if procDict["signal"] != -5: 
        effEntries = 0
        formulaName = str(hash(procDict["evtweight"]))
        formula = ROOT.TTreeFormula(formulaName, procDict["evtweight"], myChain)
        formula.GetNdata()
        myChain.SetNotify(formula)
        for entry in myChain:
            effEntries += formula.EvalInstance()
        entriesEffEntriesYield.append(effEntries)
        entriesEffEntriesYield.append(lumi*procDict["xsection"]*effEntries/procDict["genevents"])
        formula.IsA().Destructor(formula)
    else:
        entriesEffEntriesYield.append(entries)
        entriesEffEntriesYield.append(entries)
    myChain.IsA().Destructor(myChain)
    return entriesEffEntriesYield
 



