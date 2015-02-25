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
import copy

from utils import PConfig
from utils import PResult

######## FITTER MAIN #############################################################

def lstSqCountingFitterMain(cfgFile, resultFile, dataFile, mode, option):
	print "============================================="
	print "================= MISchief =================="
	print "============================================="
	print "== Reading configuration file {0}".format(cfgFile)
	myConfig = PConfig(cfgFile)	
	print "== Reading MVA MC tree result file {0}".format(resultFile)
	myMCResult = PResult()
	myMCResult.iniFromFile(resultFile)
	print "== Reading MVA data tree result file {0}".format(dataFile)
	myDataResult = PResult()
	myDataResult.iniFromFile(dataFile)

	if len(myDataResult.branches) is not len(myMCResult.branches):
		print "== MC tree and data tree don't have the same number of branches."
		sys.exit(1)

	if mode == "lstSqCounting":
		print "== Performing a least-square fit on the branch yields."
		result,res,nDoF = lstSqCountingFit(myConfig, myMCResult, myDataResult, option)
		print "== Fit results are:" 
		for name,val in result.items():
			print "=== {0}: {1:.2f}".format(name, val)
		print "=== With chi-sq./NDoF = {0:.2f}/{1}".format(res, nDoF)

	elif mode == "weightedLstSqCounting":
		print "== Performing a weighted least-square fit on the branch yields."
		result,res,nDoF,var,cov = weightedLstSqCountingFit(myConfig, myMCResult, myDataResult, option)
		print "== Fit results are:" 
		for name,val in result.items():
			print "=== {0}: {1:.2f} +- {2:.2f}".format(name, val, var[name])
		print "=== With chi-sq./NDoF = {0:.2f}/{1}".format(res, nDoF)
		print "=== Covariance matrix:"
		for name,val in cov.items():
			print "=== {0}: {1:.2f}".format(name, cov[name])
	
	else:
		print "== Fit mode not correctly specified!"
		sys.exit(1)

######## WEIGHTED LEAST SQUARE COUNTING FIT ################################################

def weightedLstSqCountingFit(myConfig, myMCResult, myDataResult, mode="fixBkg"):

	x = []
	res = 0
	varVec = []
	nBr = len(myMCResult.branches)
	nVar = 0

	y = []
	A = []
	# Vector containing the prediction for the backgrounds for each branch;
	# has to be subtracted from the observed number of events!
	b = []

	allVarVec = myMCResult.branches[0][2].keys()
	if mode == "fixBkg":
		for proc in allVarVec:
			for proc2 in myConfig.procCfg:
				if proc2["name"] == proc:
					if proc2["signal"] == "1":
						varVec.append(proc)
					break
	else:
		varVec = allVarVec
	for branch in myDataResult.branches:
		y.append(branch[2]["data"])
	for branch in myMCResult.branches: 
		b_i = 0
		for proc in allVarVec:
			for proc2 in myConfig.procCfg:
				if proc2["name"] == proc:
					if proc2["signal"] != "1":
						b_i += branch[2][proc]
					break
		b.append(b_i)
		row = []
		for proc in varVec:
			row.append(branch[2][proc])
		A.append(row)
	yw = 0
	if mode == "fixBkg":
		yw = np.array(y) - np.array(b)
	else:
		yw = np.array(y)
	Aw = np.array(A)
	W = np.eye(nBr)
	for i in range(nBr):
		W[i][i] = 1./y[i]

	AwT = Aw.transpose()
	Atemp = np.linalg.inv(np.dot(np.dot(AwT,W), Aw))
	Atemp2 = np.dot(Atemp,np.dot(AwT,W))
	x = np.dot(Atemp2, yw)
	res = 0.
	resVec = yw - np.dot(Aw,x)
	for i in range(nBr):
		res += W[i][i] * (resVec[i]**2)
	
	nDoF = nBr - len(varVec)
	result = {}
	var = {}
	cov = {}
	for i,proc in enumerate(varVec):
		result[proc] = x[i]
		var[proc] = Atemp[i][i]
		for j,proc2 in enumerate(varVec):
			cov[proc+"/"+proc2] = Atemp[i][j]

	return result,res,nDoF,var,cov
	
###### LEAST SQUARE COUNTING FIT #########################################################
#(best not use this one! no weights used for uncertainties) 

def lstSqCountingFit(myConfig, myMCResult, myDataResult, mode="fixBkg"):

	x = []
	res = 0
	varVec = []
	nBr = len(myMCResult.branches)

	y = []
	A = []
	# vector containing the prediction for the backgrounds for each branch
	# has to be subtracted from the observed number of events!
	b = []

	allVarVec = myMCResult.branches[0][2].keys()
	if mode == "fixBkg":
		for proc in allVarVec:
			for proc2 in myConfig.procCfg:
				if proc2["name"] == proc:
					if proc2["signal"] == "1":
						varVec.append(proc)
					break
	else:
		varVec = allVarVec
	for branch in myDataResult.branches:
		y.append(branch[2]["data"])
	for branch in myMCResult.branches: 
		b_i = 0
		for proc in allVarVec:
			for proc2 in myConfig.procCfg:
				if proc2["name"] == proc:
					if proc2["signal"] != "1":
						b_i += branch[2][proc]
					break
		b.append(b_i)
		row = []
		for proc in varVec:
			row.append(branch[2][proc])
		A.append(row)
	yw = 0
	if mode == "fixBkg":
		yw = np.array(y) - np.array(b)
	else:
		yw = np.array(y)
	Aw = np.array(A)

	x,res = np.linalg.lstsq(Aw, yw)[0:2]
	
	nDoF = nBr - len(varVec)
	result = {}
	for i,proc in enumerate(varVec):
		result[proc] = x[i]

	return result,float(res),nDoF
	
######## MAIN #############################################################

if __name__ == "__main__":
	argConf = 1
	argMC = 2
	argData = 3
	argMode = 4
	argOption = 5

	lstSqCountingFitterMain(sys.argv[argConf], sys.argv[argMC], sys.argv[argData], sys.argv[argMode], sys.argv[argOption])
