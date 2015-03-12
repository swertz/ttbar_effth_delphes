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
		configs = defineNewCfgs(self.cfg, self.locks, self.tree, self.level)
		
		# Define threads with the new configurations
		threads = []
		for thisCfg in configs:
			myThread = launchMisChief(self.level, thisCfg, self.locks)
			threads.append(myThread)
		
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
					mvaResults.append( (sigEff, bkgEff, minMCEventsSig, minMCEventsBkg, thisCfg) )
					
				else:
					# Something went wrong. Remove this analysis from pool and the other ones go on, but don't remove the files (=> investigate problem)
					with self.locks["stdout"]:
						print "== Level " + str(self.level) + ": Something went wrong in analysis " + thisCfg.mvaCfg["outputdir"] + "/" + thisCfg.mvaCfg["name"] + ". Excluding it."

		# Maybe everything went wrong:
		if len(mvaResults) == 0:
			with self.locks["stdout"]:
				print "== Level "+ str(self.level) + ": Every analysis failed. Stopping branch."
			return 0
		
		# Sort the resulting according to decreasing discrimination
		mvaResults.sort(reverse = True, key = lambda entry: entry[0]/entry[1] )

		# Decide what to do next and define next configs
		nextConfigs = analyseResults(self.cfg, mvaResults, self.locks, self.tree, self.level)

		# Launch and define next threads, if any
		if len(nextConfigs) != 0:
			nextThreads = []

			for thisCfg in nextConfigs:
				thisThread = tryMisChief(self.level+1, thisCfg, self.locks, self.tree)
				nextThreads.append(thisThread)

			for thread in nextThreads:
				thread.start()

			for thread in nextThreads:
				thread.join()

######## MODULAR TREE ############################################################
# Define new configuration objects based on chosen tree-building strategy 

def defineNewCfgs(cfg, locks, tree, level):

	if cfg.mvaCfg["mode"] == "operators":
		return treeStrategyOps.defineNewCfgs(cfg, locks, tree, level)

	elif cfg.mvaCfg["mode"] == "MIS":
		return treeStrategyMIS.defineNewCfgs(cfg, locks, tree, level)

	else:
		print "== Tree building strategy not properly defined."
		sys.exit(1)

# Decide what to based on the results of the tmvas:

def analyseResults(cfg, results, locks, tree, level):

	if cfg.mvaCfg["mode"] == "operators":
		return treeStrategyOps.analyseResults(cfg, results, locks, tree, level)

	elif cfg.mvaCfg["mode"] == "MIS":
		return treeStrategyMIS.analyseResults(cfg, results, locks, tree, level)

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

		# it would be annoying if, say, outputdir was "&& rm -rf *"
		if commandString.find("&&") >= 0 or commandString.find("|") >= 0:
			with self.locks["stdout"]:
				print "== Looks like a security issue..."
			sys.exit(1)

		result = call(commandString, shell=True)

		self.cfg.mvaCfg["outcode"] = result
		if result != 0:
			with self.locks["stdout"]:
				print "== Something went wrong (error code " + str(result) + ") in analysis " + self.cfg.mvaCfg["outputdir"] + "/" + self.cfg.mvaCfg["name"] + "."

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
			tree.Draw("This->GetReadEntry()>>tempHist", proc["evtweight"], "goff")
			tempHist = TH1F(gDirectory.Get("tempHist"))
			effEntries = tempHist.Integral()
			del tempHist
			expectedEvents = float(cfg.mvaCfg["lumi"])*float(proc["xsection"])*effEntries/int(proc["genevents"])
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
				tree.Draw("This->GetReadEntry()>>tempHist", proc["evtweight"], "goff")
				tempHist = TH1F(gDirectory.Get("tempHist"))
				effEntries = tempHist.Integral()
				del tempHist
				expectedEvents = float(cfg.mvaCfg["lumi"])*float(proc["xsection"])*effEntries/int(proc["genevents"])
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
		treeYields[ proc["name"] ].Sumw2()
		
		treeMVAs[ proc["name"] ] = TH1D(proc["name"] + "_MVAs", "MVA histograms for " + proc["name"], nBrSkimmed*nFitBins, 0, nBrSkimmed*nFitBins)
		treeMVAs[ proc["name"] ].Sumw2()

		procFile = TFile(proc["path"], "READ")
		procTree = procFile.Get(proc["treename"])
		procTree.Draw("This->GetReadEntry()>>tempHist", "abs("+proc["evtweight"]+")", "goff")
		tempHist = TH1F(gDirectory.Get("tempHist"))
		procTotEffEntriesAbs = tempHist.Integral()
		del tempHist
		procTotEntries = procTree.GetEntries()
		procFile.Close()
		
		for j,branch in enumerate(tree):
		
			branchProcFile = TFile(branch + "_proc_" + proc["name"] + ".root", "READ")
			branchTree = branchProcFile.Get(proc["treename"])
			branchTree.Draw("This->GetReadEntry()>>tempHist", proc["evtweight"], "goff")
			branchTempHist = TH1F(gDirectory.Get("tempHist"))
			branchEffEntries = branchTempHist.Integral()
			del branchTempHist
			branchProcFile.Close()

			branchEffs.SetBinContent(j+1, i+1, 100.*branchEffEntries/procTotEffEntriesAbs)
			branchEffs.GetYaxis().SetBinLabel(i+1, proc["name"])
			branchEffs.GetXaxis().SetBinLabel(j+1, branch)

			branchYield = branchEffEntries * float(cfg.mvaCfg["lumi"]) * float(proc["xsection"]) / int(proc["genevents"])
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

		treeYields[ proc["name"] ].SetEntries(procTotEntries)
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
