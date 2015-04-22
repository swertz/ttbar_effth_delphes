#include <cstdlib> // for exit() function
#include "pproc.h"

using namespace std;

PProc::PProc(PConfig* config, unsigned int num){
  #ifdef P_LOG
    cout << "Creating PProc instance nr. " << num << " for " << config->GetName(num) << ".\n";
  #endif

  myConfig = config;
  myName = myConfig->GetName(num);
  myType = myConfig->GetType(num);
  myColor = myConfig->GetColor(num);
  myXSection = myConfig->GetXSection(num);
  myHist = (TH1D*) new TH1D((myName + "_output").c_str(), "MVA output", myConfig->GetHistBins(), 0., 1.);
  myHist->Sumw2();
  myPaths = myConfig->GetPaths(num);
  myTreeName = myConfig->GetTreeName(num);
  myGenMCEvents = (double)myConfig->GetTotEvents(num);
  
  myEvtWeightNames = myConfig->GetEvtWeights(num);
  for(unsigned int i=0; i<myEvtWeightNames.size(); i++)
    myEvtWeights.push_back(0);

  for(unsigned int i=0; i<myConfig->GetNInputVars(); i++)
    myInputVars.push_back(0);

  myChain = new TChain(myTreeName.c_str());
  for(auto &i: myPaths)
    myChain->Add(i.c_str()); 

  myEntries = (double) myChain->GetEntries();

  myChain->Draw("This->GetReadEntry()>>tempHist", GetEvtWeightsString().c_str(), "goff");
  TH1F* tempHist = (TH1F*) gDirectory->Get("tempHist");
  myEffEntries = tempHist->Integral();
  delete tempHist; tempHist = NULL;

  delete myChain; myChain = NULL;
}

void PProc::Open(void){
  // Create the TChain and defines the branches so that the PProc methods
  // return the input variables or weights associated with the event
  // being read at the moment.
  
  myChain = new TChain(myTreeName.c_str());
  for(auto &i: myPaths)
    myChain->Add(i.c_str()); 

  for(unsigned int i=0; i<myConfig->GetNInputVars(); i++)
    myChain->SetBranchAddress(myConfig->GetInputVar(i).c_str(), &myInputVars.at(i));
  
  for(unsigned int i = 0; i < myEvtWeightNames.size(); ++i)
    myChain->SetBranchAddress(myEvtWeightNames.at(i).c_str(), &myEvtWeights.at(i));
}

void PProc::Close(void){
  delete myChain; myChain = NULL;
}

std::vector<std::string> PProc::GetPaths(void) const{
  return myPaths;
}

std::string PProc::GetName(void) const{
  return myName;
}

int8_t PProc::GetType(void) const{
  return myType;
}

double PProc::GetXSection(void) const{
  return myXSection;
}

double PProc::GetGenMCEvents(void) const{
  return myGenMCEvents;
}

double PProc::GetEntries(void) const{
  return myEntries;
}

double PProc::GetEffEntries(void) const{
  return myEffEntries;
}

double PProc::GetEffEntries(const std::string& condition){
  // Return effective number of entries, based on the condition

  bool wasOpen = myChain->GetEntries() > 0;
  if(!wasOpen)
    Open();

  myChain->Draw("This->GetReadEntry()>>tempHist", ("(" + condition + ")*" + GetEvtWeightsString()).c_str(), "goff");
  TH1F* tempHist = (TH1F*)gDirectory->Get("tempHist");
  double effEntries = tempHist->Integral();
  delete tempHist; tempHist = NULL;

  if(!wasOpen)
    Close();

  return effEntries;
}

double PProc::GetEffEntriesAbs(void) const{
  return myEffEntriesAbs;
}

double PProc::GetEffEntriesAbs(const std::string& condition){
  // Return effective number of entries, based on the condition
  // Using the sum of abs(weight)

  bool wasOpen = myChain->GetEntries() > 0;
  if(!wasOpen)
    Open();

  myChain->Draw("This->GetReadEntry()>>tempHist", ("(" + condition + ")*abs("+GetEvtWeightsString()+")").c_str(), "goff");
  TH1F* tempHist = (TH1F*)gDirectory->Get("tempHist");
  double effEntries = tempHist->Integral();
  delete tempHist; tempHist = NULL;

  if(!wasOpen)
    Close();

  return effEntries;
}

double PProc::GetYield(void) const{
  return myEffEntries*GetGlobWeight();
}

double PProc::GetYield(const std::string& condition){
  return GetEffEntries(condition)*GetGlobWeight();
}

double PProc::GetYieldAbs(void) const{
  return myEffEntriesAbs*GetGlobWeight();
}

double PProc::GetYieldAbs(const std::string& condition){
  return GetEffEntriesAbs(condition)*GetGlobWeight();
}

double PProc::GetGlobWeight(void) const{
  return myXSection*myConfig->GetLumi()/myGenMCEvents;
}

std::string PProc::GetEvtWeightsString(void) const{
  std::string weight = myEvtWeightNames.at(0);

  for(auto i = myEvtWeightNames.begin() + 1; i != myEvtWeightNames.end(); ++i)
    weight += "*" + (*i);

  return weight;
}

double PProc::GetEvtWeight(void) const{
  if(myChain->GetEntries() <= 0){
    cerr << "Error in " << myName << "::GetEvtWeight(): can't return event weight without opening the process first.\n";
    exit(1);
  }

  float weight = 1.;
  
  for(auto &i : myEvtWeights)
    weight *= i;
  
  return (double) weight;
}

double* PProc::GetInputVar(const std::string& varName){
  if(myChain->GetEntries() <= 0){
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
  if(myChain->GetEntries() <= 0){
    cerr << "Error in " << myName << "::GetTree(): can't return TTree without opening the process first.\n";
    exit(1);
  }
  return myChain;
}

TH1D* PProc::GetHist(void) const{
  return myHist;
}

Color_t PProc::GetColor(void) const{
  return myColor;
}

bool compareProc(const PProc* lhs, const PProc* rhs){
  return lhs->GetYield() < rhs->GetYield();
}

PProc::~PProc(){
  #ifdef P_LOG
    cout << "Destroying PProc " << myName << "." << endl;
  #endif
  delete myHist; myHist = NULL;
  delete myChain; myChain = NULL;
}
