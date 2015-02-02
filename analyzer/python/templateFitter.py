#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

import sys
from ROOT import *

from utils import PConfig
from utils import convertColor
from math import sqrt

######## FITTER MAIN #############################################################

def templateFitterMain(templateCfgFileName):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	
	# Load configuration (same structure as analysis configuration => re-use class)

	print "== Reading configuration file {0}".format(templateCfgFileName)
	templateCfg = PConfig(templateCfgFileName)
	outFile = TFile(templateCfg.mvaCfg["outFile"], "RECREATE")

	# Fill histograms for different processes
	
	print "== Filling input histograms from trees."
	fillHistos(templateCfg)
	outFile.cd()

	# Generate pseudo-experiment
	
	inputVar = templateCfg.mvaCfg["inputvar"]
	nBins = int(templateCfg.mvaCfg["nbins"])
	varMin = float(templateCfg.mvaCfg["varmin"])
	varMax = float(templateCfg.mvaCfg["varmax"])
	
	dataHist = TH1D("MCdata_" + inputVar, "MC data: " + inputVar, \
		nBins, varMin, varMax)
	mcSumHist = dataHist.Clone("MCsum_" + inputVar)
	mcSumHist.SetTitle("MC sum: " + inputVar)
	for proc in templateCfg.dataCfg:
		if proc["signal"] != "1":
			mcSumHist.Add(proc["histo"])

	mcExpect = mcSumHist.Integral()
	rPoisson = TRandom(0)
	totEvents = rPoisson.Poisson(mcExpect)
	dataHist.FillRandom(mcSumHist, totEvents)

	# Configure the fit

	histVar = RooRealVar("histVar", "histVar", varMin, varMax)
	procVars = {}
	procRHists = {}
	procPDFs = {}
	sigYields = {}
	
	for proc in templateCfg.dataCfg:

		# For each signal, configure a variable and a PDF from the corresponding
		# histogram.
	
		expect = float( proc["histo"].Integral() )
		if proc["signal"] == "1":
			range = float( proc["range"] )
			procVars[ proc["name"] ] = RooRealVar(proc["name"] + "_var", \
				"Variable for process " + proc["name"], \
				0., -range*expect, range*expect)
			sigYields[ proc["name"] ] = expect
		else:
			procVars[ proc["name"] ] = RooRealVar(proc["name"] + "_var", \
				"Variable for process " + proc["name"], expect) 
			
		procRHists[ proc["name"] ] = RooDataHist(proc["name"] + "_hist", \
			"Histogram for process " + proc["name"], \
			RooArgList(histVar), proc["histo"])
		
		procPDFs[ proc["name"] ] = RooHistPdf(proc["name"] + "_histPdf", \
			"Histogram PDF for process " + proc["name"], \
			RooArgSet(histVar), procRHists[ proc["name"] ])

	dataRHist = RooDataHist("data_hist","Histogram for data", \
		RooArgList(histVar), dataHist)
	
	varArgList = RooArgList()
	PDFArgList = RooArgList()
	varIndexes = {}
	i = 0
	for proc in procVars.keys():
		varArgList.add( procVars[proc] )
		PDFArgList.add( procPDFs[proc] )
		if sigYields.keys().__contains__(proc):
			varIndexes[proc] = i
			i += 1

	model = RooAddPdf("Template_model", "Template model", PDFArgList, varArgList)

	# Do the fit

	fitResult = model.fitTo(dataRHist, \
		RooFit.SumW2Error(kTRUE), \
		RooFit.NumCPU(int(templateCfg.mvaCfg["numcpu"]), 1), \
		RooFit.Save(kTRUE)\
		)
	fitResult.SetName("fitResult")

	# Retrieve fit results

	fittedEvtNum = {}
	fittedVars = {}
	corr = {}
	evtNumErrors = {}
	varErrors = {}

	resultArgList = fitResult.floatParsFinal()
	corrHist = fitResult.correlationHist()
	minNLL = fitResult.minNll()
	cov = fitResult.covarianceMatrix()
	
	for sig in sigYields.keys():
		
		fittedEvtNum[sig] = resultArgList.find(sig + "_var").getVal()
		evtNumErrors[sig] = sqrt( cov[ varIndexes[sig] ][ varIndexes[sig] ] )

		fittedVars[sig] = fittedEvtNum[sig] / sigYields[sig]
		varErrors[sig] = evtNumErrors[sig] / sigYields[sig]

		for sig2 in sigYields.keys():
			corr[sig + "/" + sig2] = fitResult.correlation(sig + "_var", sig2 + "_var")

	# Print the fit result
	
	print "\n== Fit results:"
	for sig in sigYields.keys():
		print "=== {0}: {1:.2f} +- {2:.2f} events =====> {3} = {4:.3f} +- {5:.3f}"\
			.format(sig, fittedEvtNum[sig], evtNumErrors[sig], 
			sig, fittedVars[sig], varErrors[sig])
	
	print "\n== Correlations:"
	for i,sig in enumerate(sigYields.keys()):
		for j,sig2 in enumerate(sigYields.keys()):
			if j > i:
				print "=== {0}/{1}: {2:.2f}".format(sig, sig2, corr[sig + "/" + sig2])
	print ""
	
	# Plot the fit results
	# The built-in RooFit functions can't be used since some of the "PDFs" may 
	# have negative values (RooFit can't stomach it).

	#frame = histVar.frame()
	#dataRHist.plotOn(frame)
	#model.plotOn(frame)
	#for data in templateCfg.dataCfg:
	#	model.plotOn(frame, RooFit.Components(data["name"] + "_histPdf"), \
	#		RooFit.LineStyle(kDashed), RooFit.LineColor( convertColor(data["color"]) ) )
	#cnv = TCanvas("Template_fit","Template fit")
	#cnv.cd()
	#frame.Write()

	corrHist.Write()

	for proc in templateCfg.dataCfg:
		proc["histo"].Write()
	dataHist.Write()
	mcSumHist.Write()
	
	outFile.Close()

######## FILL HISTOGRAMS #############################################################

def fillHistos(cfg):
	inputVar = cfg.mvaCfg["inputvar"]
	nBins = int(cfg.mvaCfg["nbins"])
	varMin = float(cfg.mvaCfg["varmin"])
	varMax = float(cfg.mvaCfg["varmax"])
	genWeight = cfg.mvaCfg["genweight"]
	lumi = float(cfg.mvaCfg["lumi"])

	for proc in cfg.dataCfg:
		
		proc["histo"] = TH1D(proc["name"] + "_" + inputVar, \
			proc["name"] + ": " + inputVar, \
			nBins, varMin, varMax)
		
		dataFile = TFile(proc["path"])
		dataTree = dataFile.Get(proc["treename"])
		nEntries = dataTree.GetEntriesFast()

		for event in dataTree:
			
			weight = dataTree.__getattr__(genWeight) * lumi * float(proc["xsection"]) / float(proc["genevents"])
			proc["histo"].Fill(dataTree.__getattr__(inputVar), weight)
		
		dataFile.Close()

######## MAIN #############################################################

if __name__ == "__main__":
	templateFitterMain(sys.argv[1])
