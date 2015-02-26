#include <cstdlib> // for exit() function
#include <iostream>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <TMVA/Reader.h>
#include <TMVA/Tools.h>
#include <TMVA/Config.h>
#include "panalysis.h"

#define SSTR( x ) dynamic_cast< std::ostringstream & > \
        ( std::ostringstream() << std::dec << x ).str()

double min(double a, double b){
	return (a < b) ? a : b;
}

double max(double a, double b){
	return (a > b) ? a : b;
}

using namespace std;

PAnalysis::PAnalysis(PConfig *config){
	#ifdef P_LOG
		cout << "Initializing analysis " << config->GetAnaName() << "." << endl;
	#endif

	mySig = -1;
	myCut = 0;
	myBkgEff = 0;
	mySigEff = 0;
	myMinMCNumberSig = -1;
	myMinMCNumberBkg = -1;
	
	myConfig = config;
	myName = config->GetAnaName();
	myOutput = config->GetOutputDir() + "/" + config->GetOutputName();

	myOutputFile = (TFile*) new TFile(myOutput+".root", "RECREATE");
	if(myOutputFile->IsZombie()){
		cerr << "Failure opening file " << myOutput+".root" << ".\n";
		exit(1);
	}

	for(unsigned int i=0; i<config->GetNProc(); i++){
		PProc *tempProc = new PProc(config, i);
		AddProc(tempProc);
	}
}

void PAnalysis::AddProc(PProc* proc){
	#ifdef P_LOG
		cout << "Adding process " << proc->GetName() << " to analysis " << myName << "." << endl;
	#endif

	myProc.push_back(proc);
	switch(proc->GetType()){
		case 0:
			myBkgs.push_back(myProc.size()-1);
			break;
		case 1:
			if(mySig >= 0){
				cerr << "Only one signal can be assigned to the analysis!" << endl;
				exit(1);
			}
			mySig = myProc.size()-1;
			break;
		default:
			break;
	}
}

void PAnalysis::OpenAllProc(void){
	for(unsigned int i=0; i<myProc.size(); i++)
		myProc.at(i)->Open();
}

void PAnalysis::CloseAllProc(void){
	for(unsigned int i=0; i<myProc.size(); i++)
		myProc.at(i)->Close();
}

void PAnalysis::DefineAndTrainFactory(unsigned int iterations, TString method, TString topo){
	if(mySig < 0 || !myBkgs.size()){
		cerr << "Cannot compute input weights: at least two processes (one signal and one background) have to be assigned to the analysis!" << endl;
		exit(1);
	}

	OpenAllProc();

	// Computing input weights
	// Note: not quite clear how TMVA computes the weights (how are they combined with the gen weight?)
	//		... should be OK to pass as input weight xsection*eff*lumi/nSelected for each process

	for(unsigned int i=0; i<myProc.size(); i++){
		double xS = myProc.at(i)->GetXSection();
		double eff = myProc.at(i)->GetEfficiency();
		double nSel = myProc.at(i)->GetTree()->GetEntries();
		double lumi = myConfig->GetLumi(); 
		myProc.at(i)->SetInputReweight(xS*eff*lumi/nSel);
	}

	if(topo == "")
		topo = myConfig->GetTopology();
	if(method == "")
		method = myConfig->GetMvaMethod();
	myMvaMethod = method;
	if(iterations== 0)
		iterations = myConfig->GetIterations();

	// Defining Factory and MVA

	#ifdef P_LOG
		cout << "Initialising factory of type " << method;
		if(method == "MLP" || method == "TMLP")
			cout << " and of topology " << topo << ".\n";
		else
			cout << ".\n";
	#endif

	TMVA::Tools::Instance();
	(TMVA::gConfig().GetIONames()).fWeightFileDir = myConfig->GetOutputDir();
	
	#ifdef P_LOG
		myFactory = (TMVA::Factory*) new TMVA::Factory(myName, myOutputFile, "!DrawProgressBar");
	#else
		myFactory = (TMVA::Factory*) new TMVA::Factory(myName, myOutputFile, "Silent:!DrawProgressBar");
	#endif
	myFactory->AddSignalTree(myProc.at(mySig)->GetTree(), myProc.at(mySig)->GetInputReweight());
	for(unsigned int i=0; i<myBkgs.size(); i++)
		myFactory->AddBackgroundTree(myProc.at(myBkgs.at(i))->GetTree(), myProc.at(myBkgs.at(i))->GetInputReweight());

	// Will also use weights defined in the input process dataset
	// Careful if these weights are negative!
	if(myConfig->GetGenWeight() != "")
		myFactory->SetWeightExpression(myConfig->GetGenWeight());

	for(unsigned int i=0; i<myConfig->GetNInputVars(); i++)
		myFactory->AddVariable(myConfig->GetInputVar(i));

	// Events: train/test/train/test/...
	// ? for each background tree or for all the brackgrounds together ?
	myFactory->PrepareTrainingAndTestTree("", "nTrain_Signal="+SSTR(myConfig->GetTrainEntries())+":nTrain_Background="+SSTR(myConfig->GetTrainEntries())+":nTest_Signal="+SSTR(myConfig->GetTrainEntries())+":nTest_Background="+SSTR(myConfig->GetTrainEntries())+":SplitMode=Alternate:NormMode=EqualNumEvents");

	if(method == "MLP")
		myFactory->BookMethod(TMVA::Types::kMLP, method+"_"+myName, "!H:V:NeuronType=tanh:VarTransform=Norm:IgnoreNegWeightsInTraining=True:NCycles="+SSTR(iterations)+":HiddenLayers="+topo+":TestRate=5:TrainingMethod=BFGS:SamplingTraining=False:ConvergenceTests=50");
	else if(method == "BDT")
		myFactory->BookMethod(TMVA::Types::kBDT, method+"_"+myName, "!H:V:NTrees="+SSTR(iterations));
	else{
		cerr << "Couldn't recognize MVA method.\n";
		exit(1);
	}

	// Training and stuff

	myFactory->TrainAllMethods();
	myFactory->TestAllMethods();
	myFactory->EvaluateAllMethods();

	CloseAllProc();
}

