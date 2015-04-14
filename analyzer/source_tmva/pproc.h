#ifndef DEF_NN_PPROC
#define DEF_NN_PPROC

#include <iostream>
#include "TString.h"
#include "TFile.h"
#include "TTree.h"
#include "TH1.h"
#include "TColor.h"
#include "TROOT.h"

#include "defs.h"
#include "pconfig.h"

class PProc{
  public:
  
  PProc(PConfig *config, unsigned int num);
  ~PProc();

  void Open(void);
  void Close(void);

  TString GetPath(void) const;
  TString GetName(void) const;
  TString GetEvtWeightsString(void) const;
  double GetEvtWeight(void) const;
  int GetType(void) const;
  double GetXSection(void) const;
  double GetGenMCEvents(void) const;
  double GetEntries(void) const;
  double GetEffEntries(void) const;
  double GetEffEntries(TString condition);
  double GetEffEntriesAbs(void) const;
  double GetEffEntriesAbs(TString condition);
  double GetYield(void) const;
  double GetYield(TString condition);
  double GetYieldAbs(void) const;
  double GetYieldAbs(TString condition);
  double GetGlobWeight(void) const;
  double *GetInputVar(TString varName);
  TH1D* GetHist(void) const;
  TTree* GetTree(void) const;
  TFile* GetFile(void) const;
  Color_t GetColor(void) const;

  private:

  PConfig *myConfig;

  TH1D* myHist;
  TTree* myTree;
  TFile* myFile;

  TString myTreeName;
  TString myPath;
  TString myName;
  std::vector<TString> myEvtWeightNames;
  int myType;
  double myXSection;
  double myGenMCEvents;
  double myEntries;
  double myEffEntries;
  double myEffEntriesAbs;
  Color_t myColor;

  std::vector<double> myInputVars;
  std::vector<float> myEvtWeights;
};

bool compareProc(const PProc* lhs, const PProc* rhs);

#endif
