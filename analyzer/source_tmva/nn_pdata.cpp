#include <cstdlib> // for exit() function
#include "nn_pdata.h"

using namespace std;

PData::PData(PConfig* config, unsigned int num){
	#ifdef P_LOG
		cout << "Creating data instance nr. " << num << " for " << config->GetName(num) << ".\n";
	#endif
	myPath = config->GetPath(num);
	myFile = (TFile*) new TFile(myPath, "READ");
	if(myFile->IsZombie()){
		cerr << "Failure opening file " << myPath << ".\n";
		exit(1);
	}
	myTreeName = config->GetTreeName(num);
	myTree = (TTree*) myFile->Get(myTreeName);
	for(unsigned int i=0; i<config->GetNWeights(); i++)
		myWeight.push_back(0);
	myEfficiency = (double)myTree->GetEntries()/config->GetTotEvents(num);
	myFile->Close();
	myName = config->GetName(num);
	myType = config->GetType(num);
	myColor = config->GetColor(num);
	myXSection = config->GetXSection(num);
	myHist = (TH1D*) new TH1D(myName+"_output", "MVA output", config->GetHistBins(), 0., 1.);
	myConfig = config;
}

void PData::Open(void){
	myFile = (TFile*) new TFile(myPath, "READ");
	if(myFile->IsZombie()){
		cerr << "Failure opening file " << myPath << ".\n";
		exit(1);
	}
	myTree = (TTree*) myFile->Get(myTreeName);
	for(unsigned int i=0; i<myConfig->GetNWeights(); i++)
		myTree->SetBranchAddress(myConfig->GetWeight(i), &myWeight.at(i));
}

void PData::Close(void){
	myFile->Close();
}

void PData::SetInputReweight(double reweight){
	myInputReweight = reweight;
}

void PData::SetHistReweight(double reweight){
	myHistReweight = reweight;
}

TString PData::GetPath(void) const{
	return myPath;
}

TString PData::GetName(void) const{
	return myName;
}

int PData::GetType(void) const{
	return myType;
}

double PData::GetXSection(void) const{
	return myXSection;
}

double PData::GetEfficiency(void) const{
	return myEfficiency;
}

double PData::GetInputReweight(void) const{
	return myInputReweight;
}

double PData::GetHistReweight(void) const{
	return myHistReweight;
}

double* PData::GetHyp(TString hypName){
	if(myTree->GetEntries() <= 0){
		cerr << "Error in " << myName << "::GetHyp(): can't return weight without opening the data first.\n";
		exit(1);
	}
	for(unsigned int i=0; i<myConfig->GetNWeights(); i++){
		if(hypName == myConfig->GetWeight(i))
			return &myWeight.at(i);
	}
	cerr << "Error in " << myName << "::GetHyp(): couldn't find weight under hypothesis " << hypName << ".\n";
	exit(1);
}

TTree* PData::GetTree(void) const{
	if(myTree->GetEntries() <= 0){
		cerr << "Error in " << myName << "::GetTree(): can't return TTree without opening the data first.\n";
		exit(1);
	}
	return myTree;
}

TH1D* PData::GetHist(void) const{
	return myHist;
}

TFile* PData::GetFile(void) const{
	if(myFile->IsZombie()){
		cerr << "Error in " << myName << "::GetFile(): can't return TFile without opening the data first.\n";
		exit(1);
	}
	return myFile;
}

Color_t PData::GetColor(void) const{
	return myColor;
}

bool compareData(const PData* lhs, const PData* rhs){
	return lhs->GetXSection()*lhs->GetEfficiency() < rhs->GetXSection()*rhs->GetEfficiency();
}

PData::~PData(){
	#ifdef P_LOG
		cout << "Destroying PData " << myName << "." << endl;
	#endif
	delete myHist;
	delete myFile;
}
