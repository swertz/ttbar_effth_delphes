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
	for proc in templateCfg.dataCfg:
		if proc["signal"] != "1":
			mcSumHist.Add(proc["histo"])

	mcExpect = mcSumHist.Integral()
	rPoisson = ROOT.TRandom()
	totEvents = rPoisson.Poisson(mcExpect)
	dataHist.FillRandom(mcSumHist, totEvents)

	# do the fit

	histVar = ROOT.RooRealVar("histVar", "histVar", varMin, varMax)
	procVars = {}
	procRHists = {}
	procPDFs = {}
	
	for proc in templateCfg.dataCfg:

		# for each signal, configure a variable and a PDF from the corresponding
		# histogram
	
		expect = float( proc["histo"].Integral() )
		if proc["signal"] == "1":
			range = float( proc["range"] )
			procVars[ proc["name"] ] = ROOT.RooRealVar(proc["name"] + "_var", \
				"Variable for process " + proc["name"], \
				0., -range*expect, range*expect)
		else:
			procVars[ proc["name"] ] = ROOT.RooRealVar(proc["name"] + "_var", \
				"Variable for process " + proc["name"], expect) 
			
		procRHists[ proc["name"] ] = ROOT.RooDataHist(proc["name"] + "_hist", \
			"Histogram for process " + proc["name"], \
			ROOT.RooArgList(histVar), proc["histo"])
		
		procPDFs[ proc["name"] ] = ROOT.RooHistPdf(proc["name"] + "_histPdf", \
			"Histogram PDF for process " + proc["name"], \
			ROOT.RooArgSet(histVar), procRHists[ proc["name"] ])

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

	for proc in cfg.dataCfg:
		proc["histo"] = ROOT.TH1D(proc["name"] + "_" + inputVar, \
			proc["name"] + ": " + inputVar, \
			nBins, varMin, varMax)
		dataFile = ROOT.TFile(proc["path"])
		dataTree = dataFile.Get(proc["treename"])
		nEntries = dataTree.GetEntriesFast()
		for event in dataTree:
			weight = dataTree.__getattr__(genWeight) * float(proc["xsection"]) * \
				nEntries / float(proc["genevents"])
			proc["histo"].Fill(dataTree.__getattr__(inputVar), weight)
		dataFile.Close()

######## MAIN #############################################################

if __name__ == "__main__":
	templateFitterMain(sys.argv[1])
