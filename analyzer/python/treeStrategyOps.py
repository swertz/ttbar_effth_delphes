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
            inputVar = []

            # This part adapts each new analysis from the current one:
            # in particular, which process is signal ("1"), which is background ("0"), 
            # and which is spectator ("-1")
            # It also defines the input variables ("inputVar") to be used for the training.
            # By default, it is the weight corresponding to the hypothesis of the processes used
            # for training ("weightname"). Of course this field might be left blank, with
            # other input variables used as well ("otherinputvar").

            for name2, proc2 in thisCfg.procCfg.items():

                if proc2["signal"] == 1 or proc2["signal"] == -1:
                    if name == name2:
                        proc2["signal"] = 1
                    else:
                        proc2["signal"] = -1

                if proc2["signal"] == -2:
                    proc2["signal"] = 0
                if proc2["signal"] == 0:
                    bkgName += "_" + name2
                    inputVar += proc2["weightname"]

            if bkgName == "":
                with locks["stdout"]:
                    print "== Error in box " + box.name + ": no background to train against signal " + name + "!"
                box.log("Error: no background to train against signal " + name + "!")
                sys.exit(1)

            thisCfg.mvaCfg["name"] = name + "_vs" + bkgName
            #thisCfg.mvaCfg["inputvar"] = thisCfg.mvaCfg["otherinputvars"] + inputVar + [proc["weightname"]]
            # To use the Singleton mode (in this special case):
            thisCfg.mvaCfg["inputvar"] = [ "(atan(" + inputVar[0] + "-abs(" + proc["weightname"][0] + "))+1.6)/3.2" ]
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
    for i, mva in enumerate(goodMVA):
        if mva.result[1] > float(box.cfg.mvaCfg["maxbkgeff"]):
            mva.log("MVA doesn't reach the minimum discrimination.")
            if box.cfg.mvaCfg["removebadana"]:
                mva.log("Delete output files.")
                os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
    goodMVA = [ mva for mva in goodMVA if mva.result[1] < float(box.cfg.mvaCfg["maxbkgeff"]) ]

    # If no MVA has sufficient discrimination, stop branch:
    if len(goodMVA) == 0:
        box.log("Found no MVA to have enough discrimination. Stopping here.")
        with locks["stdout"]:
            print "== Level {0}, box {1}: Found no MVA to have sufficient discrimination. Stopping branch.".format(box.level, box.name)
        
        if box.level != 1:
            if box.cfg.mvaCfg["removebadana"]:
                box.log("Removing output directory of this unsatisfactory try.")
                os.system("rm -r " + box.cfg.mvaCfg["outputdir"])
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
            print "== Level {0}, box {1}: Reached max level. Stopping the branch.".format(box.level, box.name)

        defineSigAndBkgBoxes(box, locks, bestMVA, sigIsEnd = True, bkgIsEnd = True)
    
        # Removing the others if asked
        if box.cfg.mvaCfg["removebadana"]:
            box.log("Removing output files of MVAs we're not keeping.")
            for mva in [ mva for mva in goodMVA if mva.cfg.mvaCfg["name"] != bestMVA.cfg.mvaCfg["name"] ]:
                os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
        
        return 0

    # We know we can go down one more level. Find the best MVA:
    stopSigLike = False
    stopBkgLike = False
    
    for i, mva in enumerate(goodMVA):
        bestMVA = mva
        cfgSigLike = copy.deepcopy(bestMVA.cfg)
        cfgBkgLike = copy.deepcopy(bestMVA.cfg)
        myCfgs = {"Sig": cfgSigLike, "Bkg": cfgBkgLike}

        for split in ["Sig", "Bkg"]:
            for name, proc in myCfgs[split].procCfg.items():
                if bestMVA.entries[split][name] < box.cfg.mvaCfg["minmcevents"]:
                    proc["signal"] = -3

        enoughMC_SigLike = cfgSigLike.countProcesses([-1, 1]) > 0 and cfgSigLike.countProcesses([-2, 0]) > 0
        enoughMC_BkgLike = cfgBkgLike.countProcesses([-1, 1]) > 0 and cfgBkgLike.countProcesses([-2, 0]) > 0

        if not enoughMC_SigLike and not enoughMC_BkgLike:
            if i == len(goodMVA) - 1:
                bestMVA = goodMVA[0]
                stopSigLike = True
                stopBkgLike = True
                break
            else:
                continue

        #if not (nSig_SigLike and nBkg_SigLike):
        if not enoughMC_SigLike:
            stopSigLike = True

        #if not (nSig_BkgLike and nBkg_BkgLike):
        if not enoughMC_BkgLike:
            stopBkgLike = True

        break        
    
    if stopSigLike:
        box.log("Sig-like part of best analysis has no process with enough MC to train => stop that branch.")
        bestMVA.log("Sig-like part has no process with enough MC to train => stop that branch.")
        with locks["stdout"]:
            print "== Level {0}, box {1}: {2} is the best MVA, but sig-like subset doesn't have enough MC events to train another MVA => stopping here.".format(box.level, box.name, bestMVA.cfg.mvaCfg["name"])
    if stopBkgLike:
        box.log("Bkg-like part of best analysis has no process with enough MC to train => stop that branch.")
        bestMVA.log("Bkg-like part has no process with enough MC to train => stop that branch.")
        with locks["stdout"]:
            print "== Level {0}, box {1}: {2} is the best MVA, but bkg-like subset doesn't have enough MC events to train another MVA => stopping here.".format(box.level, box.name, bestMVA.cfg.mvaCfg["name"])
    
    defineSigAndBkgBoxes(box, locks, bestMVA, sigIsEnd = stopSigLike, bkgIsEnd = stopBkgLike)
    
    # Removing the others if asked
    if box.cfg.mvaCfg["removebadana"]:
        box.log("Removing output files of MVAs we're not keeping.")
        for mva in [ mva for mva in goodMVA if mva.cfg.mvaCfg["name"] != bestMVA.cfg.mvaCfg["name"] ]:
            os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
    

