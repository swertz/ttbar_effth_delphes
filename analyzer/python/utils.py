#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python2.7
# -*- coding: utf-8 -*-

# Author: Sebastien Wertz
#		  sebastien.wertz@uclouvain.be
# License: GPLv2
#!/usr/bin/python2.6

import copy
import sys

######## CLEAN BLANKS #############################################################
def cleanBlanks(item):
	""" Gets a string, and returns the string after having removed any blank spaces at the beginning
	or end of the string. Caution: in-place modification of the string! """
	if len(item) > 0:
		while item[0] == " ":
			item = item[1:]
			if len(item) == 0:
				break
	if len(item) > 0:
		while item[len(item)-1] == " ":
			item = item[:len(item)-1]
			if len(item) == 0:
				break
	return item


######## CLASS MC STUDY CONFIG #####################################################

class PMCConfig:

	def __init__(self, cfgFileName):

		self.cfg = {}
		self.params = []

		with open(cfgFileName, "r") as cfgFile:
			
			# splitting the lines, skipping empty lines and comment lines (starting with a "#")
			cfgContent = cfgFile.read()
			lines = [ line for line in cfgContent.split("\n") if line is not "" ]
			lines = [ line for line in lines if line[0] is not "#" ]
			# splitting between the ":"
			lines = [ line.split("=") for line in lines ]
			for line in lines:
				# removing blank spaces before and after the "="
				line = [ cleanBlanks(item) for item in line ]
				if line[0].find("param") >= 0:
						paramSet = {}
						paramList = line[1].split(";")
						for param in paramList:
							name = param.split(":")[0]
							name = cleanBlanks(name)
							value = param.split(":")[1]
							value = cleanBlanks(value)
							value = float(value)
							paramSet[name] = value
						self.params.append(paramSet)
				else:
					self.cfg[line[0]] = line[1]

######## CLASS PRESULT #############################################################

class PResult:

	def __init__(self):
		self.branches = []

	def iniFromFile(self, cfgFileName):

		with open(cfgFileName, "r") as cfgFile:
			# splitting the lines, skipping empty lines and comment lines (starting with a "#")
			cfgContent = cfgFile.read()
			lines = [ line for line in cfgContent.split("\n") if line is not "" ]
			lines = [ line for line in lines if line[0] is not "#" ]
			# splitting between the ":"
			self.branches = [ line.split(":") for line in lines ]
			for branch in self.branches:
				if len(self.branches) < 3:
					print "== Error in the result file syntax."
					sys.exit(1)
				# splitting the data entries to get name and expected number of events
				datae = branch[2].split(",")
				datae = [ data for data in datae if data != "" ]
				datae = [ data.split("=") for data in datae ]
				datae = [ (data[0], float(data[1])) for data in datae ]
				branch[2] = dict(datae)
	
	def iniFromRDS(self, mcResult, rdsRow):
		self.branches = copy.deepcopy(mcResult.branches)

		for branch in self.branches:
			branch[2] = {}
			branch[2]["data"] = rdsRow.find(branch[1] + "_var").getVal()

######## CLASS PCONFIG #####################################################

class PConfig:

	def __init__(self, cfgFileName):
		self.mvaCfg = {}
		self.dataCfg = []

		with open(cfgFileName, "r") as cfgFile:
			# splitting the file content into sections (starting with a "[")
			cfgSections = cfgFile.read().split("[")
			for section in cfgSections:

				# skipping comment lines (starting with a "#")
				if section[0] == "#":
					continue

				# section title goes up to "]"
				sectionTitle = section.split("]")[0]
				sectionContent = section.split("]")[1]

				if sectionTitle == "analysis":

					tempCfgTable = [ line for line in sectionContent.split("\n") ] # divide the lines
					tempCfgTable = [ line for line in tempCfgTable if line is not "" ] # avoid empty lines
					tempCfgTable = [ line for line in tempCfgTable if line[0] is not "#" ] # avoid lines starting with a '#'
					tempCfgTable = [ line.split("#")[0] for line in tempCfgTable ] # there could be a commen further along: keep only what's before the '#'
					tempCfgTable = [ line.split("=") for line in tempCfgTable ] # split the name of the entry and the entry itself
					cfgTable = []

					for line in tempCfgTable:
						# removing blank spaces before and after the "="
						tupleLine = [ cleanBlanks(item) for item in line ]
						cfgTable.append(tuple(tupleLine))

					self.mvaCfg = dict(cfgTable)
					# there has to be at least twice as many events left as the number of events asked for training
					#if int(self.mvaCfg["minmcevents"]) < 2*int(self.mvaCfg["trainentries"]):
					#	self.mvaCfg["minmcevents"] = str(2*int(self.mvaCfg["trainentries"]))

				elif sectionTitle.find("data_") >= 0:

					tempCfgTable = [ line for line in sectionContent.split("\n") ]
					tempCfgTable = [ line for line in tempCfgTable if line is not "" ]
					tempCfgTable = [ line for line in tempCfgTable if line[0] is not "#" ]
					tempCfgTable = [ line.split("#")[0] for line in tempCfgTable ]
					tempCfgTable = [ line.split("=") for line in tempCfgTable ]
					cfgTable = []

					for line in tempCfgTable:
						# removing blank spaces before and after the "="
						tupleLine = [ cleanBlanks(item) for item in line ]
						cfgTable.append(tuple(tupleLine))

					self.dataCfg.append(dict(cfgTable))

			if len(self.dataCfg) < 2:
				print "== Config file has not the proper syntax."
				sys.exit(1)

