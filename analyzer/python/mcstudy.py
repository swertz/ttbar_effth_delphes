#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

import ROOT
import sys
import os
import numpy as np
import math

from lstSqCountingFitter import weightedLstSqCountingFit
from utils import PMCConfig
from utils import PConfig
from utils import PResult

######## MC STUDY MAIN #############################################################

def mcStudyMain(mcStudyFile):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	print "== Reading configuration file {0}".format(mcStudyFile)
	myMCStudy = PMCConfig(mcStudyFile)
	print "== Reading analysis file {0}".format(myMCStudy.cfg["mvaCfg"])
	myConfig = PConfig(myMCStudy.cfg["mvaCfg"])
	resultFile = myConfig.mvaCfg["outputdir"] + "/" + myConfig.mvaCfg["name"] + "_results.out"
	print "== Reading MVA MC tree result file {0}".format(resultFile)
	myMCResult = PResult()
	myMCResult.iniFromFile(resultFile)

	if myMCStudy.cfg["mode"] == "counting":
		outFile = ROOT.TFile(myMCStudy.cfg["outFile"], "RECREATE")
		for i,paramSet in enumerate(myMCStudy.params):
			print "== Doing a counting-experiment study using parameters:"
			print paramSet

			subDir = outFile.mkdir("params_"+str(i), "Param_Set_"+str(i))
			subDir.cd()

			histDict = {}
			corrList = {}
			weightedNormHist = ROOT.TH1D("Weighted_Norm_hist", "Weighted Norm", 100, 0, 10)
			resHist = ROOT.TH1D("Chi_Square_hist", "Chi Square", 100, 0, 50)

			varVect = []
			for i,data in enumerate(myConfig.dataCfg):
				if data["signal"] == "1":
					myHist = ROOT.TH1D(data["name"]+"_hist",data["name"]+"/\Lambda^2 (GeV^{-2})", 100, -2, 2)
					histDict[data["name"]] = myHist
					myVarHist = ROOT.TH1D(data["name"]+"_StdDev_hist",data["name"]+" Std. Dev. (GeV^{-2})", 100, 0., 1.)
					histDict[data["name"]+"_StdDev"] = myVarHist
					
					varVect.append(data["name"])
					for j,data2 in enumerate(myConfig.dataCfg):
						if data2["signal"] == "1":
							corrList[data["name"]+"/"+data2["name"]] = 0.

			histDict["weightedNorm"] = weightedNormHist
			histDict["chisq"] = resHist
			histDict["corrList"] = corrList

			pseudoNumber = int(myMCStudy.cfg["pseudoNumber"])
			mcStudyCounting(myConfig, myMCResult, paramSet, histDict, pseudoNumber) 

			nVar = len(varVect)
			corrHist = ROOT.TH2D("Correlations_hist","Correlations", nVar, 0, nVar, nVar, 0, nVar)
			for i,proc in enumerate(varVect):
				for j,proc2 in enumerate(varVect):
					corrHist.SetBinContent(i+1, j+1, corrList[proc+"/"+proc2]/pseudoNumber)
					corrHist.GetXaxis().SetBinLabel(i+1, proc)
					corrHist.GetYaxis().SetBinLabel(j+1, proc2)
			histDict["corrList"] = corrHist
			for hist in histDict.values():
				if hist.Integral() != 0 and hist.GetDimension() == 1:
					hist.Scale(1./hist.Integral())
				hist.Write()

		outFile.Close()

	else:
		print "== Mode not valid"
		sys.exit(1)

######## MC STUDY BRANCH TEMPLATES #####################################################
# Pseudo-experiments on the MC histograms for each branch

#def mcStudyBranchTemplates():
	# get histograms for the processes for each branch


######## MC STUDY SIMPLE TEMPLATES #####################################################
# Pseudo-experiments on MC histograms for a particular kinematical variable

def mcStudyTemplate():

######## MC STUDY COUNTING #############################################################
# Pseudo-experiments on the predicted number of events for each branch

def mcStudyCounting(myConfig, myMCResult, params, histDict, pseudoNumber):
	print "== Doing MC Study: counting experiment on the tree."

	branchPDFs = {}
	branchMeans = {}
	branchVars = {}
	prodname = ""

	print "== Initializing multi-dimensional PDF."

	# generate PDFs: each branch is a Poisson with
	# mean = predicted number of events in that branch,
	# depending on the parameters chosen:
	allVarVec = myMCResult.branches[0][2].keys()
	varVec = []
	for proc in allVarVec:
		for data in myConfig.dataCfg:
			if data["name"] == proc:
				if data["signal"] == "1":
					varVec.append(proc)
				break

	for branch in myMCResult.branches:
		mean = ROOT.RooRealVar(branch[1] + "_events", "Predicted number of events in branch " + branch[1], 0.)
		for proc in branch[2].keys():
			for data in myConfig.dataCfg:
				if data["name"] == proc:
					if data["signal"] == "1":
						mean.setVal(branch[2][proc]*params[proc] + mean.getVal())
					else:
						mean.setVal(branch[2][proc] + mean.getVal())
		branchMeans[ branch[1] ] = mean

		var = ROOT.RooRealVar(branch[1] + "_var", "Variable for branch " + branch[1], 0, "GeV^-2")
		branchVars[ branch[1] ] = var

		pdf = ROOT.RooPoisson(branch[1] + "_pdf", "Poisson PDF for branch " + branch[1], var, mean)
		branchPDFs[ branch[1] ] = pdf

		prodname += "*" + branch[1] + "_pdf"
	
	# remove the "*" at the beginning of the product PDF name:
	prodname = prodname[1:]
	
	# generate "total" PDF (product of each branch's PDF)
	prodPDFList = ROOT.RooArgList()
	for pdf in branchPDFs.values():
		prodPDFList.add(pdf)
	prodPDF = ROOT.RooProdPdf("total_pdf", "Total PDF for all the branches", prodPDFList)

	print "== Generating pseudo-experiments."

	# generate pseudo-expts.
	prodArgSet = ROOT.RooArgSet()
	for var in branchVars.values():
		prodArgSet.add(var)
	dataSet = prodPDF.generate(prodArgSet, pseudoNumber)

	print "== Doing a weighted least-square fit on each pseudo-experiment result."
	
	nDoF = 0
	# translate dataset element in a PResult and call fit on each pseudo-experiment
	for i in range(pseudoNumber):
		rdsRow = dataSet.get(i)
		myDataResult = PResult()
		myDataResult.iniFromRDS(myMCResult, rdsRow)
		result,chisq,nDoF,var,cov = weightedLstSqCountingFit(myConfig, myMCResult, myDataResult)
		weighteddsquare = 0.
		for proc in result.keys():
			weighteddsquare += result[proc]**2/var[proc]
			for proc2 in result.keys():
				histDict["corrList"][proc+"/"+proc2] += cov[proc+"/"+proc2]/math.sqrt(abs(var[proc]*var[proc2]))
		for proc in varVec:
			histDict[proc].Fill(result[proc])
			histDict[proc+"_StdDev"].Fill(math.sqrt(var[proc]))
		histDict["weightedNorm"].Fill(math.sqrt(weighteddsquare))
		histDict["chisq"].Fill(chisq)
	histDict["chisq"].SetTitle(histDict["chisq"].GetTitle() + " (" + str(nDoF) + " D.o.F.)")

	print "== Done."

######## MAIN #############################################################

if __name__ == "__main__":
	mcStudyMain(sys.argv[1])
