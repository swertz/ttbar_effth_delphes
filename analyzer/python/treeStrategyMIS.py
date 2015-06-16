# Not to be used as standalone file

import sys
import os
import copy
import ROOT
from operator import methodcaller
from math import sqrt

from treeStructure import MISAnalysis
from treeStructure import MISBox 


#def puritySignifSubLeadProc(nLead, nSubLead) :
#    if nLead == 0 or nSubLead == 0:
#        return 100000
#    return (nSubLead+nLead)/(sqrt(nLead)+nLead/sqrt(nSubLead))
def puritySignifSubLeadProc(nLead, nSubLead) :
    if nLead == 0 or nSubLead == 0:
        return 100000
    #print "Method 1 : ", (nSubLead+nLead)/(sqrt(nLead)+nLead/sqrt(nSubLead))
    #print "Method 2 : ", (nSubLead*sqrt(nSubLead+nLead))/sqrt(nSubLead*nLead)
    return (nSubLead*sqrt(nSubLead+nLead))/sqrt(nSubLead*nLead)

def getPurity(n1, n2) :
    return n1/float(n1+n2)

def defineNewCfgs(box, locks):
    """ Create specific tmva configuration objects ("PConfig") based on the current "box.cfg".
    Use them to create MVA objects ("MISAnalysis"), which are then stored in "box.MVA".
    Each of them will be used to launch a thread.."""

    configs=[]
    for proc1Name, proc1Dict in box.cfg.procCfg.items():
        if proc1Dict["signal"]==-3 or proc1Dict["signal"] == -5 or box.entries[proc1Name] < box.cfg.mvaCfg["minmcevents"] : 
            continue
        proc1Yield = box.yields[proc1Name]
        #allowedProcNames = [name for name in box.cfg.procCfg.keys() if name != proc1Name and box.cfg.procCfg[name]["signal"] != -3 and box.entries[name] > box.cfg.mvaCfg["minmcevents"]  ]
        for proc2Name in box.cfg.procCfg.keys() :
            proc2Yield = box.yields[proc2Name]
            if proc1Yield >  proc2Yield and not (box.cfg.procCfg[proc2Name]["signal"]==-3 or box.cfg.procCfg[proc2Name]["signal"] == -5 or box.entries[proc2Name] < box.cfg.mvaCfg["minmcevents"]) :          # the second one will always be the one with the smallest yield (the bkg), avoid also to have DY_vs_TT and TT_vs_DY 
                thisCfg = copy.deepcopy(box.cfg)
                proc2Dict = box.cfg.procCfg[proc2Name]
                inputVar = []
                #inputVar += proc2Dict["weightname"]
                thisCfg.mvaCfg["name"] = proc1Name + "_vs_" + proc2Name
                thisCfg.mvaCfg["inputvar"] =  [ "((atan(" + proc2Dict["weightname"][0] + "-" + proc1Dict["weightname"][0] + "))+1.6)/3.2" ]    
                #thisCfg.mvaCfg["inputvar"] =  [ "((atan(" + proc1Dict["weightname"][0] + "/" + proc2Dict["weightname"][0] + "))+1.6)/3.2" ]    
                #thisCfg.mvaCfg["inputvar"] = thisCfg.mvaCfg["otherinputvars"] + inputVar + proc1Dict["weightname"]
                thisCfg.mvaCfg["splitname"] = thisCfg.mvaCfg["name"]
                thisCfg.mvaCfg["outputname"] = thisCfg.mvaCfg["name"]
                thisCfg.mvaCfg["log"] = thisCfg.mvaCfg["name"] + ".results"
                thisCfg.mvaCfg["sumYieldsOfSeparatedProc"] = proc1Yield + proc2Yield
                thisCfg.mvaCfg["proc1"] = proc1Name
                thisCfg.mvaCfg["proc2"] = proc2Name
                thisCfg.procCfg[proc1Name]["signal"]=1
                thisCfg.procCfg[proc2Name]["signal"]=0
                configs.append(thisCfg)
                                 
    for config in configs:
        newMVA = MISAnalysis(box, config)
        box.MVA.append(newMVA)

