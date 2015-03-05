#include <string>
#include <sstream>
#include <iostream>
#include <map>
#include <cstdlib>
#include "TObjArray.h"
#include "TObjString.h"

#include "pconfig.h"

#define SSTR( x ) dynamic_cast< std::ostringstream & > \
        ( std::ostringstream() << std::dec << x ).str()

using namespace std;

PConfig::PConfig(TString configFile){
	ConfigFile cfg(configFile.Data());

	anaName = (string)cfg.Value("analysis","name");
	outputDir = (string)cfg.Value("analysis","outputdir");
	outputName = (string)cfg.Value("analysis","outputname");
	mvaMethod = (string)cfg.Value("analysis","mvamethod");
	topology = "";
	if(mvaMethod.Contains("MLP"))
		topology = (string)cfg.Value("analysis","topology");
	iterations = (unsigned int)cfg.Value("analysis","iterations");
	trainEntries = (unsigned int)cfg.Value("analysis","trainentries");
	workingPoint = (double)cfg.Value("analysis","workingpoint");
	lumi = (double)cfg.Value("analysis","lumi");
	histBins = (unsigned int)cfg.Value("analysis","histbins");
	plotBins = (unsigned int)cfg.Value("analysis","plotbins");
	writeOptions = (string)cfg.Value("analysis","writeoptions");
	outputTasks = (string)cfg.Value("analysis","outputtasks");
	splitName = (string)cfg.Value("analysis","splitname");
	logName = (string)cfg.Value("analysis","log");

	TString inputVarString = (string)cfg.Value("analysis","inputvar");
	TObjArray* tempArray = inputVarString.Tokenize(",");
	for(int k=0; k<tempArray->GetEntries(); k++){
		TObjString* tempObj = (TObjString*) tempArray->At(k);
		TString varName = (TString) tempObj->GetString();
		if(varName != "")
			inputVars.push_back(tempObj->GetString());
	}
	nInputVars = inputVars.size();
	delete tempArray;

	nProc = 0;
	for(int i=0; i<cfg.GetNSections()-1; i++){
		paths.push_back( (string)cfg.Value("proc_"+SSTR(i),"path") );
		names.push_back( (string)cfg.Value("proc_"+SSTR(i),"name") );
		types.push_back( (int)cfg.Value("proc_"+SSTR(i),"signal") );
		xSections.push_back( (double)cfg.Value("proc_"+SSTR(i),"xsection") );
		totEvents.push_back( (long)cfg.Value("proc_"+SSTR(i),"genevents") );
		treeNames.push_back( (string)cfg.Value("proc_"+SSTR(i),"treename") );
		colors.push_back( TranslateColor((string)cfg.Value("proc_"+SSTR(i),"color")) );
		
		std::vector<TString> thisWeights;
		TString weightString = (string)cfg.Value("proc_"+SSTR(i),"evtweight");
		TObjArray* tempArray = weightString.Tokenize("*");
		for(int k=0; k<tempArray->GetEntries(); k++){
			TObjString* tempObj = (TObjString*) tempArray->At(k);
			TString weightName = (TString) tempObj->GetString();
			if(weightName != "")
				thisWeights.push_back((TString) tempObj->GetString());
		}
		delete tempArray;
		evtWeights.push_back(thisWeights);
		
		nProc++;
	}
}

TString PConfig::GetPath(unsigned int i) const{
	return paths.at(i);
}

TString PConfig::GetName(unsigned int i) const{
	return names.at(i);
}

int PConfig::GetType(unsigned int i) const{
	return types.at(i);
}

Color_t PConfig::GetColor(unsigned int i) const{
	return colors.at(i);
}

double PConfig::GetXSection(unsigned int i) const{
	return xSections.at(i);
}

long PConfig::GetTotEvents(unsigned int i) const{
	return totEvents.at(i);
}

TString PConfig::GetTreeName(unsigned int i) const{
	return treeNames.at(i);
}

std::vector<TString> PConfig::GetEvtWeights(unsigned int i) const{
	return evtWeights.at(i);
}

unsigned int PConfig::GetNProc(void) const{
	return nProc;
}

unsigned int PConfig::GetNInputVars(void) const{
	return nInputVars;
}

TString PConfig::GetAnaName(void) const{
	return anaName;
}

TString PConfig::GetOutputDir(void) const{
	return outputDir;
}

TString PConfig::GetOutputName(void) const{
	return outputName;
}

TString PConfig::GetTopology(void) const{
	return topology;
}

TString PConfig::GetMvaMethod(void) const{
	return mvaMethod;
}

unsigned int PConfig::GetIterations(void) const{
	return iterations;
}

unsigned int PConfig::GetTrainEntries(void) const{
	return trainEntries;
}

double PConfig::GetWorkingPoint(void) const{
	return workingPoint;
}

double PConfig::GetLumi(void) const{
	return lumi;
}

unsigned int PConfig::GetHistBins(void) const{
	return histBins;
}

unsigned int PConfig::GetPlotBins(void) const{
	return plotBins;
}

TString PConfig::GetWriteOptions(void) const{
	return writeOptions;
}

TString PConfig::GetOutputTasks(void) const{
	return outputTasks;
}

TString PConfig::GetSplitName(void) const{
	return splitName;
}

TString PConfig::GetLogName(void) const{
	return logName;
}

TString PConfig::GetInputVar(unsigned int i) const{
	return inputVars.at(i);
}

Color_t PConfig::TranslateColor(TString color) const{
	Color_t finalColor = 0;
	vector<TString> tempColor;
	TObjArray* tempArray = color.Tokenize("+");
	for(int k=0; k<tempArray->GetEntries(); k++){
		TObjString* tempObj = (TObjString*) tempArray->At(k);
		tempColor.push_back(tempObj->GetString());
	}
	if(tempColor.size() > 2){
		cerr << "Invalid color specified!\n",
		exit(1);
	}
	if(tempColor.at(0).Contains("k")){
		map<TString, Color_t> colorMap;
		colorMap["kWhite"] = kWhite;
		colorMap["kBlack"] = kBlack;
		colorMap["kGray"] = kGray;
		colorMap["kRed"] = kRed;
		colorMap["kGreen"] = kGreen;
		colorMap["kBlue"] = kBlue;
		colorMap["kYellow"] = kYellow;
		colorMap["kMagenta"] = kMagenta;
		colorMap["kCyan"] = kCyan;
		colorMap["kOrange"] = kOrange;
		colorMap["kSpring"] = kSpring;
		colorMap["kTeal"] = kTeal;
		colorMap["kAzure"] = kAzure;
		colorMap["kViolet"] = kViolet;
		colorMap["kPink"] = kPink;
		finalColor = colorMap[tempColor.at(0)];
		if(tempColor.size() == 2)
			finalColor += tempColor.at(1).Atoi();
	}else{
		finalColor += tempColor.at(0).Atoi();
	}
	return finalColor;
}
	