void PAnalysis::DoHist(bool evalOnTrained){
	#ifdef P_LOG
		cout << "Filling output histograms.\n";
	#endif
	if(!myFactory){
		cerr << "Cannot draw NN output histograms without having defined and trained the factory! Attemping to call DefineAndTrainFactory().\n";
		DefineAndTrainFactory();
	}
	
	vector<float> inputs(myConfig->GetNInputVars());
	TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
	for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
		myReader->AddVariable(myConfig->GetInputVar(k), &inputs.at(k));
	myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");

	OpenAllProc();

	// Computing event reweighting for the histograms

	double expBkg = 0;
	for(unsigned int i=0; i<myProc.size(); i++){
		if(myProc.at(i)->GetType() != 1){
			double xS = myProc.at(i)->GetXSection();
			double eff = myProc.at(i)->GetEfficiency();
			expBkg += xS*eff;
		}
	}
	double entriesSig;
	if(evalOnTrained)
		entriesSig = myProc.at(mySig)->GetTree()->GetEntries();
	else
		entriesSig = max(floor(myProc.at(mySig)->GetTree()->GetEntries()/2), myProc.at(mySig)->GetTree()->GetEntries() - myConfig->GetTrainEntries());

	for(unsigned int i=0; i<myProc.size(); i++){
		if(myProc.at(i)->GetType() != 1){
			double xS = myProc.at(i)->GetXSection();
			double eff = myProc.at(i)->GetEfficiency();
			double entriesBkg = myProc.at(i)->GetTree()->GetEntries();
			if(!evalOnTrained && myProc.at(i)->GetType() == 0)
				entriesBkg = max(floor(myProc.at(i)->GetTree()->GetEntries()/2), myProc.at(i)->GetTree()->GetEntries() - myConfig->GetTrainEntries());
			myProc.at(i)->SetHistReweight(xS*eff/entriesBkg);
		}
	}
	myProc.at(mySig)->SetHistReweight(expBkg/entriesSig);

	// Filling histograms

	for(unsigned int j=0; j<myProc.size(); j++){
		PProc* proc = (PProc*) myProc.at(j);

		for(long i=0; i<proc->GetTree()->GetEntries(); i++){
			if(proc->GetType() >= 0 && i%2==0 && i < 2*myConfig->GetTrainEntries() && !evalOnTrained)
				continue;
			proc->GetTree()->GetEntry(i);
			for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
				inputs.at(k) = (float) *proc->GetInputVar(myConfig->GetInputVar(k));
			proc->GetHist()->Fill(Transform(myMvaMethod, myReader->EvaluateMVA(myName)), proc->GetHistReweight());
		}
		
		proc->GetHist()->SetLineWidth(3);
		proc->GetHist()->SetLineColor(proc->GetColor());
		proc->GetHist()->SetXTitle("MVA output");
		proc->GetHist()->SetStats(0);
		if(proc->GetType() == -1)
			proc->GetHist()->SetLineStyle(2);
		else
			proc->GetHist()->SetLineStyle(0);

	}

	CloseAllProc();
	
	delete myReader;
}

