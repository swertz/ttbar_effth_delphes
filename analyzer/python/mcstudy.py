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
from templateFitter import templateFit
from templateFitter import fillHistos
from templateFitter import getHistos
from utils import PMCConfig
from utils import PConfig
from utils import PResult
from utils import convertWgtLstSqToTemplate 

######## MC STUDY MAIN #############################################################

def mcStudyMain(mcStudyFile):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	
	print "== Reading configuration file {0}".format(mcStudyFile)
	myMCStudy = PMCConfig(mcStudyFile)
	
	print "== Reading analysis file {0}".format(myMCStudy.cfg["anaCfg"])
	myConfig = PConfig(myMCStudy.cfg["anaCfg"])

	outFile = ROOT.TFile(myMCStudy.cfg["outFile"], "RECREATE")
	
	for i,paramSet in enumerate(myMCStudy.params):
		
		print "== Doing a pseudo-experiment study using parameters:"
		print paramSet

		subDir = outFile.mkdir("params_"+str(i), "Param_Set_"+str(i))
		subDir.cd()

		histDict = {}
		corrList = {}
		weightedNormHist = ROOT.TH1D("Weighted_Norm_hist", "Weighted Norm", 100, 0, 10)
		weightedNormHist.SetBit(ROOT.TH1.kCanRebin)
		weightedNormHist.SetDirectory(subDir)
		resHist = ROOT.TH1D("Chi_Square_hist", "Chi Square", 100, 0, 10)
		resHist.SetBit(ROOT.TH1.kCanRebin)
		resHist.SetDirectory(subDir)
		
		histDict["weightedNorm"] = weightedNormHist
		histDict["chisq"] = resHist

		varVect = []
		for i,proc in enumerate(myConfig.procCfg):
			
			if proc["signal"] == "1":
				
				procN = proc["name"]
				
				myHist = ROOT.TH1D(procN+"_hist", procN+"/\Lambda^2 (GeV^{-2})", 100, -0.5, 0.5)
				myHist.SetBit(ROOT.TH1.kCanRebin)
				myHist.SetDirectory(subDir)
				histDict[procN] = myHist
				myVarHist = ROOT.TH1D(procN+"_StdDev_hist", \
					procN+" Std. Dev. (GeV^{-2})", 100, 0., 1.)
				myVarHist.SetBit(ROOT.TH1.kCanRebin)
				myVarHist.SetDirectory(subDir)
				histDict[procN+"_StdDev"] = myVarHist
				
				varVect.append(procN)
				
				for j,proc2 in enumerate(myConfig.procCfg):
					if proc2["signal"] == "1":
						corrList[procN+"/"+proc2["name"]] = 0.

		histDict["corrList"] = corrList

		pseudoNumber = int(myMCStudy.cfg["pseudoNumber"])
	
		if myMCStudy.cfg["mode"] == "counting":
			resultFile = myConfig.mvaCfg["outputdir"] + "/" + \
				myConfig.mvaCfg["name"] + "_results.out"
		
			print "== Reading MVA MC tree result file {0}".format(resultFile)
			myMCResult = PResult()
			myMCResult.iniFromFile(resultFile)
			mcStudyCounting(myConfig, myMCResult, paramSet, histDict, pseudoNumber) 
		
		elif myMCStudy.cfg["mode"] == "template":
			myHist = ROOT.TH1D("minNLL_hist", "-log(L) at minimum", 100, -400000, -300000)
			myHist.SetBit(ROOT.TH1.kCanRebin)
			myHist.SetDirectory(subDir)
			histDict["minNLL"] = myHist
			
			mcStudyTemplate(myConfig, paramSet, histDict, pseudoNumber)

		elif myMCStudy.cfg["mode"] == "templateFromMVA":
			resultFile = myConfig.mvaCfg["outputdir"] + "/" + \
				myConfig.mvaCfg["name"] + "_results.out"
		
			print "== Reading MVA MC tree result file {0}".format(resultFile)
			myMCResult = PResult()
			myMCResult.iniFromFile(resultFile)
			
			myHist = ROOT.TH1D("minNLL_hist", "-log(L) at minimum", 100, -400000, -300000)
			myHist.SetBit(ROOT.TH1.kCanRebin)
			myHist.SetDirectory(subDir)
			histDict["minNLL"] = myHist
			
			templateCfg = convertWgtLstSqToTemplate(myConfig, myMCResult, myMCStudy.cfg["histFile"])
			
			mcStudyTemplate(templateCfg, paramSet, histDict, pseudoNumber)

		else:
			print "== Mode not valid"
			sys.exit(1)

		subDir.cd()
		
		nVar = len(varVect)
		corrHist = ROOT.TH2D("Correlations_hist","Correlations", nVar, 0, nVar, nVar, 0, nVar)
		corrHist.SetDirectory(subDir)
		for i,proc in enumerate(sorted(varVect)):
			for j,proc2 in enumerate(sorted(varVect, reverse=True)):
				if i == j:
					# factor 0.5 since this bin is filled twice when looping over proc and proc2
					corrHist.SetBinContent(i+1, j+1, 0.5*corrList[proc+"/"+proc2]/pseudoNumber)
				else:
					corrHist.SetBinContent(i+1, j+1, corrList[proc+"/"+proc2]/pseudoNumber)
				corrHist.GetXaxis().SetBinLabel(i+1, proc)
				corrHist.GetYaxis().SetBinLabel(j+1, proc2)
		histDict["corrList"] = corrHist
		
		for hist in sorted(histDict.values(), key = lambda hist: hist.GetTitle()):
			if hist.Integral() != 0 and hist.GetDimension() == 1:
				hist.Scale(1./hist.Integral())
			hist.Write()
		
	if myMCStudy.cfg["mode"] == "template":
		outFile.cd()
		for proc in sorted(myConfig.procCfg, key = lambda proc: proc["name"]):
			proc["histo"].Write()

	outFile.Close()

