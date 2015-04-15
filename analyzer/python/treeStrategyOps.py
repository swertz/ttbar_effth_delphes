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
    
    configs = []
    
    count = 0

    for name, proc in box.cfg.procCfg.items():
        if proc["signal"] == 1 and box.cfg.mvaCfg["removefrompool"]:
            proc["signal"] = -3

        if proc["signal"] == 1 or proc["signal"] == -1:
            # copy previous configuration and adapt it
            thisCfg = copy.deepcopy(box.cfg)
            bkgName = ""
            inputVar = ""

            # This part adapts each new analysis from the current one:
            # in particular, which process is signal ("1"), which is background ("0"), 
            # and which is spectator ("-1")
            # It also defines the input variables ("inputVar") to be used for the training.
            # By default, it is the weight corresponding to the hypothesis of the processes used
            # for training ("weightname"). Of course this field might be left blank, with
            # other input variables used as well ("otherinputvar").

            count += 1
            count2 = 0

            for name2, proc2 in thisCfg.procCfg.items():

                if proc2["signal"] == 1 or proc2["signal"] == -1:
                    count2 += 1
                    if count2 == count:
                        proc2["signal"] = 1
                    else:
                        proc2["signal"] = -1

                if proc2["signal"] == -2:
                    proc2["signal"] = 0
                if proc2["signal"] == 0:
                    bkgName += "_" + name2
                    inputVar += proc2["weightname"] + ","

            thisCfg.mvaCfg["name"] = name + "_vs" + bkgName
            thisCfg.mvaCfg["inputvar"] = ','.join(thisCfg.mvaCfg["otherinputvars"] + [inputVar + proc["weightname"]])
            thisCfg.mvaCfg["splitname"] = thisCfg.mvaCfg["name"]
            thisCfg.mvaCfg["outputname"] = thisCfg.mvaCfg["name"]
            thisCfg.mvaCfg["log"] = thisCfg.mvaCfg["name"] + ".results"
            
            configs.append(thisCfg)

    for cfg in configs:
        newMVA = MISAnalysis(box, cfg)
        box.MVA.append(newMVA)

