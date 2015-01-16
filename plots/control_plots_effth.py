#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
# usage: ./control_plots.py dataBGConfFile dataSigConfFile plotConfFile outFile(.root) channel legSig

#### Preamble

from ROOT import *
import sys

gSystem.Load("libDelphes.so")

lumi = 100000. # pb-1
argDataBGConf = 1
argDataSigConf = 2
argPlotConf = 3
argOut = 4
argChan = 5
argLegSig = 6

#### The PStack class contains a THStack, a list of PHist's and some information about the plot being produced
# It is initialized using a line of the PlotConf file

class PStack:

	StackCount = 0

	def __init__(self, configLine):
		self.Name = configLine[0]
		self.Title = configLine[1]
		self.VarName = configLine[2]
		self.NBins = configLine[3]
		self.Start = configLine[4]
		self.End = configLine[5]
		self.SetLog = configLine[6] # x, y or xy will set the mentioned axes to log-scale
		self.HistList = []
		self.Stack = THStack(self.Name, self.Title)
		PStack.StackCount+=1

	def AddHisto(self, hist):
		self.HistList.append(hist)
		self.Stack.Add(hist.Hist)

#### PHist class contains a TH1D, information about the histogram, and a list of PDataSets
# It is initialized using a line of the PlotConf file, a PDataSet, and information about the normalization used

class PHist:
	
	def __init__(self, configLine, dataSet, norm=0):
		self.Name = dataSet.Name + "/" + dataSet.Channel + " - " + configLine[0]
		self.Title = dataSet.Name + "/" + dataSet.Channel + " - " + configLine[1]
		self.VarName = configLine[2]
		self.NBins = int(configLine[3])
		self.Start = float(configLine[4])
		self.End = float(configLine[5])
		self.DataSet = [dataSet]
		self.Norm = norm
		self.Hist =  TH1F(self.Name, self.Title, self.NBins, self.Start, self.End)
		self.Hist.SetStats(0)

		if self.DataSet[0].Signal == 1:
			self.Hist.SetLineColor(self.DataSet[0].Color)
			self.Hist.SetLineWidth(2)
		else:
			self.Hist.SetFillColor(self.DataSet[0].Color)

	def AddDataSet(self, dataSet):
		self.DataSet.append(dataSet)

	def Fill(self):
	
		totNorm = 0.

		for dataSet in self.DataSet:

			inputFile = TFile(dataSet.Path, "READ")
			inputTree = inputFile.Get("Event")
			nEntries = inputTree.GetEntries()

			for event in inputTree:
				if self.Norm == -1:
					self.Hist.Fill(inputTree.__getattr__(self.VarName), lumi*dataSet.CS*inputTree.__getattr__("GenWeight")/dataSet.Nevt)
				else:
					self.Hist.Fill(inputTree.__getattr__(self.VarName), inputTree.__getattr__("GenWeight"))

			inputFile.Close()
			
		if self.Hist.Integral() != 0:
			if self.Norm == 0:
				self.Hist.Scale( 1./self.Hist.Integral() )
			elif self.Norm > 0:
				self.Hist.Scale( self.Norm/self.Hist.Integral() )

#### Contains info about the data set used to fill a PHist

class PDataSet:

	DataSetCount = 0

	def __init__(self, configLine):
		self.Path = configLine[0]
		self.Name = configLine[1]
		self.Channel = configLine[2]
		self.Entry = int(configLine[3])
		self.CS = float(configLine[4])
		self.Eff = float(configLine[5])
		self.Signal = int(configLine[6]) # 0=background / 1=signal 
		self.Color = int(configLine[7])
		self.Nevt = int(configLine[8])
		PDataSet.DataSetCount += 1

#### Reading the DataBGConf file and initializing the background PDataSets

configFileData = open(sys.argv[argDataBGConf], "r")
configList = configFileData.read().split("\n")
configFileData.close()
configTableData = [ line.split() for line in [ line for line in configList if line is not "" ] if line[0] is not "#" ]
configTableData = [ line for line in configTableData if (line[6] is not "1" and line[2] == sys.argv[argChan])] # keeping only the background, in the right channel
configTableData.sort(key=lambda line: float(line[4])*float(line[5])) # sorting: rarest processes first (clearer in log scale)
del configList
print "Data - Background:"
for configLine in configTableData:
	print str(configLine).translate(None, "'")

DataSets = []
for configDataLine in configTableData:
	myDataSet = PDataSet(configDataLine)
	DataSets.append(myDataSet)

#### Reading the DataSigConf file and initializing the signal PDataSets

