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

argDataConf = 1
argPlotConf = 2
argOut = 3
argChan = 4

#### PHist class contains a TH1D, information about the histogram, and a PDataSet
# It is initialized using a line of the PlotConf file, a PDataSet, and information about the normalization used

class PHist:
	
	def __init__(self, configLine, dataSet):
		self.Name = dataSet.Name + "/" + dataSet.Channel + " - " + configLine[0]
		self.Title = configLine[1]
		self.VarName = configLine[2]
		self.NBins = int(configLine[3])
		self.Start = float(configLine[4])
		self.End = float(configLine[5])
		self.DataSet = dataSet
		self.Hist =  TH1F(self.Name, self.Title, self.NBins, self.Start, self.End)

		self.Hist.SetLineColor(self.DataSet.Color)
		self.Hist.SetLineWidth(2)
		if self.DataSet.Signal == 1:
			self.Hist.SetLineWidth(3)
			self.Hist.SetLineStyle(2)
		self.Hist.SetStats(0)

	def Fill(self):

		inputFile = TFile(self.DataSet.Path, "READ")
		inputTree = inputFile.Get("Event")

		for event in inputTree:
			self.Hist.Fill(inputTree.__getattr__(self.VarName), inputTree.__getattr__("GenWeight"))
		
		self.Hist.Scale( 1./self.Hist.Integral() )

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

HistList = []

for configPlotLine in configTablePlots:
	myHistList = []
	for dataSet in DataSets:
		myHist = PHist(configPlotLine, dataSet)
		myHist.Fill()
		myHistList.append(myHist)
	HistList.append(myHistList)

#### Drawing the plots and saving the output:
# For each plot, a canvas, pad (necessary for setting log scales, for instance) and legend is defined, and the PHist is drawn.
# Everything is then saved to the output file.

outputFile = TFile(sys.argv[argOut], "RECREATE")

for myHistList in HistList:
	canvas = TCanvas(myHistList[0].Title,myHistList[0].Title, 600, 600)
	myPad = TPad(myHistList[0].Title,myHistList[0].Title,0.,0.,1.,1.,0)
	myPad.Draw()
	myPad.cd()
	myPad.SetGridy()

	leg = TLegend(.6,.75,.89,.89)
	
	for hist in sorted(myHistList,key = lambda hist: hist.Hist.GetMaximum(), reverse=True):
		hist.Hist.Draw("same")
		hist.Hist.GetXaxis().SetTitle(hist.Title)
	for hist in myHistList:
		leg.AddEntry(hist.Hist, hist.DataSet.Name + "/" + hist.DataSet.Channel, "f")
	leg.Draw()

	canvas.Write()

outputFile.Close()

