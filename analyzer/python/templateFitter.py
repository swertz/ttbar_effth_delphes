#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#          sebastien.wertz@uclouvain.be
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
    outFile = TFile(templateCfg.mvaCfg["outfile"], "RECREATE")

    if templateCfg.mvaCfg["options"].find("fill") >= 0:
        # Fill histograms for different processes
        print "== Filling input histograms from trees."
        fillHistos(templateCfg, dataHist = True)
    
    elif templateCfg.mvaCfg["options"].find("get") >= 0:
        # Retrieve histograms from specified files
        print "== Getting input histograms from files."
        getHistos(templateCfg, dataHist = True)

    outFile.cd()

    fitResults = templateFit(templateCfg)

    fittedVars = fitResults["fittedVars"]
    varErrors = fitResults["varErrors"]
    corr = fitResults["corr"]
    minNLL = fitResults["minNLL"]
    chisq = fitResults["chisq"]
    nDoF = fitResults["nDoF"]
    corrHist = fitResults["corrHist"]

    # Print the fit result
    
    print "\n== Fit results:"
    for sig in fittedVars.keys():
        print "=== {0}: {1} = {2:.3f} +- {3:.3f}"\
            .format(sig, fittedVars[sig], varErrors[sig])
    
    print "\n== Correlations:"
    for i,sig in enumerate(fittedVars.keys()):
        for j,sig2 in enumerate(fittedVars.keys()):
            if j > i:
                print "=== {0}/{1}: {2:.2f}".format(sig, sig2, corr[sig + "/" + sig2])
    print ""
    
    plotTemplateFitResults(templateCfg, fittedVars, outFile)

    corrHist.Write()
    
    for proc in templateCfg.procCfg:
        proc["histo"].Write()
    templateCfg.mvaCfg["datahisto"].Write()
    
    outFile.Close()

######## TEMPLATE FIT ################################################################

