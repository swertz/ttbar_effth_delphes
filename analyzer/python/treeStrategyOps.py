# Not to be used as standalone file

import sys
import copy

def defineNewCfgs(cfg):
	""" Create specific tmva configuration object and return a list with all the configurations.
	Each of them will be used to launch a thread. """
	
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
