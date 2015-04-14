# Not to be used as standalone file

import sys
import os
import copy
import ROOT

from treeStructure import MISAnalysis
from treeStructure import MISBox 

def defineNewCfgs(box, locks):
    """ Create specific tmva configuration object and define a list with all the configurations.
    Each of them will be used to launch a thread. The list is stored in box.MVA."""
    
    configs = []
    
    count = 0

    for proc in box.cfg.procCfg:
        if proc["signal"] == "1" and box.cfg.mvaCfg["removefrompool"] == "y":
            proc["signal"] = "-3"

        if proc["signal"] == "1" or proc["signal"] == "-1":
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

            for proc2 in thisCfg.procCfg:

                if proc2["signal"] == "1" or proc2["signal"] == "-1":
                    count2 += 1
                    if count2 == count:
                        proc2["signal"] = "1"
                    else:
                        proc2["signal"] = "-1"

                if proc2["signal"] == "-2":
                    proc2["signal"] = "0"
                if proc2["signal"] == "0":
                    bkgName += "_" + proc2["name"]
                    inputVar += proc2["weightname"] + ","

            thisCfg.mvaCfg["name"] = proc["name"] + "_vs" + bkgName
            thisCfg.mvaCfg["inputvar"] = thisCfg.mvaCfg["otherinputvar"] + "," + inputVar + proc["weightname"]
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
        if mva.result[1] > float(cfg.mvaCfg["maxbkgeff"]):
            mva.log("MVA doesn't reach the minimum discrimination.")
            if box.cfg.mvaCfg["removebadana"]:
                mva.log("Delete output files.")
                os.system("rm " + mva.mvaCfg["outputdir"] + "/" + mva.mvaCfg["name"] + "*")
    goodMVA = [ mva for mva in goodMVA if mva.result[1] < float(box.cfg.mvaCfg["maxbkgeff"]) ]

    # If no MVA has sufficient discrimination, log current box in tree and stop branch:
    if len(goodMVA) == 0:
        box.log("Found no MVA to have enough discrimination. Stopping here.")
        with locks["stdout"]:
            print "== Level {0}: Found no MVA to have sufficient discrimination. Stopping branch.".format(level)
        
        if level != 1:
            if cfg.mvaCfg["removebadana"]:
                box.log("Removing output directory of this unsatisfactory try.")
                os.system("rmdir " + cfg.mvaCfg["outputdir"])
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
        
        for proc in cfgSigLike.procCfg:
            if proc["signal"] == "-1":
                proc["signal"] = "1"
            proc["path"] = bestMVA["outputdir"] + "/" + bestMVA["name"] + "_siglike_proc_" + proc["name"] + ".root"
            proc["entries"] = str(bestMVA.entries["sig"][ proc["name"] ])
            proc["yield"] = str(bestMVA.yields["sig"][ proc["name"] ])
        
        sigBox = MISBox(box, cfgSigLike)
        sigBox.isEnd = True
        sigBox.name = box.name + "/" + bestMVA["outputname"] + "_SigLike"
        box.goodMVA.sigLike = sigBox

        # Bkg-like branch
        cfgBkgLike = copy.deepcopy(bestMVA.cfg)
        
        for proc in cfgBkgLike.procCfg:
            if proc["signal"] == "-1":
                proc["signal"] = "1"
            proc["path"] = bestMVA["outputdir"] + "/" + bestMVA["name"] + "_bkglike_proc_" + proc["name"] + ".root"
            proc["entries"] = str(bestMVA.entries["bkg"][ proc["name"] ])
            proc["yield"] = str(bestMVA.yields["bkg"][ proc["name"] ])
        
        bkgBox = MISBox(box, cfgBkgLike)
        bkgBox.isEnd = True
        bkgBox.name = box.name + "/" + bestMVA["outputname"] + "_BkgLike"
        box.goodMVA.bkgLike = bkgBox
        
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
            for proc in myCfgs[split].procCfg:
                if mva.entries[split][ proc["name"] ] < int(box.cfg.mvaCfg["minmcevents"]):
                    proc["signal"] = "-3"

        nSig_Sig = cfgSigLike.countProcesses(["-1","1"]) > 0
        nBkg_Sig = cfgSigLike.countProcesses(["-2","0"]) > 0
        
        nSig_Bkg = cfgBkgLike.countProcesses(["-1","1"]) > 0
        nBkg_Bkg = cfgBkgLike.countProcesses(["-2","0"]) > 0

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
    if box.cfg.mvaCfg["removebadana"] == "y":
        box.log("Removing output files of MVAs we're not keeping.")
        for mva in [ mva for mva in goodMVA if mva.cfg.mvaCfg["name"] != bestMVA.cfg.mvaCfg["name"] ]:
            os.system("rm " + mva.cfg.mvaCfg["outputdir"] + "/" + mva.cfg.mvaCfg["name"] + "*")
    
    # Starting two new "tries", one for signal-like events, the other one for background-like
    # unless one of those doesn't have enough MC => stop here, and log result in tree 
    
    # Sig-like branch
    cfgSigLike.mvaCfg["outputdir"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_SigLike"
    for proc in cfgSigLike.procCfg:
        proc["path"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_siglike_proc_" + proc["name"] + ".root"
        proc["entries"] = str(bestMVA.entries["sig"][ proc["name"] ])
        proc["yield"] = str(bestMVA.yields["sig"][ proc["name"] ])
        if proc["signal"] == "-1":
            proc["signal"] = "1"

    sigBox = MISBox(box, cfgSigLike)
    bestMVA.sigLike = sigBox 
    sigBox.name = box.name + "/" + bestMVA["outputname"] + "_SigLike"
    
    if stopSigLike:
        box.log("Sig-like part of best analysis has no process with enough MC to train => stop that branch.")
        bestMVA.log("Sig-like part has no process with enough MC to train => stop that branch.")
        with locks["stdout"]:
            print "== Level {0}: {1} is the best MVA, but sig-like subset doesn't have enough MC events to train another MVA => stopping here.".format(box.level, bestMVA.mvaCfg["name"])
        sigBox.isEnd = True
    
    # Bkg-like branch
    cfgBkgLike.mvaCfg["outputdir"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + bestMVA.cfg.mvaCfg["name"] + "_BkgLike"

    for proc in cfgBkgLike.procCfg:
        proc["path"] = bestMVA.cfg.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_bkglike_proc_" + proc["name"] + ".root"
        proc["entries"] = str(bestMVA.entries["bkg"][ proc["name"] ])
        proc["yield"] = str(bestMVA.yields["bkg"][ proc["name"] ])
        if proc["signal"] == "-1":
            proc["signal"] = "1"
    
    bkgBox = MISBox(box, cfgBkgLike)
    bestMVA.bkgLike = bkgBox 
    bkgBox.name = box.name + "/" + bestMVA["outputname"] + "_BkgLike"

    if stopBkgLike:
        box.log("Bkg-like part of best analysis has no process with enough MC to train => stop that branch.")
        bestMVA.log("Bkg-like part has no process with enough MC to train => stop that branch.")
        with locks["stdout"]:
            print "== Level {0}: {1} is the best MVA, but bkg-like subset doesn't have enough MC events to train another MVA => stopping here.".format(level, bestMva.mvaCfg["name"])
        bkgBox.isEnd = True

if __name__ == "__main__":
    print "Do not run on this file."
