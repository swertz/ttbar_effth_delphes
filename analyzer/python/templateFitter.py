#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

#### Preamble

import sys
import ROOT

from utils import PConfig
from utils import PResult

######## FITTER MAIN #############################################################

def templateFitterMain(templateCfgFileName):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	
	# Load configuration (same structure as analysis configuration => re-use class)
	print "== Reading configuration file {0}".format(templateCfgFileName)
	templateCfg = PConfig(templateCfgFileName)
	outFile = ROOT.TFile(templateCfg.mvaCfg["outFile"], "RECREATE")

	# Fill histograms for different processes
	print "== Filling input histograms from trees."
	fillHistos(templateCfg)
	outFile.cd()

	# generate pseudo-experiment
	inputVar = templateCfg.mvaCfg["inputvar"]
	nBins = int(templateCfg.mvaCfg["nbins"])
	varMin = float(templateCfg.mvaCfg["varmin"])
	varMax = float(templateCfg.mvaCfg["varmax"])
	
	dataHist = ROOT.TH1D("MCdata_" + inputVar, "MCdata: " + inputVar, \
		nBins, varMin, varMax)
	mcSumHist = dataHist.Clone("MCsum_" + inputVar)
	for data in templateCfg.dataCfg:
		mcSumHist.Add(data["histo"])
	for i in range(nBins):
		mcExpect = mcSumHist.GetBinContent(i+1)
		mean = ROOT.RooRealVar("binMean", "Predicted number of events in a bin", \
			mcExpect)
		var = ROOT.RooRealVar("binVar", "Variable for number of events in a bin", \
			mcExpect)
		pdf = ROOT.RooPoisson("binPDF", "PDF for bin number", var, mean)
		dataSet = pdf.generate(ROOT.RooArgSet(var), 1)
		rds = dataSet.get(0)
		dataHist.SetBinContent(i+1, rds.find("binVar").getVal())

	# do the fit
	histVar = ROOT.RooRealVar("histVar", "Variable the histograms are built of.", \
		varMin, varMax)
	procVars = {}
	procRHists = {}
	procPDFs = {}
	for data in templateCfg.dataCfg:
		if data["signal"] == "1":
			procVars[ data["name"] ] = ROOT.RooRealVar(data["name"] + "_var", \
				"Variable for process " + data["name"], 0., -1., 1.)
			procRHists[ data["name"] ] = ROOT.RooDataHist(data["name"] + "_hist", \
				"Histogram for process " + data["name"], \
				ROOT.RooArgList(histVar), data["histo"])
			procPDFs[ data["name"] ] = ROOT.RooHistPdf(data["name"] + "_histPdf", \
				"Histogram PDF for process " + data["name"], \
				ROOT.RooArgSet(histVar), procRHists[ data["name"] ])
	dataRHist = ROOT.RooDataHist("data_hist","Histogram for data", \
		ROOT.RooArgList(histVar), data["histo"])
	
	varArgList = ROOT.RooArgList()
	for var in procVars.values():
		varArgList.add(var)

	PDFArgList = ROOT.RooArgList()
	for pdf in procPDFs.values():
		PDFArgList.add(pdf)

	myModel = ROOT.RooAddPdf("Template_model", "Template model", PDFArgList, varArgList)

	myModel.fitTo(dataRHist)

	for data in templateCfg.dataCfg:
		data["histo"].Write()
	dataHist.Write()
	mcSumHist.Write()
	outFile.Close()

######## FITTER MAIN #############################################################

def fillHistos(cfg):
	inputVar = cfg.mvaCfg["inputvar"]
	nBins = int(cfg.mvaCfg["nbins"])
	varMin = float(cfg.mvaCfg["varmin"])
	varMax = float(cfg.mvaCfg["varmax"])
	genWeight = cfg.mvaCfg["genweight"]

	for data in cfg.dataCfg:
		data["histo"] = ROOT.TH1D(data["name"] + "_" + inputVar, \
			data["name"] + ": " + inputVar, \
			nBins, varMin, varMax)
		dataFile = ROOT.TFile(data["path"])
		dataTree = dataFile.Get(data["treename"])
		nEntries = dataTree.GetEntriesFast()
		for event in dataTree:
			weight = dataTree.__getattr__(genWeight) * float(data["xsection"]) * \
				nEntries / float(data["genevents"])
			data["histo"].Fill(dataTree.__getattr__(inputVar), weight)
		dataFile.Close()

######## MAIN #############################################################

if __name__ == "__main__":
	argConf = 1
	argMC = 2
	argData = 3
	argMode = 4
	argOption = 5

	templateFitterMain(sys.argv[1])
