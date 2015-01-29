#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

argConf = 1
argExec = 2

from ROOT import *
import sys
import os
from threading import Thread,RLock
import time
import copy
from subprocess import call

from utils import PConfig

######## CLASS TRYMISCHIEF #####################################################

class tryMisChief(Thread):

	def __init__(self, level, cfg, locks, tree):
		Thread.__init__(self)
		self.level = level
		self.cfg = cfg
		self.locks = locks
		self.tree = tree

	def run(self):
		if not os.path.isdir(self.cfg.mvaCfg["outputdir"]):
			os.makedirs(self.cfg.mvaCfg["outputdir"])
		
		# for each data that is marked as signal, create specific
		# configuration and launch thread
		threads = []
		configs = []
		for data in self.cfg.dataCfg:
			if data["signal"] == "1":
				# copy previous configuration and adapt it
				thisCfg = copy.deepcopy(self.cfg)
				bkgName = ""
				inputVar = ""
				# this part has still to be worked out:
				for data2 in thisCfg.dataCfg:
					if data2 != data and data2["signal"] == "1":
						data2["signal"] = "-1"
					if data2["signal"] == "0":
						bkgName += "_" + data2["name"]
						inputVar += data2["weightname"] + ","
				thisCfg.mvaCfg["name"] = data["name"] + "_vs" + bkgName
				thisCfg.mvaCfg["inputvar"] = thisCfg.mvaCfg["otherinputvar"] + "," + inputVar + data["weightname"]
				thisCfg.mvaCfg["splitname"] = thisCfg.mvaCfg["name"]
				thisCfg.mvaCfg["outputname"] = thisCfg.mvaCfg["name"]
				thisCfg.mvaCfg["log"] = thisCfg.mvaCfg["name"] + ".results"
				# define thread with this new configuration
				myThread = launchMisChief(self.level, thisCfg, self.locks)
				threads.append(myThread)
				configs.append(thisCfg)
		with self.locks["stdout"]:
			print "== Level {0}: Starting {1} mva threads.".format(self.level, len(threads))

		# launching the analyses and waiting for them to finish
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		
		# find the one giving the best results (as long as it fulfills the conditions)
		# it would be nice to have several ways to choose the best one...
		# it may be that no analysis has enough MC events to continue => still keep only the best one, but stop branch
		# (hence:)
		bestFigGoodMC = 0.
		bestMvaGoodMC = None
		bestFigNoMC = 0.
		bestMvaNoMC = None
		# exclude the ones that didn't end successfully:
		configs = [ cfg for cfg in configs if cfg.mvaCfg["outcode"] == 0 ]
		if len(configs) == 0:
			with self.locks["stdout"]:
				print "== Level {0}: All analyses seem to have failed. Stopping branch.".format(self.level)
			return 0
		
		for thisCfg in configs:
			with open(thisCfg.mvaCfg["outputdir"] + "/" + thisCfg.mvaCfg["log"], "r") as logFile:
				logResults = [ line for line in logFile.read().split("\n") if line != "" ]
				minMCEvents = int(logResults[2])
				sigEff = float(logResults[0])
				bkgEff = float(logResults[1])
				if bkgEff > 0.:
					if sigEff/bkgEff > bestFigNoMC:
						bestFigNoMC = sigEff/bkgEff
						bestMvaNoMC = thisCfg
					if sigEff/bkgEff > bestFigGoodMC and minMCEvents >= int(self.cfg.mvaCfg["minmcevents"]):
						if float(self.cfg.mvaCfg["maxbkgeff"]) > 0.:
							if sigEff/bkgEff > float(self.cfg.mvaCfg["workingpoint"])/float(self.cfg.mvaCfg["maxbkgeff"]):
								bestFigGoodMC = sigEff/bkgEff
								bestMvaGoodMC = thisCfg
						else:
							bestFigGoodMC = sigEff/bkgEff
							bestMvaGoodMC = thisCfg
				else:
					# something went wrong. Remove this analysis from pool and the other ones go on, but don't remove the files (=> investigate problem)
					with self.locks["stdout"]:
						print "== Level " + str(level) + ": Something went wrong in analysis " + thisCfg.mvaCfg["outputdir"] + "/" + thisCfg.mvaCfg["name"] + ". Excluding it."

		# if all of them have had a problem:
		if bestMvaGoodMC is None and bestMvaNoMC is None:
			with self.locks["stdout"]:
				print "== Level {0}: All analyses seem to have had a problem. Stopping branch.".format(self.level)
			return 0

		# if no analysis has enough MC, stop this branch and keep only the best remaining analysis
		if bestMvaGoodMC is None:
			with self.locks["stdout"]:
				print "== Level {0}: Found best mva to be {1}, but no analysis with sufficient MC events. Stopping the branch.".format(self.level, bestMvaNoMC.mvaCfg["name"])
			# log the result in the tree:
			with self.locks["tree"]:
				branch = bestMvaNoMC.mvaCfg["outputdir"] + "/" + bestMvaNoMC.mvaCfg["name"]
				self.tree.append(branch)
			# removing the others
			if self.cfg.mvaCfg["removebadana"] == "y":
				for thisCfg in configs:
					if thisCfg is not bestMvaNoMC: 
						os.system("rm "+thisCfg.mvaCfg["outputdir"]+"/"+thisCfg.mvaCfg["name"]+"*")
			return 0

		# if we have found a good analysis:
		with self.locks["stdout"]:
			print "== Level {0}: Found best mva to be {1}.".format(self.level, bestMvaGoodMC.mvaCfg["name"])
	
		## log the result in the tree:
		#with self.locks["tree"]:
		#	branch = bestMvaGoodMC.mvaCfg["outputdir"] + "/" + bestMvaGoodMC.mvaCfg["name"]
		#	self.tree.append(branch)

		# removing the others
		if self.cfg.mvaCfg["removebadana"] == "y":
			for thisCfg in configs:
				if thisCfg is not bestMvaGoodMC: 
					os.system("rm "+thisCfg.mvaCfg["outputdir"]+"/"+thisCfg.mvaCfg["name"]+"*")

		# if max level reached, stop this branch
		if self.level == int(self.cfg.mvaCfg["maxlevel"]):
			with self.locks["stdout"]:
				print "== Level {0}: Reached max level. Stopping the branch.".format(self.level)
			with self.locks["tree"]:
				branch = bestMvaGoodMC.mvaCfg["outputdir"] + "/" + bestMvaGoodMC.mvaCfg["name"]
				self.tree.append(branch)
			return 0

		# starting two new "tries", one for signal-like events, the other one for background-like
		cfgSigLike = copy.deepcopy(bestMvaGoodMC)
		cfgBkgLike = copy.deepcopy(bestMvaGoodMC)

		cfgSigLike.mvaCfg["outputdir"] = bestMvaGoodMC.mvaCfg["outputdir"] + "/" + bestMvaGoodMC.mvaCfg["name"] + "_SigLike"
		cfgBkgLike.mvaCfg["outputdir"] = bestMvaGoodMC.mvaCfg["outputdir"] + "/" + bestMvaGoodMC.mvaCfg["name"] + "_BkgLike"

		for data in cfgSigLike.dataCfg:
			data["path"] = bestMvaGoodMC.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_data_" + data["name"] + "_siglike.root"
			if data["signal"] == "-1":
				data["signal"] = "1"
		for data in cfgBkgLike.dataCfg:
			data["path"] = bestMvaGoodMC.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_data_" + data["name"] + "_bkglike.root"
			if data["signal"] == "-1":
				data["signal"] = "1"

		threadSig = tryMisChief(self.level+1, cfgSigLike, self.locks, self.tree)
		threadBkg = tryMisChief(self.level+1, cfgBkgLike, self.locks, self.tree)

		threadSig.start()
		threadBkg.start()

		threadSig.join()
		threadBkg.join()