def analyseResults(box, locks):
    """ Based on the current box and the results stored in "box.MVA", decide what to do next. 
    Failed tmva calls have "box.MVA.result=None" => careful!.
    This function defines "box.daughters[]" by building new boxes using configs which have been adapted from the current config ("box.cfg") and the results of the "box.MVA"'s. 
    Each new box not marked as "isEnd=True" will be passed to a new "tryMisChief" instance, to get to the next level of the tree.
    If the list is empty, or if all the daughter boxes have "isEnd=True", this branch is simply stopped (with no other action taken... be sure to do everything you need to do here). """
    
        
    succeededMVA = [ mva for mva in box.MVA if mva.result is not None ]
    box.goodMVA = None
    if len(succeededMVA) == 0 :
        box.isEnd = True
        box.log("All mva are None...")

    if box.cfg.mvaCfg["analysisChoiceMode"] == "YieldsBased":
        mvaConsideredProcYields = []
        dict_yields_mva = {}
        for mva in succeededMVA :
            dict_yields_mva[str(mva.cfg.mvaCfg["sumYieldsOfSeparatedProc"])] = mva
            mvaConsideredProcYields.append(mva.cfg.mvaCfg["sumYieldsOfSeparatedProc"])
            box.log("Tried MVA {0}".format(mva.cfg.mvaCfg["name"]))
        mvaConsideredProcYields.sort(reverse = True)
        for yieldsKey in  mvaConsideredProcYields :
            mva = dict_yields_mva[str(yieldsKey)] 
            mvaCfg = mva.cfg.mvaCfg
            currentPurity_p = getPurity(box.effEntries[mvaCfg["proc1"]] + sqrt(box.effEntries[mvaCfg["proc1"]]), box.effEntries[mvaCfg["proc2"]] - sqrt(box.effEntries[mvaCfg["proc2"]]))
            currentPurity_m = getPurity(box.effEntries[mvaCfg["proc1"]] - sqrt(box.effEntries[mvaCfg["proc1"]]), box.effEntries[mvaCfg["proc2"]] + sqrt(box.effEntries[mvaCfg["proc2"]]))
            foreseePurity_p = getPurity(mva.effEntries["Sig"][mvaCfg["proc1"]] + sqrt(mva.effEntries["Sig"][mvaCfg["proc1"]]), mva.effEntries["Sig"][mvaCfg["proc2"]] - sqrt(mva.effEntries["Sig"][mvaCfg["proc2"]]))
            foreseePurity_m = getPurity(mva.effEntries["Sig"][mvaCfg["proc1"]] + sqrt(mva.effEntries["Sig"][mvaCfg["proc1"]]), mva.effEntries["Sig"][mvaCfg["proc2"]] - sqrt(mva.effEntries["Sig"][mvaCfg["proc2"]]))
            currentPuritySig = puritySignifSubLeadProc(box.effEntries[mvaCfg["proc2"]], box.effEntries[mvaCfg["proc1"]])
            foreseePuritySig = puritySignifSubLeadProc(mva.effEntries["Sig"][mvaCfg["proc2"]], mva.effEntries["Sig"][mvaCfg["proc1"]])
            if (foreseePuritySig - currentPuritySig) <  box.cfg.mvaCfg["puritySigImprovementCriteria"]:
            #if max(currentPurity_p, currentPurity_m) > min(foreseePurity_p, foreseePurity_m):
                with locks["stdout"]:
                    print mva.cfg.mvaCfg["name"], " was not discriminative enough..."
                    print "Proc 1 - proc 2 entries now : {0} - {1}. Idem after cut : {2} - {3}".format(box.effEntries[mvaCfg["proc1"]], box.effEntries[mvaCfg["proc2"]], mva.effEntries["Sig"][mvaCfg["proc1"]], mva.effEntries["Sig"][mvaCfg["proc2"]])
                    print foreseePuritySig, " ", currentPuritySig, " ", box.cfg.mvaCfg["puritySigImprovementCriteria"] 
                box.log("Proc 1 - proc 2 entries now : {0} - {1}. Idem after cut : {2} - {3}".format(box.effEntries[mvaCfg["proc1"]], box.effEntries[mvaCfg["proc2"]], mva.effEntries["Sig"][mvaCfg["proc1"]], mva.effEntries["Sig"][mvaCfg["proc2"]]))
                box.log("Was not discriminative enough...")
                continue
            else : 
                box.goodMVA = mva
                box.log("== Level {0}: Found best MVA to be {1}.".format(box.level, box.goodMVA.cfg.mvaCfg["name"]))
                with locks["stdout"]:
                    print "== Level {0}: Found best MVA to be {1}.".format(box.level, box.goodMVA.cfg.mvaCfg["name"])
                break
        if box.cfg.mvaCfg["removebadana"]:
            for mva in succeededMVA :
                if box.goodMVA != mva : 
                    mva.log("Delete output files.")
                    os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
        if box.goodMVA is None :
            box.isEnd = True
            box.log("No mva reach the requested discrimination...")
            return 0            
    
    if box.cfg.mvaCfg["analysisChoiceMode"] ==  "DiscriBased":
        goodMVA = [ mva for mva in succeededMVA if mva.result[1] < float(box.cfg.mvaCfg["maxbkgeff"]) ]
        if len(goodMVA)==0:
            box.isEnd = True
            return 0
        goodMVA.sort(reverse = True, key = lambda mva: mva.result[0]/mva.result[1])
        with locks["stdout"]:
            print "== Level {0}: Found best MVA to be {1}.".format(box.level, goodMVA[0].cfg.mvaCfg["name"])
        box.goodMVA = goodMVA[0] # Keep track of the MVA chosen to define the new sig- and bkg-like subsets. This must be specified before building a daughter box (otherwise the daughter box will not know how she was conceived, poor thing...)
        




    cfgSigLike = copy.deepcopy(box.goodMVA.cfg)
    cfgSigLike.mvaCfg["outputdir"]=box.goodMVA.cfg.mvaCfg["outputdir"] + "/" + box.goodMVA.cfg.mvaCfg["name"] + "_SigLike"
    for name, procDict in cfgSigLike.procCfg.items() :
        if procDict["signal"] != -3 and procDict["signal"] != -5 :
            procDict["signal"]=-1
        if box.goodMVA.entries["Sig"][name] < int(box.cfg.mvaCfg["minmcevents"]) and procDict["signal"] != -5:
            procDict["signal"] = -3
        procDict["path"] = [box.goodMVA.cfg.mvaCfg["outputdir"] + "/" + box.goodMVA.cfg.mvaCfg["name"] + "_SigLike_proc_" + name + ".root"]
        procDict["entries"] = box.goodMVA.entries["Sig"][name]
        procDict["yield"] = box.goodMVA.yields["Sig"][name]
        
    cfgBkgLike = copy.deepcopy(box.goodMVA.cfg)
    cfgBkgLike.mvaCfg["outputdir"]=box.goodMVA.cfg.mvaCfg["outputdir"] + "/" + box.goodMVA.cfg.mvaCfg["name"] + "_BkgLike"
    for name, procDict in cfgBkgLike.procCfg.items() :
        if procDict["signal"] != -3 and procDict["signal"] != -5 :
            procDict["signal"]=-1
        if box.goodMVA.entries["Bkg"][name] < int(box.cfg.mvaCfg["minmcevents"]) and procDict["signal"] != -5 :
            procDict["signal"] = -3
        procDict["path"] = [box.goodMVA.cfg.mvaCfg["outputdir"] + "/" + box.goodMVA.cfg.mvaCfg["name"] + "_BkgLike_proc_" + name + ".root"]
        procDict["entries"] = box.goodMVA.entries["Bkg"][name]
        procDict["yield"] = box.goodMVA.yields["Bkg"][name]

    sigBox = MISBox(parent = box, cfg = cfgSigLike, type = "Sig") # "sigBox" will be a daughter of "box", and "box" the parent of "sigBox"
    bkgBox = MISBox(parent = box, cfg = cfgBkgLike, type = "Bkg")
    box.goodMVA.sigLike = sigBox # Keep track that the sig-like subset of this MVA is the box we have just defined
    box.goodMVA.bkgLike = bkgBox # Keep track that the sig-like subset of this MVA is the box we have just defined
    if box.level > box.cfg.mvaCfg["maxlevel"]-1 :
        box.log("Will stop branching at the next iteration because max layer is reached.")
        print "Will stop branching at the next iteration because max layer is reached."
        sigBox.isEnd = True # If we want to stop here (usually, when stopping, we have NO goodMVA)
        bkgBox.isEnd = True # If we want to stop here (usually, when stopping, we have NO goodMVA)
    

if __name__ == "__main__":
    print "Do not run on this file."