float PAnalysis::Transform(TString method, float input){
	if(method == "BDT")
		return 1/(1+exp(-10*input));
	else if(method.Contains("MLP"))
		return 1/(1+exp(-5*(input-0.5)));
	else
		return input;
}

void PAnalysis::DoPlot(void){
	#ifdef P_LOG
		cout << "Plotting output histograms.\n";
	#endif
	if(!myProc.at(0)->GetHist()->GetEntries()){
		cerr << "Cannot plot MVA output histograms without histograms! Attemping to call DoHist().\n";
		DoHist();
	}
	
	myCnvPlot = (TCanvas*) new TCanvas(myName+"_MVA output","MVA output");
	myLegend = new TLegend(0.73,0.7,0.89,0.89);
	myLegend->SetFillColor(0);
	myStack = (THStack*) new THStack("output_stack","MVA output");
	
	for(unsigned int j=0; j<myProc.size(); j++)
		myLegend->AddEntry(myProc.at(j)->GetHist(), myProc.at(j)->GetName(), "f");
	FillStack();

	TH1D* tempSigHist = (TH1D*) myProc.at(mySig)->GetHist()->Rebin(myConfig->GetHistBins()/myConfig->GetPlotBins(),"rebinned");

	if(myStack->GetMaximum() > tempSigHist->GetMaximum()){
		myStack->Draw("");
		tempSigHist->Draw("same");
		myStack->Draw("same");
	}else{
		tempSigHist->Draw("");
		myStack->Draw("same");
		tempSigHist->Draw("same");
	}

	myLegend->Draw();
}

void PAnalysis::FillStack(void){
	vector<PProc*> pointers;
	for(unsigned int i=0; i<myProc.size(); i++){
		if(myProc.at(i)->GetType() != 1)
			pointers.push_back(myProc.at(i));
	}
	sort(pointers.begin(), pointers.end(), &compareProc);
	for(unsigned int i=0; i<pointers.size(); i++)
		myStack->Add(pointers.at(i)->GetHist()->Rebin(myConfig->GetHistBins()/myConfig->GetPlotBins(),"rebinned"));
}

void PAnalysis::DoROC(void){
	#ifdef P_LOG
		cout << "Drawing ROC curve.\n";
	#endif
	if(mySig<0 || !myBkgs.size()){
		cerr << "Cannot draw ROC curve without signal and background processes!\n";
		exit(1);
	}else if(!myProc.at(0)->GetHist()->GetEntries()){
		cerr << "Cannot draw ROC curve without process histograms! Attempting to call DoHist().\n";
		DoHist();
	}
	
	double countS = myProc.at(mySig)->GetHist()->Integral();
	double totS = countS;
	double countBkg = 0;
	unsigned int nBins = myConfig->GetHistBins();
	for(unsigned int i=0; i<myBkgs.size(); i++)
		countBkg += myProc.at(myBkgs.at(i))->GetHist()->Integral();
	double totBkg = countBkg;
	double sigEff[nBins+2];
	double bkgEff[nBins+2];

	for(unsigned int i=0; i<=nBins+1; i++){
		countS -= (double)myProc.at(mySig)->GetHist()->GetBinContent(i);
		for(unsigned int j=0; j<myBkgs.size(); j++)
			countBkg -= (double)myProc.at(myBkgs.at(j))->GetHist()->GetBinContent(i);
		sigEff[i] = countS/totS;
		bkgEff[i] = countBkg/totBkg;
	}

	sigEff[0] = 1.;
	sigEff[nBins+1] = 0.;
	bkgEff[0] = 1.;
	bkgEff[nBins+1] = 0.;
	
	myROC = (TGraph*) new TGraph(nBins+2, bkgEff, sigEff);
	myROC->GetXaxis()->SetTitle("Background sigEff");
	myROC->GetYaxis()->SetTitle("Signal sigEff");
	myROC->SetTitle("Signal vs bkg sigEff (cut on NN)");
	myROC->SetMarkerColor(kBlue);
	myROC->SetMarkerStyle(20);
	
	myCnvEff = (TCanvas*) new TCanvas("ROC","Signal sigEff vs bkg. sigEff");
	myCnvEff->SetGrid(20,20);
	myROC->Draw("ALP");
	myLine = (TLine*) new TLine(0,0,1,1);
	myLine->Draw();
}