def analyseResults(box, locks):
    """ Based on the current box and the results stored in box.MVA, decide what to do next. 
    Failed tmva calls have box.MVA.result=None => careful!.
    This function defines box.daughters[] with configs which have been adapted from the current config and the results. Each of these will be passed to a new tryMisChief instance, to get to the next node. 
    If the list is empty, or if all the daughter boxes have isEnd=True, this branch is simply stopped (with no other action taken... be sure to do everything you need to do here). """

    goodMVA = [ mva for mva in box.MVA if mva.result is not None ]

    # Forget about (and delete is asked) MVAs who have not reached sufficient discrimination
    for i,mva in enumerate(goodMVA):
        if mva.result[1] > float(box.cfg.mvaCfg["maxbkgeff"]):
            mva.log("MVA doesn't reach the minimum discrimination.")
            if box.cfg.mvaCfg["removebadana"]:
                mva.log("Delete output files.")
                os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
    goodMVA = [ mva for mva in goodMVA if mva.result[1] < float(box.cfg.mvaCfg["maxbkgeff"]) ]

    # If no MVA has sufficient discrimination, log current box in tree and stop branch:
    if len(goodMVA) == 0:
        box.log("Found no MVA to have enough discrimination. Stopping here.")
        with locks["stdout"]:
            print "== Level {0}: Found no MVA to have sufficient discrimination. Stopping branch.".format(box.level)
        
        if box.level != 1:
            if box.cfg.mvaCfg["removebadana"]:
                box.log("Removing output directory of this unsatisfactory try.")
                os.system("rmdir " + box.cfg.mvaCfg["outputdir"])
            # The box we're in is an "end" box
            box.isEnd = True
        
        return 0

    # Sort good MVAs in decreasing discrimination order:
    goodMVA.sort(reverse = True, key = lambda mva: mva.result[0]/mva.result[1])
    bestMVA = goodMVA[0]

    # If max level reached, stop this branch and log best MVA results in tree whatever MC we still have left.
    if box.level == int(box.cfg.mvaCfg["maxlevel"]):
        box.log("Reached max level. Stopping here, but defining sig- and bkg-like end-boxes.")
        with locks["stdout"]:
            print "== Level {0}: Reached max level. Stopping the branch.".format(box.level)
        
        box.goodMVA = bestMVA
        bestMVA.log("We are the Chosen One!")
        
        # Sig-like branch
        cfgSigLike = copy.deepcopy(bestMVA.cfg)
        
        for name, proc in cfgSigLike.procCfg.items():
            if proc["signal"] == -1:
                proc["signal"] = 1
            proc["path"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_siglike_proc_" + name + ".root"
            proc["entries"] = str(bestMVA.entries["sig"][name])
            proc["yield"] = str(bestMVA.yields["sig"][name])
        
        sigBox = MISBox(parent = box, cfg = cfgSigLike, type = "sig")
        sigBox.isEnd = True
        box.goodMVA.sigLike = sigBox

        # Bkg-like branch
        cfgBkgLike = copy.deepcopy(bestMVA.cfg)
        
        for name, proc in cfgBkgLike.procCfg.items():
            if proc["signal"] == -1:
                proc["signal"] = 1
            proc["path"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_bkglike_proc_" + name + ".root"
            proc["entries"] = str(bestMVA.entries["bkg"][name])
            proc["yield"] = str(bestMVA.yields["bkg"][name])
        
        bkgBox = MISBox(parent = box, cfg = cfgBkgLike, type = "bkg")
        bkgBox.isEnd = True
        box.goodMVA.bkgLike = bkgBox
    
        # Removing the others if asked
        if box.cfg.mvaCfg["removebadana"]:
            box.log("Removing output files of MVAs we're not keeping.")
            for mva in [ mva for mva in goodMVA if mva.cfg.mvaCfg["name"] != bestMVA.cfg.mvaCfg["name"] ]:
                os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
        
        return 0

    # We know we can go down one more level. Find the best MVA:
    cfgSigLike = copy.deepcopy(bestMVA.cfg)
    stopSigLike = False
    cfgBkgLike = copy.deepcopy(bestMVA.cfg)
    stopBkgLike = False
    
    for mva in goodMVA:
        bestMVA = mva
        cfgSigLike = copy.deepcopy(mva.cfg)
        cfgBkgLike = copy.deepcopy(mva.cfg)
        myCfgs = {"sig": cfgSigLike, "bkg": cfgBkgLike}

        for split in ["sig", "bkg"]:
            for name, proc in myCfgs[split].procCfg.items():
                if mva.entries[split][name] < int(box.cfg.mvaCfg["minmcevents"]):
                    proc["signal"] = -3

        nSig_Sig = cfgSigLike.countProcesses([-1, 1]) > 0
        nBkg_Sig = cfgSigLike.countProcesses([-2, 0]) > 0
        
        nSig_Bkg = cfgBkgLike.countProcesses([-1, 1]) > 0
        nBkg_Bkg = cfgBkgLike.countProcesses([-2, 0]) > 0

        if ( not (nSig_Sig and nBkg_Sig) ) and ( not (nSig_Bkg and nBkg_Bkg) ):
            if i == len(results) - 1:
                bestMVA = goodMVA[0]
                cfgSigLike = copy.deepcopy(bestMVA.cfg)
                cfgBkgLike = copy.deepcopy(bestMVA.cfg)
                stopSigLike = True
                stopBkgLike = True
                break
            else:
                continue

        if not (nSig_Sig and nBkg_Sig):
            stopSigLike = True

        if not (nSig_Bkg and nBkg_Bkg):
            stopBkgLike = True

        break        
    
    # We have found a good analysis:
    box.goodMVA = bestMVA
    bestMVA.log("We are the Chosen One!")
    box.log("Found best analysis to be " + bestMVA.cfg.mvaCfg["name"] + ".")
    with locks["stdout"]:
        print "== Level {0}: Found best MVA to be {1}.".format(box.level, bestMVA.cfg.mvaCfg["name"])
    
    # Removing the others if asked
    if box.cfg.mvaCfg["removebadana"]:
        box.log("Removing output files of MVAs we're not keeping.")
        for mva in [ mva for mva in goodMVA if mva.cfg.mvaCfg["name"] != bestMVA.cfg.mvaCfg["name"] ]:
            os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
    
    # Starting two new "tries", one for signal-like events, the other one for background-like
    # unless one of those doesn't have enough MC => stop here, and define that daughter box as end-box. 
    
    # Sig-like branch
    cfgSigLike.mvaCfg["outputdir"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_SigLike"
    for name, proc in cfgSigLike.procCfg.items():
        proc["path"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_siglike_proc_" + name + ".root"
        proc["entries"] = str(bestMVA.entries["sig"][name])
        proc["yield"] = str(bestMVA.yields["sig"][name])
        if proc["signal"] == -1:
            proc["signal"] = 1

    sigBox = MISBox(parent = box, cfg = cfgSigLike, type = "sig")
    bestMVA.sigLike = sigBox 
    
    if stopSigLike:
        box.log("Sig-like part of best analysis has no process with enough MC to train => stop that branch.")
        bestMVA.log("Sig-like part has no process with enough MC to train => stop that branch.")
        with locks["stdout"]:
            print "== Level {0}: {1} is the best MVA, but sig-like subset doesn't have enough MC events to train another MVA => stopping here.".format(box.level, bestMVA.cfg.mvaCfg["name"])
        sigBox.isEnd = True
    
    # Bkg-like branch
    cfgBkgLike.mvaCfg["outputdir"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_BkgLike"

    for name, proc in cfgBkgLike.procCfg.items():
        proc["path"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_bkglike_proc_" + name + ".root"
        proc["entries"] = str(bestMVA.entries["bkg"][name])
        proc["yield"] = str(bestMVA.yields["bkg"][name])
        if proc["signal"] == -1:
            proc["signal"] = 1
    
    bkgBox = MISBox(parent = box, cfg = cfgBkgLike, type = "bkg")
    bestMVA.bkgLike = bkgBox 

    if stopBkgLike:
        box.log("Bkg-like part of best analysis has no process with enough MC to train => stop that branch.")
        bestMVA.log("Bkg-like part has no process with enough MC to train => stop that branch.")
        with locks["stdout"]:
            print "== Level {0}: {1} is the best MVA, but bkg-like subset doesn't have enough MC events to train another MVA => stopping here.".format(level, bestMva.mvaCfg["name"])
        bkgBox.isEnd = True

if __name__ == "__main__":
    print "Do not run on this file."
