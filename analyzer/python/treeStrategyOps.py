# Not to be used as standalone file

import sys
import os
import copy

def defineNewCfgs(cfg, locks, tree, level):
	""" Create specific tmva configuration object and return a list with all the configurations.
	Each of them will be used to launch a thread. The analysis tree, locks and level are also passed, in case they are needed."""
	
	configs = []
	
	count = 0

	for proc in cfg.procCfg:
		if proc["signal"] == "1" and cfg.mvaCfg["removefrompool"] == "y":
			proc["signal"] = "-3"

		if proc["signal"] == "1" or proc["signal"] == "-1":
			# copy previous configuration and adapt it
			thisCfg = copy.deepcopy(cfg)
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

	return configs

def analyseResults(cfg, results, locks, tree, level):
	""" Based on the current config and the list of results=[(sigEff,bkgEff,minMCEventsSigLike,minMCEventsBkgLike,config),...], decide what to do next. 
	The results are sorted according to decreasing sigEff/bkgEff values.
	Failed tmva calls are not included in the result list => have to be investigated separately.
	Analysis tree, locks and level might be used. 
	Function returns a list of configs which have been adapted from the current config and the results. Each of these will be passed to a new tryMisChief instance, to get to the next node. 
	If the list is empty, this branch is simply stopped (with no other action taken... be sure to everything you need to do here. """

	configs = []
		
	# If no analysis has enough MC, stop this branch and remove the bad analyses if asked for
	# and log the previous node of the branch in the tree, if this node is not yet in it (it might have been added by another parallel branch)
	if len( [ result for result in results if result[2] >= int(cfg.mvaCfg["minkeepevents"]) and result[3] >= int(cfg.mvaCfg["minkeepevents"]) ] ) == 0:
		with locks["stdout"]:
			print "== Level {0}: Found no MVA to have enough MC events. Stopping branch.".format(level)
		if level != 1:
			with locks["tree"]:
				branch = cfg.mvaCfg["previousbranch"]
				if not tree.__contains__(branch):
					tree.append(branch)
		if cfg.mvaCfg["removebadana"] == "y":
			for thisCfg in [ result[4] for result in results ]:
				os.system("rm "+thisCfg.mvaCfg["outputdir"]+"/"+thisCfg.mvaCfg["name"]+"*")
			os.system("rmdir "+cfg.mvaCfg["outputdir"])
		return []

	# For now: take most discriminating MVA. One might decide to do other things,
	# such as take best best MVA, provided one has enough MC to continue (otherwise, take second-best, and so on)
	for i,result in enumerate(results):
		if result[1] > float(cfg.mvaCfg["maxbkgeff"]):
			if cfg.mvaCfg["removebadana"]:
				os.system("rm "+result[4].mvaCfg["outputdir"]+"/"+result[4].mvaCfg["name"]+"*")
	results = [ result for result in results if result[1] < float(cfg.mvaCfg["maxbkgeff"]) ]

	bestMva = results[0][4]
	removeSigLike = False
	removeBkgLike = False
	stopSigLike = False
	stopBkgLike = False
	
	if results[0][2] < int(cfg.mvaCfg["minkeepevents"]):
		removeSigLike = True
	else:
		removeSigLike = False
	
	if results[0][2] < int(cfg.mvaCfg["minmcevents"]):
		stopSigLike = True
	else:
		stopSigLike = False
	
	if results[0][3] < int(cfg.mvaCfg["minkeepevents"]):
		removeBkgLike = True
	else:
		removeBkgLike = False
	
	if results[0][3] < int(cfg.mvaCfg["minmcevents"]):
		stopBkgLike = True
	else:
		stopBkgLike = False

	# if we have found a good analysis:
	with locks["stdout"]:
		print "== Level {0}: Found best MVA to be {1}.".format(level, bestMva.mvaCfg["name"])
	
	# removing the others
	if cfg.mvaCfg["removebadana"] == "y":
		for thisCfg in [ result[4] for result in results ]:
			if thisCfg is not bestMva: 
				os.system("rm "+thisCfg.mvaCfg["outputdir"]+"/"+thisCfg.mvaCfg["name"]+"*")
	
	# if the sig/bkg-like subsets doesn't have enough MC => remove this subset, but still keep branch if enough MC events
	if stopSigLike:
		if removeSigLike:
			if cfg.mvaCfg["removebadana"] == "y":
				os.system("rm " + bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike*")
			with locks["stdout"]:
				print "== Level {0}: {1} is the best MVA, but sig-like subset doesn't have enough MC events => excluding it.".format(level, bestMva.mvaCfg["name"])
		else:
			with locks["stdout"]:
				print "== Level {0}: {1} is the best MVA, but sig-like subset doesn't have enough MC events to train another MVA => stopping here.".format(level, bestMva.mvaCfg["name"])
			with locks["tree"]:
				branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike"
				tree.append(branch)
	
	if stopBkgLike:
		if removeBkgLike:
			if cfg.mvaCfg["removebadana"] == "y":
				os.system("rm " + bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike*")
			with locks["stdout"]:
				print "== Level {0}: {1} is the best MVA, but bkg-like subset doesn't have enough MC events => excluding it.".format(level, bestMva.mvaCfg["name"])
		else:
			with locks["stdout"]:
				print "== Level {0}: {1} is the best MVA, but bkg-like subset doesn't have enough MC events to train another MVA => stopping here.".format(level, bestMva.mvaCfg["name"])
			with locks["tree"]:
				branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike"
				tree.append(branch)

	# if max level reached, stop this branch and log results in tree
	if level == int(cfg.mvaCfg["maxlevel"]):
		with locks["stdout"]:
			print "== Level {0}: Reached max level. Stopping the branch.".format(level)
		with locks["tree"]:
			if not removeSigLike:
				branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike"
				if not tree.__contains__(branch):
					tree.append(branch)
			if not removeBkgLike:
				branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike"
				if not tree.__contains__(branch):
					tree.append(branch)
		return []
	
	# starting two new "tries", one for signal-like events, the other one for background-like
	# unless one of those doesn't have enough MC
	cfgSigLike = copy.deepcopy(bestMva)
	cfgBkgLike = copy.deepcopy(bestMva)

	cfgSigLike.mvaCfg["outputdir"] = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_SigLike"
	cfgSigLike.mvaCfg["previousbranch"] = cfg.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike"

	cfgBkgLike.mvaCfg["outputdir"] = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_BkgLike"
	cfgBkgLike.mvaCfg["previousbranch"] = cfg.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike"

	for proc in cfgSigLike.procCfg:
		proc["path"] = bestMva.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_siglike_proc_" + proc["name"] + ".root"
		if proc["signal"] == "-1":
			proc["signal"] = "1"
	for proc in cfgBkgLike.procCfg:
		proc["path"] = bestMva.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_bkglike_proc_" + proc["name"] + ".root"
		if proc["signal"] == "-1":
			proc["signal"] = "1"

	if not stopSigLike:
		configs.append(cfgSigLike)
	if not stopBkgLike:
		configs.append(cfgBkgLike)

	return configs
