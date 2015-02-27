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
import treeStrategyOps
import treeStrategyMIS

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

		# Define new configurations based on the one passed to this "try":
		configs = defineNewCfgs(self.cfg)
		
		# Define threads with the new configurations
		threads = []
		for thisCfg in configs:
			myThread = launchMisChief(self.level, thisCfg, self.locks)
			threads.append(myThread)
			configs.append(thisCfg)
		
		with self.locks["stdout"]:
			print "== Level {0}: Starting {1} mva threads.".format(self.level, len(threads))

		# Launching the analyses and waiting for them to finish
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		
		# Find the one giving the best results (as long as it fulfills the conditions)
		# (it would be nice to have several ways to choose the best one...)
		# If an analysis only has enough MC events in the sig-/bkg-selection, only keep that part
		# It may be that no analysis has enough MC events to continue => stop branch
		# It there are not enough MC events to keep the branch, remove it
		
		# exclude the ones that didn't end successfully ("outcode" != 0) :
		configs = [ cfg for cfg in configs if cfg.mvaCfg["outcode"] == 0 ]
		if len(configs) == 0:
			with self.locks["stdout"]:
				print "== Level {0}: All analyses seem to have failed. Stopping branch.".format(self.level)
			return 0

		# Build a list containing a tuple (sigEff, bkgEff, minMCEventsSig, minMCEventsBkg, config)
		# The list will be used to select the best MVA (by some criteria) and to decide whether to:
		# - Define two new branches, one for the signal subset, one for the background subset, and go on with the training
		# - Do not go on with one of the subsets, because of insufficient MC for training, 
		#	but either keep the corresponding box (sufficient MC for box)
		#	or forget about it and continue training on the other subset.
		# - Stop here (no good MVA, or no sufficient MC for training), but for each subset, either
		#	keep the corresponding box (sufficient MC for box)
		#	or forget about it.

		mvaResults = []
		
		for thisCfg in configs:
			with open(thisCfg.mvaCfg["outputdir"] + "/" + thisCfg.mvaCfg["log"], "r") as logFile:
				
				logResults = [ line for line in logFile.read().split("\n") if line != "" ]
				
				minMCEventsSig = int(logResults[2])
				minMCEventsBkg = int(logResults[3])
				
				sigEff = float(logResults[0])
				bkgEff = float(logResults[1])
				
				if bkgEff > 0.:
					if bkgEff < float(self.cfg.mvaCfg["maxbkgeff"]) or float(self.cfg.mvaCfg["maxbkgeff"]) == 0.:
						mvaResults.append( (sigEff, bkgEff, minMCEventsSig, minMCEventsBkg, thisCfg) )
					
				else:
					# Something went wrong. Remove this analysis from pool and the other ones go on, but don't remove the files (=> investigate problem)
					with self.locks["stdout"]:
						print "== Level " + str(level) + ": Something went wrong in analysis " + thisCfg.mvaCfg["outputdir"] + "/" + thisCfg.mvaCfg["name"] + ". Excluding it."

		# Sort the resulting according to decreasing discrimination
		mvaResults.sort(reverse = True, key = lambda entry: entry[0]/entry[1] )

		# If no analysis has enough MC, stop this branch and remove the bad analyses if asked for
		# and log the previous node of the branch in the tree, if this node is not yet in it (it might have been added by another parallel branch)
		if len( [ result for result in mvaResults if result[2] >= int(self.cfg.mvaCfg["minkeepevents"]) and result[3] >= int(self.cfg.mvaCfg["minkeepevents"]) ] ) == 0:
			with self.locks["stdout"]:
				print "== Level {0}: Found no MVA to have enough MC events. Stopping branch.".format(self.level)
			if self.level != 1:
				with self.locks["tree"]:
					branch = self.cfg.mvaCfg["previousbranch"]
					if not self.tree.__contains__(branch):
						self.tree.append(branch)
			if self.cfg.mvaCfg["removebadana"] == "y":
				for thisCfg in configs:
					os.system("rm "+thisCfg.mvaCfg["outputdir"]+"/"+thisCfg.mvaCfg["name"]+"*")
				os.system("rmdir "+self.cfg.mvaCfg["outputdir"])
			return 0

		# For now: take most discriminating MVA. One might decide to do other things,
		# such as take best best MVA, provided one has enough MC to continue (otherwise, take second-best, and so on)

		bestMva = mvaResults[0][4]
		removeSigLike = False
		removeBkgLike = False
		stopSigLike = False
		stopBkgLike = False
		
		if mvaResults[0][2] < int(self.cfg.mvaCfg["minkeepevents"]):
			removeSigLike = True
		else:
			removeSigLike = False
		
		if mvaResults[0][2] < int(self.cfg.mvaCfg["minmcevents"]):
			stopSigLike = True
		else:
			stopSigLike = False
		
		if mvaResults[0][3] < int(self.cfg.mvaCfg["minkeepevents"]):
			removeBkgLike = True
		else:
			removeBkgLike = False
		
		if mvaResults[0][3] < int(self.cfg.mvaCfg["minmcevents"]):
			stopBkgLike = True
		else:
			stopBkgLike = False

		# if we have found a good analysis:
		with self.locks["stdout"]:
			print "== Level {0}: Found best MVA to be {1}.".format(self.level, bestMva.mvaCfg["name"])
	
		# removing the others
		if self.cfg.mvaCfg["removebadana"] == "y":
			for thisCfg in configs:
				if thisCfg is not bestMva: 
					os.system("rm "+thisCfg.mvaCfg["outputdir"]+"/"+thisCfg.mvaCfg["name"]+"*")
		
		# if the sig/bkg-like subsets doesn't have enough MC => remove this subset, but still keep branch if enough MC events
		if stopSigLike:
			if removeSigLike:
				if self.cfg.mvaCfg["removebadana"] == "y":
					os.system("rm " + bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike*")
				with self.locks["stdout"]:
					print "== Level {0}: {1} is the best MVA, but sig-like subset doesn't have enough MC events => excluding it.".format(self.level, bestMva.mvaCfg["name"])
			else:
				with self.locks["stdout"]:
					print "== Level {0}: {1} is the best MVA, but sig-like subset doesn't have enough MC events to train another MVA => stopping here.".format(self.level, bestMva.mvaCfg["name"])
				with self.locks["tree"]:
					branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike"
					self.tree.append(branch)
		
		if stopBkgLike:
			if removeBkgLike:
				if self.cfg.mvaCfg["removebadana"] == "y":
					os.system("rm " + bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike*")
				with self.locks["stdout"]:
					print "== Level {0}: {1} is the best MVA, but bkg-like subset doesn't have enough MC events => excluding it.".format(self.level, bestMva.mvaCfg["name"])
			else:
				with self.locks["stdout"]:
					print "== Level {0}: {1} is the best MVA, but bkg-like subset doesn't have enough MC events to train another MVA => stopping here.".format(self.level, bestMva.mvaCfg["name"])
				with self.locks["tree"]:
					branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike"
					self.tree.append(branch)

		# if max level reached, stop this branch and log results in tree
		if self.level == int(self.cfg.mvaCfg["maxlevel"]):
			with self.locks["stdout"]:
				print "== Level {0}: Reached max level. Stopping the branch.".format(self.level)
			with self.locks["tree"]:
				if not removeSigLike:
					branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike"
					if not self.tree.__contains__(branch):
						self.tree.append(branch)
				if not removeBkgLike:
					branch = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike"
					if not self.tree.__contains__(branch):
						self.tree.append(branch)
			return 0
		
		# starting two new "tries", one for signal-like events, the other one for background-like
		# unless one of those doesn't have enough MC
		cfgSigLike = copy.deepcopy(bestMva)
		cfgBkgLike = copy.deepcopy(bestMva)

		cfgSigLike.mvaCfg["outputdir"] = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_SigLike"
		cfgSigLike.mvaCfg["previousbranch"] = self.cfg.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_siglike"

		cfgBkgLike.mvaCfg["outputdir"] = bestMva.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_BkgLike"
		cfgBkgLike.mvaCfg["previousbranch"] = self.cfg.mvaCfg["outputdir"] + "/" + bestMva.mvaCfg["name"] + "_bkglike"

		for proc in cfgSigLike.procCfg:
			proc["path"] = bestMva.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_siglike_proc_" + proc["name"] + ".root"
			if proc["signal"] == "-1":
				proc["signal"] = "1"
		for proc in cfgBkgLike.procCfg:
			proc["path"] = bestMva.mvaCfg["outputdir"] + "/" + cfgSigLike.mvaCfg["name"] + "_bkglike_proc_" + proc["name"] + ".root"
			if proc["signal"] == "-1":
				proc["signal"] = "1"

		threadSig = tryMisChief(self.level+1, cfgSigLike, self.locks, self.tree)
		threadBkg = tryMisChief(self.level+1, cfgBkgLike, self.locks, self.tree)

		if not stopSigLike:
			threadSig.start()
		if not stopBkgLike:
			threadBkg.start()

		if not stopSigLike:
			threadSig.join()
		if not stopBkgLike:
			threadBkg.join()

######## CLASS LAUNCHMISCHIEF #####################################################
# Define new configuration objects based on chosen tree-building strategy 

def defineNewCfgs(cfg):

	if cfg.mvaCfg["mode"] == "operators":
		return treeStrategyOps.defineNewCfgs(cfg)

	elif cfg.mvaCfg["mode"] == "MIS":
		return treeStrategyMIS.defineNewCfgs(cfg)

	else:
		print "== Tree building strategy not properly defined."
		sys.exit(1)

######## CLASS LAUNCHMISCHIEF #####################################################
# Launch a MVA based on a configuration passed by tryMisChief

class launchMisChief(Thread):
	def __init__(self, level, cfg, locks):
		Thread.__init__(self)
		self.level = level
		self.cfg = cfg
		self.locks = locks

	def run(self):
		# write the config file that will be used for this analysis
		with open(self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + ".conf", "w") as configFile:
			for i,proc in enumerate(self.cfg.procCfg):
				configFile.write("[proc_" + str(i) + "]\n")
				for key, value in proc.items():
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
# Print tree structure and branch yields

def printTree(cfg, tree):
	print "== Results of the analysis:"

	for branch in tree:
	
		print "== Branch " + branch + ":"

		for proc in cfg.procCfg:
			fileName = branch + "_proc_" + proc["name"] + ".root"
			file = TFile(fileName, "READ")
			if file.IsZombie():
				print "== Error opening " + fileName + "."
				sys.exit(1)
			tree = file.Get(proc["treename"])
			expectedEvents = float(cfg.mvaCfg["lumi"])*float(proc["xsection"])*tree.GetEntries()/int(proc["genevents"])
			print "=== " + proc["name"] + ": " + str(tree.GetEntries()) + " MC events, " \
				+ "{0:.1f}".format(expectedEvents) + " expected events."
			file.Close()

######## WRITE RESULTS #############################################################
# Write tree structure and branch yields to a file

def writeResults(cfg, tree):
	fileName = cfg.mvaCfg["outputdir"] + "/" + cfg.mvaCfg["name"] + "_results.out"
	print "== Writing results to " + fileName + "."

	with open(fileName, "w") as outFile:
		count = 0
		for branch in tree:
			outFile.write(str(count) + ":" + branch + ":")
			for proc in cfg.procCfg:
				fileName = branch + "_proc_" + proc["name"] + ".root"
				file = TFile(fileName, "READ")
				if file.IsZombie():
					print "== Error opening " + fileName + "."
					sys.exit(1)
				tree = file.Get(proc["treename"])
				expectedEvents = float(cfg.mvaCfg["lumi"])*float(proc["xsection"])*tree.GetEntries()/int(proc["genevents"])
				outFile.write(proc["name"] + "={0:.3f}".format(expectedEvents) + ",")
				file.Close()
			outFile.write("\n")
			count += 1

######## PLOT RESULTS #############################################################
# Create ROOT file with, for each process, plots:
# - one bin/branch (=yields)
# - juxtaposing the MVA outputs for each branch
# - 2D plot with efficiencies for each branch

def plotResults(cfg, tree):
	fileName = cfg.mvaCfg["outputdir"] + "/" + cfg.mvaCfg["name"] + "_hists.root"
	print "== Writing histograms to " + fileName + "."

	file = TFile(fileName, "RECREATE")

	nBr = len(tree)
	nProc = len(cfg.procCfg)
	nBins = int(cfg.mvaCfg["histbins"])
	nFitBins = int(cfg.mvaCfg["fitbins"])

	branchTotals = TH1D("branch_tot", "Branch totals", nBr, 0, nBr)
	lst = TList()

	branchEffs = TH2D("branch_effs", "Branch efficiencies (%)", nBr, 0, nBr, nProc, 0, nProc)
	branchYields = TH2D("branch_yields", "Branch yields", nBr, 0, nBr, nProc, 0, nProc)
	treeYields = {}
	treeMVAs = {}
		
	# To join the MVA ouputs, we have to be careful, since there is a single MVA histogram for a sig/bkg pair.
	# Thus, we have to skim the tree, to keep only the names of the MVAs, not their sig/bkg subsets
	# We will then keep sig/bkg subsets which had been rejected in the tree building because of insufficient MC.
	# Is it a problem????
	skimmedTree = copy.deepcopy(tree)
	# Remove the sig/bkg component
	skimmedTree = [ branch.split("_siglike")[0] for branch in skimmedTree ]
	skimmedTree = [ branch.split("_bkglike")[0] for branch in skimmedTree ]
	# Remove duplicates
	skimmedTree = list(set(skimmedTree))
	nBrSkimmed = len(skimmedTree)
	
	for i,proc in enumerate(cfg.procCfg):
		
		treeYields[ proc["name"] ] = TH1D(proc["name"] + "_yields", "Branch yields for " + proc["name"], nBr, 0, nBr)
		
		treeMVAs[ proc["name"] ] = TH1D(proc["name"] + "_MVAs", "MVA histograms for " + proc["name"], nBrSkimmed*nFitBins, 0, nBrSkimmed*nFitBins)

		procFile = TFile(proc["path"], "READ")
		procTree = procFile.Get(proc["treename"])
		procTotMC = procTree.GetEntries()
		procFile.Close()
		
		for j,branch in enumerate(tree):
		
			branchProcFile = TFile(branch + "_proc_" + proc["name"] + ".root", "READ")
			branchTree = branchProcFile.Get(proc["treename"])
			branchMC = branchTree.GetEntries()
			branchProcFile.Close()

			branchEffs.SetBinContent(j+1, i+1, 100.*float(branchMC)/procTotMC)
			branchEffs.GetYaxis().SetBinLabel(i+1, proc["name"])
			branchEffs.GetXaxis().SetBinLabel(j+1, branch)

			branchYield = branchMC * float(cfg.mvaCfg["lumi"]) * float(proc["xsection"]) / int(proc["genevents"])
			treeYields[ proc["name"] ].SetBinContent(j+1, branchYield)
			treeYields[ proc["name"] ].GetXaxis().SetBinLabel(j+1, branch)

			branchYields.SetBinContent(j+1, i+1, branchYield)
			branchYields.GetYaxis().SetBinLabel(i+1, proc["name"])
			branchYields.GetXaxis().SetBinLabel(j+1, branch)

		for j,branch in enumerate(skimmedTree):

			branchFile = TFile(branch + ".root", "READ")
			procHist = branchFile.Get(proc["name"] + "_output").Rebin(nBins/nFitBins)
			
			for k in range(1, nFitBins+1):
				treeMVAs[ proc["name"] ].SetBinContent(j*nFitBins+k, procHist.GetBinContent(k))

			branchFile.Close()

		file.cd()

		treeYields[ proc["name"] ].Write()
		lst.Add(treeYields[ proc["name"] ])
		treeMVAs[ proc["name"] ].Write()

	branchTotals.Merge(lst)
	branchComps = branchYields.Clone("branch_comps")
	branchComps.SetTitle("Branch compositions (%)")
	for j in range(1, nBr+1):
		for i in range(1, nProc+1):
			branchComps.SetBinContent(j, i, 100.* branchComps.GetBinContent(j, i) / branchTotals.GetBinContent(j) )

	file.cd()
	branchEffs.Write()
	branchYields.Write()
	branchComps.Write()
	file.Close()

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
	plotResults(myConfig, tree)
	print "============================================="

if __name__ == "__main__":
	driverMain(sys.argv[argConf])
