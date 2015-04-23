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
  
  myEvtWeightString = myConfig->GetEvtWeight(num);

  for(unsigned int i=0; i<myConfig->GetNInputVars(); i++)
    myInputVars[ myConfig->GetInputVar(i) ] = 0.;

  myChain = new TChain(myTreeName.c_str());
  for(auto &i: myPaths)
    myChain->Add(i.c_str()); 

  myEntries = (double) myChain->GetEntries();

  myChain->Draw("Entries$>>tempHist", myEvtWeightString.c_str(), "goff");
  TH1F* tempHist = (TH1F*) gDirectory->Get("tempHist");
  myEffEntries = tempHist->Integral();
  delete tempHist; tempHist = NULL;

  delete myChain; myChain = NULL;

  myWeightFormula = NULL;
}

void PProc::Open(void){
  // Create the TChain and defines the branches so that the PProc methods
  // return the input variables or weights associated with the event
  // being read at the moment.
  
  myChain = new TChain(myTreeName.c_str());
  for(auto &i: myPaths)
    myChain->Add(i.c_str()); 

  for(auto &var: myInputVars)
    myChain->SetBranchAddress(var.first.c_str(), &var.second);
 
  myWeightFormula = new TTreeFormula((myName + "_WeightFormula").c_str(), myEvtWeightString.c_str(), myChain);
  // This is needed because we're using a TChain and not a TTree
  // The formula needs to be updated (by calling TTreeFormula::UpdateFormulaLeaves()) 
  // each time a new file of the chain is read.
  // TChain::SetNotify() allows to do this automatically.
  myChain->SetNotify(myWeightFormula);
}

void PProc::Close(void){
  delete myChain; myChain = NULL;
  delete myWeightFormula; myWeightFormula = NULL;
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

  bool wasOpen = myChain != NULL;
  if(!wasOpen)
    Open();

  myChain->Draw("Entries$>>tempHist", ("(" + condition + ")*" + myEvtWeightString).c_str(), "goff");
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

  bool wasOpen = myChain != NULL;
  if(!wasOpen)
    Open();

  myChain->Draw("Entries$>>tempHist", ("(" + condition + ")*abs("+myEvtWeightString+")").c_str(), "goff");
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

std::string PProc::GetEvtWeightString(void) const{
  return myEvtWeightString;
}

double PProc::GetEvtWeight(void) const{
  if(!myChain){
    cerr << "Error in " << myName << "::GetEvtWeight(): can't return event weight without opening the process first.\n";
    exit(1);
  }
  return myWeightFormula->EvalInstance();
}

double* PProc::GetInputVar(const std::string& varName){
  if(!myChain){
    cerr << "Error in " << myName << "::GetInputVar(): can't return input variable without opening the process first.\n";
    exit(1);
  }
  return &myInputVars[varName];
}

TTree* PProc::GetTree(void) const{
  if(!myChain){
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
  delete myWeightFormula; myWeightFormula = NULL;
}
