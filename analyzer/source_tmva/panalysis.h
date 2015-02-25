#ifndef DEF_NN_PANALYSIS
#define DEF_NN_PANALYSIS

#include <vector>
#include "TString.h"
#include "TFile.h"
#include "TH1.h"
#include "THStack.h"
#include "TLegend.h"
#include "TMVA/Factory.h"
#include "TCanvas.h"
#include "TGraph.h"
#include "TLine.h"

#include "defs.h"
#include "pdata.h"
#include "pconfig.h"

double min(double a, double b);

class PAnalysis{
	public:

	PAnalysis(PConfig *config);
	~PAnalysis();

	void DefineAndTrainFactory(unsigned int iterations=0, TString method="", TString topo="");
	void DoHist(bool evalOnTrained=false);
	void DoPlot(void);
	void DoROC(void);
	void BkgEffWP(double workingPoint=0);
	//void FiguresOfMerit(void);
	void WriteOutput(TString options="");
	void WriteSplitProc(TString outputDir="");
	void WriteLog(TString output="");
	double GetBkgEff(void) const;
	double GetSigEff(void) const;

	private:

	PConfig *myConfig;

	void AddProc(PProc* data);
	void OpenAllProc(void);
	void CloseAllProc(void);
	void FillStack(void);
	double Transform(TString method, double output);
	
	TFile* myOutputFile;
	THStack* myStack;

	int mySig;
	std::vector<unsigned int> myBkgs; // we may train against several backgrounds
	//double sRootB, sRootSB, sB;
	double myCut, myBkgEff, mySigEff;
	long myMinMCNumberSig;
	long myMinMCNumberBkg;

	TMVA::Factory* myFactory;

	TString myName;
	TString myOutput;
	TString myMvaMethod;
	
	std::vector<PProc*> myProc;

	TCanvas* myCnvTraining;
	TCanvas* myCnvPlot;
	TLegend* myLegend;
	TCanvas* myCnvEff;
	TGraph* myROC;
	TLine* myLine;
	TLine* myCutLine;
};

#endif