void PAnalysis::BkgEffWP(double workingPoint){
	if(workingPoint == 0)
		workingPoint = myConfig->GetWorkingPoint();
	#ifdef P_LOG
		cout << "Computing cut for signal efficiency = " << workingPoint << "... ";
	#endif
	if(!myROC){
		cerr << "Cannot compute background efficiency without ROC curve! Attempting to call DoROC().\n";
		DoROC();
	}
	if(workingPoint > 1 || workingPoint <= 0){
		cerr << "Working point must be a double between 0 and 1!\n";
		exit(1);
	}
	
	unsigned int nBins = myConfig->GetHistBins();

	double* sigEff = myROC->GetY();
	double* bkgEff = myROC->GetX();
	
	for(unsigned int i=1; i<=nBins+1; i++){
		if(sigEff[i] < workingPoint && sigEff[i-1] >= workingPoint){
			if(sigEff[i-1]-workingPoint < workingPoint-sigEff[i]){
				myBkgEff = bkgEff[i-1];
				mySigEff = sigEff[i-1];
				myCut = myProc.at(mySig)->GetHist()->GetXaxis()->GetBinLowEdge(i-1);
				break;
			}else{
				myBkgEff = bkgEff[i];
				mySigEff = sigEff[i];
				myCut = myProc.at(mySig)->GetHist()->GetXaxis()->GetBinLowEdge(i);
				break;
			}
		}
	}
	if(myCut == 0){
		cerr << "Error finding cut for specified working point.\n";
		exit(1);
	}

	myCnvPlot->cd();
	myCutLine = (TLine*) new TLine(myCut,0,myCut,max(myStack->GetMaximum(), myProc.at(mySig)->GetHist()->GetMaximum()));
	myCutLine->SetLineWidth(3);
	myCutLine->Draw();

	#ifdef P_LOG
		cout << "Found background efficiency = " << myBkgEff << " and signal efficiency = " << mySigEff << " at cut = " << myCut << ".\n";
	#endif
}

void PAnalysis::BkgEffWPPrecise(double workingPoint){
	if(workingPoint == 0)
		workingPoint = myConfig->GetWorkingPoint();
	#ifdef P_LOG
		cout << "Computing precise cut for signal efficiency = " << workingPoint << "... " << endl;
	#endif
	if(!myFactory){
		cerr << "Cannot compute precise working point without having defined and trained the factory! Attemping to call DefineAndTrainFactory().\n";
		DefineAndTrainFactory();
	}
	if(workingPoint > 1 || workingPoint <= 0){
		cerr << "Working point must be a double between 0 and 1!\n";
		exit(1);
	}

	// We will evaluate the MVA on the signal, build a vector of (MVA output), sort it, and cut the vector at the working point to find the MVA cut value

	vector<float> inputs(myConfig->GetNInputVars());
	TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
	for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
		myReader->AddVariable(myConfig->GetInputVar(k), &inputs.at(k));
	myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");

	// Fetching the signal
	PProc* proc = (PProc*) myProc.at(mySig);
	proc->Open();
	TTree* tree = proc->GetTree();
	
	vector<float> mvaOutput;
	
	for(long i=0; i<tree->GetEntries(); i++){
		tree->GetEntry(i);
		for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
			inputs.at(k) = (float) *proc->GetInputVar(myConfig->GetInputVar(k));
		float mva = Transform(myMvaMethod, myReader->EvaluateMVA(myName));
		mvaOutput.push_back(mva);
	}

	sort(mvaOutput.begin(), mvaOutput.end());

	// the sort is in ascending MVA values, so we have to cut at 1-workingPoint
	int cutIndex = (int) floor( (1.-workingPoint) * tree->GetEntries() );

	mySigEff = 1. - (double) cutIndex / tree->GetEntries();

	// just a security in the limiting case of workingPoint = 0.
	if(cutIndex == tree->GetEntries())
		myCut = (double) *mvaOutput.end() + 1.;
	else
		myCut = (double) mvaOutput.at(cutIndex);

	proc->Close();
	
	// Draw cut line on plot canvas, if it exists
	if(myCnvPlot){
		myCnvPlot->cd();
		myCutLine = (TLine*) new TLine(myCut,0,myCut,max(myStack->GetMaximum(), myProc.at(mySig)->GetHist()->GetMaximum()));
		myCutLine->SetLineWidth(3);
		myCutLine->Draw();
	}

	// Compute background efficiency using this cut:
	
	double bkgSelectedYield = 0.;
	double bkgTotYield = 0.;
	
	for(unsigned int j=0; j<myBkgs.size(); j++){
		PProc* proc = (PProc*) myProc.at(myBkgs.at(j));

		proc->Open();

		int count = 0;

		for(long i=0; i<proc->GetTree()->GetEntries(); i++){
			proc->GetTree()->GetEntry(i);
			for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
				inputs.at(k) = (float) *proc->GetInputVar(myConfig->GetInputVar(k));
			if(Transform(myMvaMethod, myReader->EvaluateMVA(myName)) >= myCut)
				count++;
		}

		bkgSelectedYield += proc->GetYield() * (double)count / proc->GetTree()->GetEntries();
		bkgTotYield += proc->GetYield();

		proc->Close();
	}

	myBkgEff = bkgSelectedYield/bkgTotYield;
	
	delete myReader;
	
	#ifdef P_LOG
		cout << "For signal efficiency " << mySigEff << ", MVA cut is (precisely) " << myCut << ", and background efficiency is " << myBkgEff << ".\n";
	#endif
}