configFileData = open(sys.argv[argDataSigConf], "r")
configList = configFileData.read().split("\n")
configFileData.close()
configTableDataSig = [ line.split() for line in [ line for line in configList if line is not "" ] if line[0] is not "#" ]
configParamSig = [ float(val) for val in configTableDataSig[0] ]
configTableDataSig = [ line for line in configTableDataSig[1:] if line[2] == sys.argv[argChan]] # keeping only the right channel
del configList
print "Data - Signal:"
print str(configParamSig).translate(None, "'")
for configLine in configTableDataSig:
	print str(configLine).translate(None, "'")

DataSetsSig = []
for i,configDataLine in enumerate(configTableDataSig):
	myDataSet = PDataSet(configDataLine)
	myDataSet.CS = myDataSet.CS * configParamSig[i+1] / (configParamSig[0]**2) # CS = CS*c_i/Lambda^2
	DataSetsSig.append(myDataSet)

#### Reading the PlotConf file and defining a table containing all the information

configFilePlots = open(sys.argv[argPlotConf], "r")
configListPlots = configFilePlots.read().split("\n")
configFilePlots.close()
configTablePlots = [ line.split(",") for line in [ line for line in configListPlots if line is not "" ] if line[0] is not "#" ] 
print "Plots:"
for configLine in configTablePlots:
	print str(configLine).translate(None, "'")
del configListPlots

#### Defining lists containing PStacks (one list for the backgrounds, and one for the eff-th-signal)
# For each PStack (one per plot), the data sets are looped over: for each PDataSet, a PHist is defined,
# filled and added to the PStack.

StackList = []
HistSigList = []

for configPlotLine in configTablePlots:

	myStack = PStack(configPlotLine)
	
	for dataSet in DataSets:
		myHist = PHist(configPlotLine, dataSet, norm=-1)
		myHist.Fill()
		myStack.AddHisto(myHist)
	
	StackList.append(myStack)

	myHistSigList = []

	if sys.argv[argLegSig] == "0":
		for dataSet in DataSetsSig:
			myHistSig = PHist(configPlotLine, dataSet, norm=-1)
			myHistSig.Fill()
			for bkgHist in myStack.HistList:
				myHistSig.Hist.Add(bkgHist.Hist)
			myHistSigList.append(myHistSig)
	else:
		myHistSig = PHist(configPlotLine, DataSetsSig[0], norm=-1)
		for dataSet in DataSetsSig[1:]:
			myHistSig.AddDataSet(dataSet)
		myHistSig.Fill()
		for bkgHist in myStack.HistList:
			myHistSig.Hist.Add(bkgHist.Hist)
		myHistSigList.append(myHistSig)
		
	HistSigList.append(myHistSigList)

#### Drawing the plots and saving the output:
# For each plot, a canvas, pad (necessary for setting log scales, for instance) and legend is defined, and the PStack is drawn.
# Everything is then saved to the output file.

outputFile = TFile(sys.argv[argOut], "RECREATE")

for i,myStack in enumerate(StackList):

	myHistSigList = HistSigList[i]

	canvas = TCanvas(myStack.Name,myStack.Title, 600, 600)
	myPad = TPad(myStack.Name,myStack.Title,0.,0.,1.,1.,0)
	myPad.Draw()
	myPad.cd()
	myPad.SetGridy()
	if myStack.SetLog.find("x") != -1:
		myPad.SetLogx()
	if myStack.SetLog.find("y") != -1:
		myPad.SetLogy()

	myHistSigList.sort(key=lambda hist: hist.Hist.GetMaximum(), reverse=True)

	if myStack.Stack.GetMaximum() > myHistSigList[0].Hist.GetMaximum():
		myStack.Stack.Draw()
		for hist in myHistSigList:
			hist.Hist.Draw("same")
	else:
		for hist in myHistSigList:
			hist.Hist.Draw("same")
		myStack.Stack.Draw("same")
		for hist in myHistSigList:
			hist.Hist.Draw("same")
	myStack.Stack.GetXaxis().SetTitle(myStack.Title)
	myHistSigList[0].Hist.GetXaxis().SetTitle(myStack.Title)

	leg = TLegend(.6,.75,.89,.89)
	for hist in myStack.HistList:
		if hist.DataSet[0].Signal is not 1:
			leg.AddEntry(hist.Hist, hist.DataSet[0].Name + "/" + hist.DataSet[0].Channel, "f")
	if sys.argv[argLegSig] == "0":
		for hist in myHistSigList:
			leg.AddEntry(hist.Hist, hist.DataSet[0].Name + "/" + hist.DataSet[0].Channel, "f")
	else:
		leg.AddEntry(myHistSigList[0].Hist, sys.argv[argLegSig], "f")
	leg.Draw()

	canvas.Write()

outputFile.Close()