######## MC STUDY SIMPLE TEMPLATES #####################################################
# Pseudo-experiments on MC histograms for a particular kinematical variable

def mcStudyTemplate(templateCfg, params, histDict, pseudoNumber):
	print "== Doing MC Study: template fits on " + templateCfg.mvaCfg["inputvar"] + "."

	if not templateCfg.procCfg[0].__contains__("histo"):
		
		if templateCfg.mvaCfg["options"].find("fill") >= 0:
			# Fill histograms with the variable used for the fit, and store them in the
			# template configuration
			print "== Filling input histograms from trees."
			fillHistos(templateCfg)
		
		elif templateCfg.mvaCfg["options"].find("get") >= 0:
			# Get histograms with the variable used for the fit, and store them in the
			# template configuration
			getHistos(templateCfg)

		else:
			print "== Invalid template fit mode."
			sys.exit(1)
		
	inputVar = templateCfg.mvaCfg["inputvar"]

	dataHist = templateCfg.procCfg[0]["histo"].Clone("MCdata_" + inputVar)
	dataHist.Reset()
	dataHist.SetTitle("MC data: " + inputVar)
	
	mcSumHist = dataHist.Clone("MCsum_" + inputVar)
	mcSumHist.SetTitle("MC sum: " + inputVar)

	for proc in templateCfg.procCfg:
		if proc["signal"] == "1":
			mcSumHist.Add(proc["histo"], params[ proc["name"] ])
		else:
			mcSumHist.Add(proc["histo"])

	mcExpect = mcSumHist.Integral()
	rPoisson = ROOT.TRandom3(0)
	
	# Generate pseudo-experiments and do the fits
	print "== Carrying out pseudo-experiments."
		
	for i in range(pseudoNumber):
	
		totEvents = rPoisson.Poisson(mcExpect)
		dataHist.FillRandom(mcSumHist, totEvents)
		templateCfg.mvaCfg["datahisto"] = dataHist

		# Do the fit
		fitResults = templateFit(templateCfg)
		
		# Otherwise ROOT complains because of possible memory leak:
		fitResults["corrHist"].SetName("corr_hist_exp" + str(i))
		
		result = fitResults["fittedVars"]
		err = fitResults["varErrors"]
		corr = fitResults["corr"]
		minNLL = fitResults["minNLL"]
		chisq = fitResults["chisq"]
		nDoF = fitResults["nDoF"]
		
		weighteddsquare = 0.
		
		for proc in templateCfg.procCfg:
			if proc["signal"] == "1":
				procN = proc["name"]
				
				weighteddsquare += (result[procN]/err[procN])**2
				
				for proc2 in templateCfg.procCfg:
					if proc2["signal"] == "1":
						proc2N = proc2["name"]
						if procN == proc2N:
							histDict["corrList"][procN+"/"+proc2N] += err[procN]
						else:
							histDict["corrList"][procN+"/"+proc2N] += corr[procN+"/"+proc2N]
				
				histDict[procN].Fill(result[procN])
				histDict[procN+"_StdDev"].Fill(err[procN])
		
		histDict["weightedNorm"].Fill(math.sqrt(weighteddsquare))
		histDict["chisq"].Fill(chisq)
		histDict["minNLL"].Fill(minNLL)
		
		dataHist.SetName("data")

		dataHist.Reset()
	
	histDict["chisq"].SetTitle(histDict["chisq"].GetTitle() + " (" + str(nDoF) + " D.o.F.)")
	
	print "== Done."

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
		for proc2 in myConfig.procCfg:
			if proc2["name"] == proc:
				if proc2["signal"] == "1":
					varVec.append(proc)
				break

	for branch in myMCResult.branches:
		mean = ROOT.RooRealVar(branch[1] + "_events", \
			"Predicted number of events in branch " + branch[1], 0.)
		for proc in branch[2].keys():
			for proc2 in myConfig.procCfg:
				if proc2["name"] == proc:
					if proc2["signal"] == "1":
						mean.setVal(branch[2][proc]*params[proc] + mean.getVal())
					else:
						mean.setVal(branch[2][proc] + mean.getVal())
		branchMeans[ branch[1] ] = mean

		var = ROOT.RooRealVar(branch[1] + "_var", \
			"Variable for branch " + branch[1], 0, "GeV^-2")
		branchVars[ branch[1] ] = var

		pdf = ROOT.RooPoisson(branch[1] + "_pdf", \
			"Poisson PDF for branch " + branch[1], var, mean)
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
				if proc == proc2:
					histDict["corrList"][proc+"/"+proc2] += math.sqrt(var[proc]) 
				else:
					histDict["corrList"][proc+"/"+proc2] += \
						cov[proc+"/"+proc2]/math.sqrt(abs(var[proc]*var[proc2]))
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
