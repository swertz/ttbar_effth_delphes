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
from threading import Thread
from threading import RLock
import time
import copy
from subprocess import call
import pickle

from utils import PConfig
import treeStrategyOps
import treeStrategyMIS

from treeStructure import MISTree
from treeStructure import MISBox
from treeStructure import MISAnalysis

######## CLASS TRYMISCHIEF #####################################################

class tryMisChief(Thread):

	def __init__(self, box, locks):
		Thread.__init__(self)
		self.box = box
		self.locks = locks

	def run(self):
		self.log("Starting try.")

		if not os.path.isdir(self.box.cfg.mvaCfg["outputdir"]):
			os.makedirs(self.box.cfg.mvaCfg["outputdir"])

		# Define new configurations based on the one passed to this "try":
		defineNewCfgs(self.box, self.locks)
		
		# Define threads with the new configurations
		threads = []
		for thisMVA in self.box.MVA:
			myThread = launchMisChief(thisMVA, self.locks)
			threads.append(myThread)
		
		with self.locks["stdout"]:
			self.log("Will start " + str(len(threads)) + " threads.")
			print "== Level {0}: Starting {1} mva threads.".format(self.box.level, len(threads))

		# Launching the analyses and waiting for them to finish
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		
		self.log("Threads finished.")

		# Exclude the ones that didn't end successfully (no result tuple)
		goodMVAs = [ mva for mva in self.box.MVA if mva.result is not None ]
		if len(goodMVAs) == 0:
			self.log("All analysis failed. Stopping branch.")
			with self.locks["stdout"]:
				print "== Level {0}: All analyses seem to have failed. Stopping branch.".format(self.box.level)
			return 0

		# Decide what to do next and define next boxes 
		analyseResults(self.box, self.locks)
		nextBoxes = [ box for box in self.box.daughters if not box.isEnd ]

		# Launch and define next threads, if any
		if len(nextBoxes) != 0:
			nextThreads = []

			for thisBox in nextBoxes:
				thisThread = tryMisChief(thisBox, self.locks)
				nextThreads.append(thisThread)

				self.log("Will launch " + str(len(nextThreads)) + " new tries and pass the hand.")

			for thread in nextThreads:
				thread.start()

			for thread in nextThreads:
				thread.join()

		self.log("Try finished successfully.")

######## MODULAR TREE ############################################################
# Define new configuration objects based on chosen tree-building strategy 

def defineNewCfgs(box, locks):

	if box.cfg.mvaCfg["mode"] == "operators":
		return treeStrategyOps.defineNewCfgs(box, locks)

	elif box.cfg.mvaCfg["mode"] == "MIS":
		return treeStrategyMIS.defineNewCfgs(box, locks)

	else:
		print "== Tree building strategy not properly defined."
		sys.exit(1)

# Decide what to based on the results of the tmvas:

def analyseResults(box, locks):

	if box.cfg.mvaCfg["mode"] == "operators":
		return treeStrategyOps.analyseResults(box, locks)

	elif box.cfg.mvaCfg["mode"] == "MIS":
		return treeStrategyMIS.analyseResults(box, locks)

	else:
		print "== Tree building strategy not properly defined."
		sys.exit(1)

######## CLASS LAUNCHMISCHIEF #####################################################
# Launch a MVA based on a configuration passed by tryMisChief

class launchMisChief(Thread):
	def __init__(self, MVA, locks):
		Thread.__init__(self)
		self.MVA = MVA
		self.locks = locks

	def run(self):
		# write the config file that will be used for this analysis
		with open(self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + ".conf", "w") as configFile:
			
			self.MVA.log("Writing config file.")
			
			for i,proc in enumerate(self.MVA.cfg.procCfg):
				
				configFile.write("[proc_" + str(i) + "]\n")
				
				for key, value in proc.items():
					configFile.write(key + " = " + value + "\n")
				
				configFile.write("\n")
			
			configFile.write("[analysis]\n")
			
			for key, value in self.MVA.cfg.mvaCfg.items():
				configFile.write(key + " = " + str(value) + "\n")

		# launch the program on this config file
		commandString = sys.argv[argExec] + " " + self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + ".conf"
		commandString += " > " + self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + ".log 2>&1"

		# it would be annoying if, say, outputdir was "&& rm -rf *"
		if commandString.find("&&") >= 0 or commandString.find("|") >= 0:
			with self.locks["stdout"]:
				print "== Looks like a security issue..."
			sys.exit(1)

		self.MVA.log("Calling " + commandString + ".")

		result = call(commandString, shell=True)

		self.MVA.log("Finished. Output code = " + str(result) + ".")
		self.MVA.outcode = result
		if result != 0:
			with self.locks["stdout"]:
				print "== Something went wrong (error code " + str(result) + ") in analysis " + self.MVA.cfg.mvaCfg["outputdir"] + "/" + self.MVA.cfg.mvaCfg["name"] + "."
		else:
			self.MVA.fetchResults()

######## ANALYSE TREE #############################################################
# Print tree structure and branch yields

def printTree(cfg, tree):
	tree.log("Printing analysis results.")
	print "== Results of the analysis:"
	tree.print()

######## WRITE RESULTS #############################################################
# Write tree structure and branch yields to a file

def writeResults(tree):
	fileName = tree.cfg.mvaCfg["outputdir"] + "/" + tree.cfg.mvaCfg["name"] + "_results.out"
	tree.log("Writing analysis results to " + fileName + ".")
	print "== Writing results to " + fileName + "."

	with open(fileName, "w") as outFile:
		tree.write(outFile)

######## PLOT RESULTS #############################################################
# Create ROOT file with, for each process, plots:
# - one bin/branch (=yields)
# - juxtaposing the MVA outputs for each branch ==> to do: also for "half-branches"
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

	gROOT.SetBatch(kTRUE);

	branchEffs.Write()
	cnv = TCanvas("cnv_branch_effs", "Branch Efficiencies", 900, 600)
	pad = TPad("branch_effs", "Branch Efficiencies", 0, 0, 1, 1, 0)
	pad.Draw()
	pad.cd()
	branchEffs.SetStats(kFALSE)
	branchEffs.Draw("COL,TEXT,Z")
	cnv.Write()
	del cnv

	branchYields.Write()
	cnv = TCanvas("cnv_branch_yield", "Branch Yields", 900, 600)
	pad = TPad("branch_yield", "Branch Yields", 0, 0, 1, 1, 0)
	pad.Draw()
	pad.cd()
	branchYields.SetStats(kFALSE)
	pad.SetLogz()
	branchYields.Draw("COL,TEXT,Z")
	cnv.Write()
	del cnv

	branchComps.Write()
	cnv = TCanvas("cnv_branch_comps", "Branch Compositions", 900, 600)
	pad = TPad("branch_comps", "Branch Compositions", 0, 0, 1, 1, 0)
	pad.Draw()
	pad.cd()
	branchComps.SetStats(kFALSE)
	pad.SetLogz()
	branchComps.Draw("COL,TEXT,Z")
	cnv.Write()
	del cnv

	file.Close()

######## MAIN #############################################################

def driverMain(cfgFile):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	print "== Reading configuration file {0}".format(cfgFile)
	myConfig = PConfig(cfgFile)
	myTree = MISTree(myConfig)
	locks = {}
	locks["stdout"] = RLock()
	mainThread = tryMisChief(myTree.firstBox, locks)
	print "== Starting main thread."
	mainThread.start()
	mainThread.join()
	print "== Main thread stopped."
	printTree(myTree)
	writeResults(myTree)
	plotResults(myTree)
	print "============================================="

if __name__ == "__main__":
	driverMain(sys.argv[argConf])
