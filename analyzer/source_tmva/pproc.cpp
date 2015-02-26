#include <cstdlib> // for exit() function
#include "pproc.h"

using namespace std;

PProc::PProc(PConfig* config, unsigned int num){
	#ifdef P_LOG
		cout << "Creating PProc instance nr. " << num << " for " << config->GetName(num) << ".\n";
	#endif
	myPath = config->GetPath(num);
	myFile = (TFile*) new TFile(myPath, "READ");
	if(myFile->IsZombie()){
		cerr << "Failure opening file " << myPath << ".\n";
		exit(1);
	}
	myTreeName = config->GetTreeName(num);
	myTree = (TTree*) myFile->Get(myTreeName);
	for(unsigned int i=0; i<config->GetNInputVars(); i++)
		myInputVars.push_back(0);
	myEfficiency = (double)myTree->GetEntries()/config->GetTotEvents(num);
	myFile->Close();
	myName = config->GetName(num);
	myType = config->GetType(num);
	myColor = config->GetColor(num);
	myXSection = config->GetXSection(num);
	myYield = myEfficiency*myXSection*config->GetLumi();
	myHist = (TH1D*) new TH1D(myName+"_output", "MVA output", config->GetHistBins(), 0., 1.);
	myConfig = config;
}

void PProc::Open(void){
	myFile = (TFile*) new TFile(myPath, "READ");
	if(myFile->IsZombie()){
		cerr << "Failure opening file " << myPath << ".\n";
		exit(1);
	}
	myTree = (TTree*) myFile->Get(myTreeName);
	for(unsigned int i=0; i<myConfig->GetNInputVars(); i++)
		myTree->SetBranchAddress(myConfig->GetInputVar(i), &myInputVars.at(i));
}

void PProc::Close(void){
	myFile->Close();
}

void PProc::SetInputReweight(double reweight){
	myInputReweight = reweight;
}

void PProc::SetHistReweight(double reweight){
	myHistReweight = reweight;
}

TString PProc::GetPath(void) const{
	return myPath;
}

TString PProc::GetName(void) const{
	return myName;
}

int PProc::GetType(void) const{
	return myType;
}

double PProc::GetXSection(void) const{
	return myXSection;
}

double PProc::GetEfficiency(void) const{
	return myEfficiency;
}

double PProc::GetYield(void) const{
	return myYield;
}

double PProc::GetInputReweight(void) const{
	return myInputReweight;
}

double PProc::GetHistReweight(void) const{
	return myHistReweight;
}

double* PProc::GetInputVar(TString varName){
	if(myTree->GetEntries() <= 0){
		cerr << "Error in " << myName << "::GetInputVar(): can't return input variable without opening the process first.\n";
		exit(1);
	}
	for(unsigned int i=0; i<myConfig->GetNInputVars(); i++){
		if(varName == myConfig->GetInputVar(i))
			return &myInputVars.at(i);
	}
	cerr << "Error in " << myName << "::GetInputVar(): couldn't find input variable " << varName << ". Remember it has to be part of the input variables defined in the [analysis] section.\n";
	exit(1);
}

TTree* PProc::GetTree(void) const{
	if(myTree->GetEntries() <= 0){
		cerr << "Error in " << myName << "::GetTree(): can't return TTree without opening the process first.\n";
		exit(1);
	}
	return myTree;
}

TH1D* PProc::GetHist(void) const{
	return myHist;
}

TFile* PProc::GetFile(void) const{
	if(myFile->IsZombie()){
		cerr << "Error in " << myName << "::GetFile(): can't return TFile without opening the process first.\n";
		exit(1);
	}
	return myFile;
}

Color_t PProc::GetColor(void) const{
	return myColor;
}

bool compareProc(const PProc* lhs, const PProc* rhs){
	return lhs->GetXSection()*lhs->GetEfficiency() < rhs->GetXSection()*rhs->GetEfficiency();
}

PProc::~PProc(){
	#ifdef P_LOG
		cout << "Destroying PProc " << myName << "." << endl;
	#endif
	delete myHist;
	delete myFile;
}
