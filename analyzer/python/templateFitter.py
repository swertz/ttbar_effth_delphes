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
from utils import convertColor 

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
	
	dataHist = ROOT.TH1D("MCdata_" + inputVar, "MC data: " + inputVar, \
		nBins, varMin, varMax)
	mcSumHist = dataHist.Clone("MCsum_" + inputVar)
	mcSumHist.SetTitle("MC sum: " + inputVar)
	for data in templateCfg.dataCfg:
		if data["signal"] != "1":
			mcSumHist.Add(data["histo"])

	mcExpect = mcSumHist.Integral()
	rPoisson = ROOT.TRandom()
	nEvents = rPoisson.Poisson(mcExpect)
	dataHist.FillRandom(mcSumHist, nEvents)

	# do the fit

	histVar = ROOT.RooRealVar("histVar", "histVar", varMin, varMax)
	procVars = {}
	procRHists = {}
	procPDFs = {}
	
	for data in templateCfg.dataCfg:

		# for each signal, configure a variable and a PDF from the corresponding
		# histogram
	
		dataExpect = float( data["histo"].Integral() )
		if data["signal"] == "1":
			range = float( data["range"] )
			procVars[ data["name"] ] = ROOT.RooRealVar(data["name"] + "_var", \
				"Variable for process " + data["name"], \
				0., -range*dataExpect, range*dataExpect)
		else:
			procVars[ data["name"] ] = ROOT.RooRealVar(data["name"] + "_var", \
				"Variable for process " + data["name"], dataExpect) 
			
		procRHists[ data["name"] ] = ROOT.RooDataHist(data["name"] + "_hist", \
			"Histogram for process " + data["name"], \
			ROOT.RooArgList(histVar), data["histo"])
		
		procPDFs[ data["name"] ] = ROOT.RooHistPdf(data["name"] + "_histPdf", \
			"Histogram PDF for process " + data["name"], \
			ROOT.RooArgSet(histVar), procRHists[ data["name"] ])

	dataRHist = ROOT.RooDataHist("data_hist","Histogram for data", \
		ROOT.RooArgList(histVar), dataHist)
	
	varArgList = ROOT.RooArgList()
	PDFArgList = ROOT.RooArgList()
	for proc in procVars.keys():
		varArgList.add( procVars[proc] )
		PDFArgList.add( procPDFs[proc] )

	model = ROOT.RooAddPdf("Template_model", "Template model", PDFArgList, varArgList)

	model.fitTo(dataRHist, ROOT.RooFit.SumW2Error(ROOT.kTRUE), \
		ROOT.RooFit.NumCPU(1) )

	# Plot the fit results
	# The built-in RooFit functions can't be used since some of the "PDFs" may 
	# have negative values (RooFit can't stomach it).

	#frame = histVar.frame()
	#dataRHist.plotOn(frame)
	#model.plotOn(frame)
	#for data in templateCfg.dataCfg:
	#	model.plotOn(frame, ROOT.RooFit.Components(data["name"] + "_histPdf"), \
	#		ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor( convertColor(data["color"]) ) )
	#cnv = ROOT.TCanvas("Template_fit","Template fit")
	#cnv.cd()
	#frame.Write()

	for data in templateCfg.dataCfg:
		data["histo"].Write()
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
	templateFitterMain(sys.argv[1])