/*void PAnalysis::FiguresOfMerit(void){
	#ifdef P_LOG
		cout << "Computing figures of merit." << endl;
	#endif
	if(mySig<0 || !myBkgs.size()){
		cerr << "Cannot compute figures of merit without signal and background proc!\n";
		exit(1);
	}else if(!myProc.at(0)->GetHist()->GetEntries()){
		cerr << "Cannot compute figures of merit without proc histograms! Attempting to call DoOutHist().\n";
		DoOutHist();
	}

	double totS = myProc.at(mySig)->GetHist()->Integral();
	double totBkg = 0;
	for(unsigned int i=0; i<myBkgs.size(); i++)
		totBkg += myProc.at(myBkgs.at(i))->GetHist()->Integral();
	double expBkg = myConfig->GetLumi()*totBkg;
	double expSig = myConfig->GetLumi()*myProc.at(mySig)->GetXSection()*myProc.at(mySig)->GetEfficiency();
	double tempSB, tempSRootB, tempSRootSB;
	double bestSRBsig = 0, bestSRBbkg = 0;

	for(int i=0; i<=P_NBINS+1; i++){
		expSig -= myConfig->GetLumi()*myProc.at(mySig)->GetXSection()*myProc.at(mySig)->GetEfficiency()*(double)myProc.at(mySig)->GetHist()->GetBinContent(i)/totS;
		for(unsigned int j=0; j<myBkgs.size(); j++)
			expBkg -= myConfig->GetLumi()*(double)myProc.at(myBkgs.at(j))->GetHist()->GetBinContent(i);

		tempSB = expSig/expBkg;
		tempSRootB = expSig/sqrt(expBkg);
		tempSRootSB = expSig/sqrt(expBkg+expSig);
		if(i > 2 && i < P_NBINS - 2){
			if(tempSB > sB)
				sB = tempSB;
			if(tempSRootB > sRootB){
				bestSRBsig = expSig;
				bestSRBbkg = expBkg;
				sRootB = tempSRootB;
			}
			if(tempSRootSB > sRootSB)
				sRootSB = tempSRootSB;
		}
	}

	#ifdef P_LOG
		cout << "Found best figures:" << endl;
		cout << "	S/B = " << sB << endl;
		cout << "	S/sqrt(B) = " << sRootB << ": signal=" << bestSRBsig << ", background=" << bestSRBbkg << endl;
		cout << "	S/sqrt(S+B) = " << sRootSB << endl;
	#endif
}*/

void PAnalysis::WriteOutput(TString options){
	#ifdef P_LOG
		cout << "Writing output to " << myOutput << ".root.\n"; 
	#endif
	if(options == "")
		options = myConfig->GetWriteOptions();

	myOutputFile->cd();
	if(myCnvEff && options.Contains("ROC"))
		myCnvEff->Write("ROC");
	if(myCnvPlot && options.Contains("plot"))
		myCnvPlot->Write("Plot");
	if(myProc.at(0)->GetHist()->GetEntries() && options.Contains("hist")){
		myProc.at(mySig)->GetHist()->Scale(myProc.at(mySig)->GetXSection()*myProc.at(mySig)->GetEfficiency()/myProc.at(mySig)->GetHist()->Integral());
		for(unsigned int i=0; i<myProc.size(); i++){
			myProc.at(i)->GetHist()->Scale(myConfig->GetLumi());
			myProc.at(i)->GetHist()->Write();
		}
	}
	if(myROC && options.Contains("ROC"))
		myROC->Write("ROC curve");
}

