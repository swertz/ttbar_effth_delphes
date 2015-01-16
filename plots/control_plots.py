#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
# usage: ./control_plots.py dataConfFile plotConfFile outFile(.root) channel

#### Preamble

from ROOT import *
import sys

gSystem.Load("libDelphes.so")

lumi = 100000. # pb-1
argDataConf = 1
argPlotConf = 2
argOut = 3
argChan = 4

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

#### PHist class contains a TH1D, information about the histogram, and a PDataSet
# It is initialized using a line of the PlotConf file, a PDataSet, and information about the normalization used

class PHist:
	
	def __init__(self, configLine, dataSet, norm=0):
		self.Name = dataSet.Name + "/" + dataSet.Channel + " - " + configLine[0]
		self.Title = dataSet.Name + "/" + dataSet.Channel + " - " + configLine[1]
		self.VarName = configLine[2]
		self.NBins = int(configLine[3])
		self.Start = float(configLine[4])
		self.End = float(configLine[5])
		self.DataSet = dataSet
		self.Norm = norm
		self.Hist =  TH1F(self.Name, self.Title, self.NBins, self.Start, self.End)

		if self.DataSet.Signal == 1:
			self.Hist.SetLineColor(self.DataSet.Color)
		else:
			self.Hist.SetFillColor(self.DataSet.Color)

	def Fill(self):

		inputFile = TFile(self.DataSet.Path, "READ")
		inputTree = inputFile.Get("Event")
		nEntries = inputTree.GetEntries()

		for event in inputTree:
			self.Hist.Fill(inputTree.__getattr__(self.VarName), inputTree.__getattr__("GenWeight"))
		
		if self.Hist.Integral() != 0:
			if self.Norm == 0:
				self.Hist.Scale( 1./self.Hist.Integral() )
			elif self.Norm > 0:
				self.Hist.Scale( self.Norm/self.Hist.Integral() )
			elif self.Norm == -1:
				self.Hist.Scale( lumi*self.DataSet.CS*self.DataSet.Eff/self.Hist.Integral() )

		inputFile.Close()

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
		PDataSet.DataSetCount += 1

#### Reading the DataConf file and initializing the PDataSets

configFileData = open(sys.argv[argDataConf], "r")
configList = configFileData.read().split("\n")
configFileData.close()
configTableData = [ line.split() for line in [ line for line in configList if line is not "" ] if line[0] is not "#" ]
del configList
print "Data:"
for configLine in configTableData:
	print str(configLine).translate(None, "'")

DataSets = []
for configDataLine in configTableData:
	if configDataLine[2] == sys.argv[argChan]:
		myDataSet = PDataSet(configDataLine)
		DataSets.append(myDataSet)

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

for configPlotLine in configTablePlots:

	myStack = PStack(configPlotLine)
	
	for dataSet in DataSets:	
		myHist = PHist(configPlotLine, dataSet, norm=-1)
		myHist.Fill()
		myStack.AddHisto(myHist)

	StackList.append(myStack)

#### Drawing the plots and saving the output:
# For each plot, a canvas, pad (necessary for setting log scales, for instance) and legend is defined, and the PStack is drawn.
# Everything is then saved to the output file.

outputFile = TFile(sys.argv[argOut], "RECREATE")

for myStack in StackList:

	canvas = TCanvas(myStack.Name,myStack.Title, 600, 600)
	myPad = TPad(myStack.Name,myStack.Title,0.,0.,1.,1.,0)
	myPad.Draw()
	myPad.cd()
	myPad.SetGridy()
	if myStack.SetLog.find("x") != -1:
		myPad.SetLogx()
	if myStack.SetLog.find("y") != -1:
		myPad.SetLogy()

	myStack.Stack.Draw()
	myStack.Stack.GetXaxis().SetTitle(myStack.Title)

	leg = TLegend(.7,.7,.89,.89)
	for hist in myStack.HistList:
		leg.AddEntry(hist.Hist, hist.DataSet.Name + "/" + hist.DataSet.Channel, "f")
	leg.Draw()

	canvas.Write()

outputFile.Close()