######## CLASS LAUNCHMISCHIEF #####################################################

class launchMisChief(Thread):
	def __init__(self, level, cfg, locks):
		Thread.__init__(self)
		self.level = level
		self.cfg = cfg
		self.locks = locks

	def run(self):
		# write the config file that will be used for this analysis
		with open(self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + ".conf", "w") as configFile:
			for i,data in enumerate(self.cfg.dataCfg):
				configFile.write("[data_" + str(i) + "]\n")
				for key, value in data.items():
					configFile.write(key + " = " + value + "\n")
				configFile.write("\n")
			configFile.write("[analysis]\n")
			for key, value in self.cfg.mvaCfg.items():
				configFile.write(key + " = " + str(value) + "\n")

		# launch the program on this config file
		commandString = sys.argv[argExec] + " " + self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + ".conf"
		commandString += " > " + self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + ".log 2>&1"
		if commandString.find("&&") >= 0 or commandString.find("|") >= 0:
			with self.locks["stdout"]:
				print "== Looks like a security issue..."
			sys.exit(1)
		result = call(commandString, shell=True)
		self.cfg.mvaCfg["outcode"] = result
		if result != 0:
			with self.locks["stdout"]:
				print "== Something went wrong (error code " + str(result) + ") in analysis " + self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + ". Excluding it."