void PAnalysis::WriteSplitRootFiles(TString outputDir){
	if(outputDir == "")
		outputDir = myConfig->GetOutputDir();
	#ifdef P_LOG
		cout << "Splitting root files and writing output files.\n"; 
	#endif
	if(!myCut){
		cerr << "Cannot write split root files without knowing the cut value! Attempting to call BkgEffWPPrecise().\n";
		BkgEffWPPrecise();
	}
		
	vector<float> inputs(myConfig->GetNInputVars());
	TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
	for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
		myReader->AddVariable(myConfig->GetInputVar(k), &inputs.at(k));
	myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");

	for(unsigned int j=0; j<myProc.size(); j++){
		PProc* proc = (PProc*) myProc.at(j);

		proc->Open();

		TFile* outFileSig = new TFile(outputDir + "/" + myName + "_siglike_proc_" + proc->GetName() + ".root","RECREATE");
		TTree* treeSig = proc->GetTree()->CloneTree(0);
		
		TFile* outFileBkg = new TFile(outputDir + "/" + myName + "_bkglike_proc_" + proc->GetName() + ".root","RECREATE");
		TTree* treeBkg = proc->GetTree()->CloneTree(0);
		
		if(outFileSig->IsZombie() || outFileBkg->IsZombie()){
			cerr << "Error creating split output files.\n";
			exit(1);
		}
		
		float mvaOutput;
		TString outBranchName = "MVAOUT__" + outputDir + "/" + myName;
		outBranchName.ReplaceAll("//","__");
		outBranchName.ReplaceAll("/","__");
		treeSig->Branch(outBranchName, &mvaOutput, outBranchName + "/F");
		treeBkg->Branch(outBranchName, &mvaOutput, outBranchName + "/F");
		
		for(long i=0; i<proc->GetTree()->GetEntries(); i++){
			proc->GetTree()->GetEntry(i);
			for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
				inputs.at(k) = (float) *proc->GetInputVar(myConfig->GetInputVar(k));
			mvaOutput = Transform(myMvaMethod, myReader->EvaluateMVA(myName));
			if(mvaOutput < myCut)
				treeBkg->Fill();
			else
				treeSig->Fill();
		}

		if(myMinMCNumberSig < 0 || treeSig->GetEntries() < myMinMCNumberSig)
			myMinMCNumberSig = treeSig->GetEntries();
		
		if(myMinMCNumberBkg < 0 || treeBkg->GetEntries() < myMinMCNumberBkg)
			myMinMCNumberBkg = treeBkg->GetEntries();

		outFileSig->cd();
		treeSig->Write();
		outFileSig->Close();
		
		outFileBkg->cd();
		treeBkg->Write();
		outFileBkg->Close();

		proc->Close();
	}
	
	delete myReader;
}

void PAnalysis::WriteLog(TString output){
	if(output == "")
		output = myConfig->GetOutputDir()+"/"+myConfig->GetLogName();
	#ifdef P_LOG
		cout << "Writing cut efficiencies to " << output << ".\n";
	#endif
	if(mySigEff == 0){
		cerr << "The cut efficiencies have to be computed first. Attempting to call BkgEffWP().\n";
		BkgEffWP();
	}
	ofstream logFile;
	logFile.open(output);
	logFile << mySigEff << endl << myBkgEff << endl;
	if(myMinMCNumberSig >= 0)
		logFile << myMinMCNumberSig << endl;
	if(myMinMCNumberBkg >= 0)
		logFile << myMinMCNumberBkg;
	logFile.close();
}	

double PAnalysis::GetBkgEff(void) const{
	return myBkgEff;
}

double PAnalysis::GetSigEff(void) const{
	return mySigEff;
}

PAnalysis::~PAnalysis(){
	#ifdef P_LOG
		cout << "Destroying PAnalysis " << myName << ".\n";
	#endif

	for(unsigned i=0; i<myProc.size(); i++)
		delete myProc.at(i);
	if(myStack)
		delete myStack;
	if(myCnvPlot)
		delete myCnvPlot;
	if(myLegend)
		delete myLegend;
	if(myCnvEff)
		delete myCnvEff;
	if(myROC)
		delete myROC;
	if(myLine)
		delete myLine;
	if(myCutLine)
		delete myCutLine;
	delete myOutputFile;
	if(myFactory)
		delete myFactory;
}