def templateFit(templateCfg):
    
    inputVar = templateCfg.mvaCfg["inputvar"]
    nBins = templateCfg.mvaCfg["nbins"]
    varMin = templateCfg.mvaCfg["varmin"]
    varMax = templateCfg.mvaCfg["varmax"]
    dataHist = templateCfg.mvaCfg["datahisto"]

    # Configure the fit

    histVar = RooRealVar("histVar", "histVar", varMin, varMax)
    procVars = {}
    procRHists = {}
    procPDFs = {}
    sigYields = {}
    
    for name,proc in templateCfg.procCfg.items():

        # For each signal, configure a variable and a PDF from the corresponding
        # histogram.
   
        expect = float( proc["histo"].Integral() )
        if proc["signal"] == 1:
            valRange = proc["range"]
            procVars[name] = RooRealVar(name + "_var", \
                "Variable for process " + name, \
                float(valRange[1]+valRange[0])*abs(expect)/2., \
                float(valRange[0])*abs(expect), \
                float(valRange[1])*abs(expect))
            sigYields[name] = expect
        else:
            procVars[name] = RooRealVar(name + "_var", \
                "Variable for process " +name, expect) 
            
        procRHists[name] = RooDataHist(name + "_hist", \
            "Histogram for process " + name, \
            RooArgList(histVar), proc["histo"])
        
        procPDFs[name] = RooHistPdf(name + "_histPdf", \
            "Histogram PDF for process " + name, \
            RooArgSet(histVar), procRHists[name])

    dataRHist = RooDataHist("data_hist","Histogram for data", \
        RooArgList(histVar), dataHist)
    
    varArgList = RooArgList()
    PDFArgList = RooArgList()
    for proc in procVars.keys():
        varArgList.add( procVars[proc] )
        PDFArgList.add( procPDFs[proc] )

    model = RooAddPdf("Template_model", "Template model", PDFArgList, varArgList)

    verbosity = -1
    RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)
    if templateCfg.mvaCfg["options"].find("verbose") >= 0:
        verbosity = 1
        RooMsgService.instance().setGlobalKillBelow(RooFit.DEBUG)

    # Do the fit

    fitResult = model.fitTo(dataRHist,
        #RooFit.SumW2Error(kTRUE),
        RooFit.Extended(kTRUE),
        RooFit.NumCPU(templateCfg.mvaCfg["numcpu"], 1),
        RooFit.Save(kTRUE),
        RooFit.PrintLevel(verbosity)
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
    
    for sig in sigYields.keys():
        
        fittedEvtNum[sig] = resultArgList.find(sig + "_var").getVal()
        evtNumErrors[sig] = procVars[sig].getError()

        fittedVars[sig] = fittedEvtNum[sig] / sigYields[sig]
        varErrors[sig] = evtNumErrors[sig] / sigYields[sig]

        for sig2 in sigYields.keys():
            corr[sig + "/" + sig2] = fitResult.correlation(sig + "_var", sig2 + "_var")

    # Compute Chi-Square of the fit (which might not be Chi-Square-distributed)

    chisq = 0.
    nDoF = 0
    for i in range(dataHist.GetNbinsX()):
        temp = 0.
        
        for name,proc in templateCfg.procCfg.items():
            if proc["signal"] == 1:
                temp += fittedVars[name] * \
                        proc["histo"].GetBinContent(i+1)
            else:
                temp += proc["histo"].GetBinContent(i+1)

        if dataHist.GetBinContent(i+1) != 0:
            temp -= dataHist.GetBinContent(i+1)
            temp /= dataHist.GetBinError(i+1)
            chisq += temp**2
            nDoF += 1

    nDoF -= len(fittedVars)

    fitResults = {}

    fitResults["fittedVars"] = fittedVars
    fitResults["fittedEvtNum"] = fittedEvtNum
    fitResults["varErrors"] = varErrors
    fitResults["evtNumErrors"] = evtNumErrors
    fitResults["corr"] = corr
    fitResults["minNLL"] = minNLL
    fitResults["chisq"] = chisq
    fitResults["nDoF"] = nDoF
    fitResults["corrHist"] = corrHist
    
    return fitResults

######## WRITE PLOTS FOR FIT RESULTS ####################################################

def plotTemplateFitResults(cfg, fittedVars, dir=None):
    # Plot the fit results and write them
    # The built-in RooFit functions can't be used since some of the "PDFs" may 
    # have negative values (RooFit can't stomach it).

    cnv = TCanvas("fit_canvas", "Maximum Likelihood fit on " + cfg.mvaCfg["inputvar"] + ": result")

    pad = TPad()
    pad.SetTitle(cnv.GetTitle())
    
    legend = TLegend(0.6,0.6,0.89,0.89)
    legend.SetFillColor(0)

    dataHist = cfg.mvaCfg["datahisto"].Clone("temp_data_hist")
    dataHist.SetTitle(cnv.GetTitle())
    dataHist.SetLineWidth(2)
    dataHist.SetMarkerStyle(8)
    dataHist.SetStats(kFALSE)
    # dataHist will define the frame axis ranges
    dataHist.Draw("same,E0,P")
    legend.AddEntry(dataHist, "Data", "lep")

    fitSumHist = dataHist.Clone()
    fitSumHist.Reset()
    fitSumHist.SetLineColor(kRed)
    fitSumHist.SetLineWidth(2)

    plottedHists = []
    minY = 0.
    maxY = 0.

    for proc in cfg.procCfg:
        temp = proc["histo"].Clone("temp_hist")
        
        if proc["signal"] == 1:
            temp.Scale(fittedVars[ proc["name"] ])
            legend.AddEntry(temp, "Fitted " + proc["name"], "l")
            temp.SetLineStyle(2)
        else:
            legend.AddEntry(temp, "Bkg.: " + proc["name"], "l")
            temp.SetLineStyle(3)
        
        temp.SetLineColor(convertColor(proc["color"]))
        temp.SetLineWidth(2)
        temp.SetStats(kFALSE)
        temp.Draw("same,hist,][")
        
        if temp.GetMinimum() < minY:
            minY = temp.GetMinimum()
        if temp.GetMaximum() > maxY:
            maxY = temp.GetMaximum()

        fitSumHist.Add(temp)
        plottedHists.append(temp)
    
    fitSumHist.Draw("same,hist,][")
    legend.AddEntry(fitSumHist, "Fitted combination", "l")

    # Redraw dataHist to have the data points on top; correct the Y axis range
    # and set axis titles.
    
    dataHist.SetAxisRange(1.1*minY, 1.1*maxY, "Y")
    
    xTitle = cfg.mvaCfg["inputvar"]
    if "inputvarunit" in cfg.mvaCfg.keys():
        xTitle += " (" + cfg.mvaCfg["inputvarunit"] + ")"
    dataHist.SetXTitle(xTitle)
    
    yTitle = "Events/" + str(dataHist.GetBinWidth(1))
    if "inputvarunit" in cfg.mvaCfg.keys():
        yTitle += " " + cfg.mvaCfg["inputvarunit"]
    dataHist.SetYTitle(yTitle)
    
    dataHist.Draw("same,E0,P")
    
    legend.Draw("same")
    
    if dir is not None:
        dir.cd()
    cnv.Write()

######## FILL HISTOGRAMS #############################################################

def fillHistos(cfg, dataHist = False):
    inputVar = cfg.mvaCfg["inputvar"]
    nBins = cfg.mvaCfg["nbins"]
    varMin = cfg.mvaCfg["varmin"]
    varMax = cfg.mvaCfg["varmax"]
    lumi = cfg.mvaCfg["lumi"]

    for proc in cfg.procCfg:
        
        hist = TH1D(proc["name"] + "_" + inputVar, \
            proc["name"] + ": " + inputVar, \
            nBins, varMin, varMax)
        hist.Sumw2()
        
        file = TFile(proc["path"])
        tree = file.Get(proc["treename"])
        evtWeightsString = proc["evtweight"]
        evtWeights = [ weight for weight in evtWeightsString.split("*") if weight != "" ]

        for event in tree:
            weight = lumi * float(proc["xsection"]) / float(proc["genevents"])
            for wgt in evtWeights:
                weight *= tree.__getattr__(wgt)
            hist.Fill(tree.__getattr__(inputVar), weight)

        proc["histo"] = hist

        file.Close()
    
    if dataHist:
        hist = TH1D("data_" + inputVar, \
            "data: " + inputVar, nBins, varMin, varMax)

        file = TFile(cfg.mvaCfg["datafile"])

        tree = file.Get(cfg.mvaCfg["datatreename"])
        nEntries = tree.GetEntriesFast()

        for event in tree:
            hist.Fill(tree.__getattr__(inputVar))

        cfg.mvaCfg["datahisto"] = hist

        file.Close()        

######## GET HISTOGRAMS #############################################################

def getHistos(cfg, dataHist = False):
    file = 0 
    
    if "histfile" in cfg.mvaCfg.keys():
        file = TFile(cfg.mvaCfg["histfile"], "READ")

    for name,proc in cfg.procCfg.items():
        if "histfile" not in cfg.mvaCfg.keys():
            file = TFile(proc["histfile"], "READ")

        proc["histo"] = file.Get(proc["histname"])
        # Necessary so that the histogram persists in memory after the file is closed
        proc["histo"].SetDirectory(0)

        if "histfile" not in cfg.mvaCfg.keys():
            file.Close()
    
    if file.IsOpen():
        file.Close()

    cfg.mvaCfg["nbins"] = cfg.procCfg.values()[0]["histo"].GetNbinsX()
    cfg.mvaCfg["varmin"] = cfg.procCfg.values()[0]["histo"].GetXaxis().GetXmin()
    cfg.mvaCfg["varmax"] = cfg.procCfg.values()[0]["histo"].GetXaxis().GetXmax()

    if dataHist:
        file = TFile(cfg.mvaCfg["datafile"])
        cfg.mvaCfg["datahisto"] = dataFile.Get(cfg.mvaCfg["datahistname"])
        cfg.mvaCfg["datahisto"].SetDirectory(0)
        file.Close()

######## MAIN #############################################################

if __name__ == "__main__":
    templateFitterMain(sys.argv[1])