def defineSigAndBkgBoxes(box, locks, bestMVA, sigIsEnd, bkgIsEnd):
        
    box.goodMVA = bestMVA
    
    bestMVA.log("We are the Chosen One!")
    box.log("Found best analysis to be " + bestMVA.cfg.mvaCfg["name"] + ".")
    with locks["stdout"]:
        print "== Level {0}, box {1}: Found best MVA to be {2}.".format(box.level, box.name, bestMVA.cfg.mvaCfg["name"])
    
    # Sig-like branch
    cfgSigLike = copy.deepcopy(bestMVA.cfg)
    cfgSigLike.mvaCfg["outputdir"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_SigLike"
    
    for name, proc in cfgSigLike.procCfg.items():
        if bestMVA.entries["Sig"][name] < box.cfg.mvaCfg["minmcevents"]:
            proc["signal"] = -3
        proc["path"] = [bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_SigLike_proc_" + name + ".root"]
        proc["entries"] = bestMVA.entries["Sig"][name]
        proc["yield"] = bestMVA.yields["Sig"][name]
    
    sigBox = MISBox(parent = box, cfg = cfgSigLike, type = "Sig")
    sigBox.isEnd = sigIsEnd
    box.goodMVA.sigLike = sigBox

    # Bkg-like branch
    cfgBkgLike = copy.deepcopy(bestMVA.cfg)
    cfgBkgLike.mvaCfg["outputdir"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_BkgLike"
    
    for name, proc in cfgBkgLike.procCfg.items():
        if bestMVA.entries["Bkg"][name] < box.cfg.mvaCfg["minmcevents"]:
            proc["signal"] = -3
        proc["path"] = [bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_BkgLike_proc_" + name + ".root"]
        proc["entries"] = bestMVA.entries["Bkg"][name]
        proc["yield"] = bestMVA.yields["Bkg"][name]
    
    bkgBox = MISBox(parent = box, cfg = cfgBkgLike, type = "Bkg")
    bkgBox.isEnd = bkgIsEnd
    box.goodMVA.bkgLike = bkgBox
    


if __name__ == "__main__":
    print "Do not run on this file."