######## ANALYSE TREE #############################################################

def printTree(cfg, tree):
	print "== Results of the analysis:"

	for branch in tree:
	
		print "== Branch " + branch + ":"
		print "=== Background-like:"

		for data in cfg.dataCfg:
			fileName = branch + "_data_" + data["name"] + "_bkglike.root"
			file = TFile(fileName, "READ")
			if file.IsZombie():
				print "=== Error opening " + fileName + "."
				sys.exit(1)
			tree = file.Get(data["treename"])
			expectedEvents = float(cfg.mvaCfg["lumi"])*float(data["xsection"])*tree.GetEntries()/int(data["genevents"])
			print "==== " + data["name"] + ": " + str(tree.GetEntries()) + " MC events, " \
				+ "{0:.1f}".format(expectedEvents) + " expected events."
			file.Close()

		print "=== Signal-like:"

		for data in cfg.dataCfg:
			fileName = branch + "_data_" + data["name"] + "_siglike.root"
			file = TFile(fileName, "READ")
			if file.IsZombie():
				print "=== Error opening " + fileName + "."
				sys.exit(1)
			tree = file.Get(data["treename"])
			expectedEvents = float(cfg.mvaCfg["lumi"])*float(data["xsection"])*tree.GetEntries()/int(data["genevents"])
			print "==== " + data["name"] + ": " + str(tree.GetEntries()) + " MC events, " \
				+ "{0:.1f}".format(expectedEvents) + " expected events."
			file.Close()

######## WRITE RESULTS #############################################################

def writeResults(cfg, tree):
	fileName = cfg.mvaCfg["outputdir"] + "/" + cfg.mvaCfg["name"] + "_results.out"
	print "== Writing results to " + fileName + "."

	with open(fileName, "w") as outFile:
		count = 0
		for branch in tree:
			outFile.write(str(count) + ":" + branch + "_bkglike:")
			for data in cfg.dataCfg:
				file = TFile(branch + "_data_" + data["name"] + "_bkglike.root", "READ")
				tree = file.Get(data["treename"])
				expectedEvents = float(cfg.mvaCfg["lumi"])*float(data["xsection"])*tree.GetEntries()/int(data["genevents"])
				outFile.write(data["name"] + "={0:.3f}".format(expectedEvents) + ",")
				file.Close()
			count += 1
			outFile.write("\n" + str(count) +":" + branch + "_siglike:")
			for data in cfg.dataCfg:
				file = TFile(branch + "_data_" + data["name"] + "_siglike.root", "READ")
				tree = file.Get(data["treename"])
				expectedEvents = float(cfg.mvaCfg["lumi"])*float(data["xsection"])*tree.GetEntries()/int(data["genevents"])
				outFile.write(data["name"] + "={0:.3f}".format(expectedEvents) + ",")
				file.Close()
			outFile.write("\n")
			count += 1

######## MAIN #############################################################

def driverMain(cfgFile):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	print "== Reading configuration file {0}".format(cfgFile)
	myConfig = PConfig(cfgFile)
	locks = {}
	locks["stdout"] = RLock()
	locks["tree"] = RLock()
	tree = []
	mainThread = tryMisChief(1, myConfig, locks, tree)
	print "== Starting main thread."
	mainThread.start()
	mainThread.join()
	print "== Main thread stopped."
	printTree(myConfig, tree)
	writeResults(myConfig, tree)
	print "============================================="

if __name__ == "__main__":
	driverMain(sys.argv[argConf])
