#ifndef DEF_NN_PPROC
#define DEF_NN_PPROC

#include <iostream>
#include "TString.h"
#include "TFile.h"
#include "TTree.h"
#include "TH1.h"
#include "TColor.h"

#include "defs.h"
#include "pconfig.h"

class PProc{
	public:
	
	PProc(PConfig *config, unsigned int num);
	~PProc();

	void SetInputReweight(double reweight);
	void SetHistReweight(double reweight);
	void Open(void);
	void Close(void);

	TString GetPath(void) const;
	TString GetName(void) const;
	int GetType(void) const;
	double GetXSection(void) const;
	double GetEfficiency(void) const;
	double GetInputReweight(void) const;
	double GetHistReweight(void) const;
	double *GetHyp(TString hypName);
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
	int myType;
	double myXSection;
	double myEfficiency;
	double myInputReweight;
	double myHistReweight;
	Color_t myColor;

	std::vector<double> myWeight;
};

bool compareProc(const PProc* lhs, const PProc* rhs);

#endif
