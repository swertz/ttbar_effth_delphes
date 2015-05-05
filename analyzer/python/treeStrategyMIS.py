# Not to be used as standalone file

import sys
import os
import copy
import ROOT

from treeStructure import MISAnalysis
from treeStructure import MISBox 

def defineNewCfgs(box, locks):
    """ Create specific tmva configuration objects ("PConfig") based on the current "box.cfg".
    Use them to create MVA objects ("MISAnalysis"), which are then stored in "box.MVA".
    Each of them will be used to launch a thread.."""
    

    count=0
    listOfCfg=[]
    configs=[]
    for name, proc in box.cfg.procCfg.items():
        if proc["signal"]==-1 :
            names = [nom for nom in box.cfg.procCfg.keys() if nom != name]
            for name2 in names:
                thisCfg = copy.deepcopy(box.cfg)
                proc2 = box.cfg.procCfg[name2]
                inputVar = []
                if proc2["signal"] == -1:
                    bkgName =  name2
                    if bkgName+"_vs_"+name not in listOfCfg:
                        listOfCfg.append(name + "_vs_" + bkgName)
                        inputVar.append(proc2["weightname"])
                        thisCfg.mvaCfg["name"] = name + "_vs_" + bkgName
                        thisCfg.mvaCfg["inputvar"] = thisCfg.mvaCfg["otherinputvars"] + inputVar + [proc["weightname"]]
                        thisCfg.mvaCfg["splitname"] = thisCfg.mvaCfg["name"]
                        thisCfg.mvaCfg["outputname"] = thisCfg.mvaCfg["name"]
                        thisCfg.mvaCfg["log"] = thisCfg.mvaCfg["name"] + ".results"
                        thisCfg.procCfg[name]["signal"]=1
                        thisCfg.procCfg[bkgName]["signal"]=0
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

    succeededMVA=[ mva for mva in box.MVA if mva.result is not None ]
    goodMVA = [ mva for mva in succeededMVA if mva.result[1] < float(box.cfg.mvaCfg["maxbkgeff"]) ]
    if len(goodMVA)==0:
        box.isEnd = True
        return 0
    goodMVA.sort(reverse = True, key = lambda mva: mva.result[0]/mva.result[1])
    bestMVA = goodMVA[0]
    with locks["stdout"]:
        print "== Level {0}: Found best MVA to be {1}.".format(box.level, bestMVA.cfg.mvaCfg["name"])
    box.goodMVA = bestMVA # Keep track of the MVA chosen to define the new sig- and bkg-like subsets. This must be specified before building a daughter box (otherwise the daughter box will not know how she was conceived, poor thing...)
    
    cfgSigLike = copy.deepcopy(bestMVA.cfg)
    cfgSigLike.mvaCfg["outputdir"]=bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_siglike"
    for name, procDict in cfgSigLike.procCfg.items() :
        if procDict["signal"] != -3:
            procDict["signal"]=-1
        if bestMVA.entries["sig"][name] < int(box.cfg.mvaCfg["minmcevents"]):
            procDict["signal"] = -3
        procDict["path"] = [bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_siglike_proc_" + name + ".root"]
        procDict["entries"] = str(bestMVA.entries["sig"][name])
        procDict["yield"] = str(bestMVA.yields["sig"][name])
        
    cfgBkgLike = copy.deepcopy(bestMVA.cfg)
    cfgBkgLike.mvaCfg["outputdir"]=bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_bkglike"
    for name, procDict in cfgBkgLike.procCfg.items() :
        if procDict["signal"] != -3:
            procDict["signal"]=-1
        procDict["path"] = [bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_bkglike_proc_" + name + ".root"]
        procDict["entries"] = str(bestMVA.entries["bkg"][name])
        procDict["yield"] = str(bestMVA.yields["bkg"][name])

    sigBox = MISBox(parent = box, cfg = cfgSigLike, type = "sig") # "sigBox" will be a daughter of "box", and "box" the parent of "sigBox"
    bkgBox = MISBox(parent = box, cfg = cfgBkgLike, type = "bkg")
    box.goodMVA.sigLike = sigBox # Keep track that the sig-like subset of this MVA is the box we have just defined
    box.goodMVA.bkgLike = bkgBox # Keep track that the sig-like subset of this MVA is the box we have just defined
    # Define "config" for next step (e.g. sig-like branch of current box), then:
    if box.level > 1 :
        sigBox.isEnd = True # If we want to stop here (usually, when stopping, we have NO goodMVA)
        bkgBox.isEnd = True # If we want to stop here (usually, when stopping, we have NO goodMVA)
    

if __name__ == "__main__":
    print "Do not run on this file."
