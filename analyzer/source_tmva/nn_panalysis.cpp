#include <cstdlib> // for exit() function
#include <iostream>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <TMVA/Reader.h>
#include <TMVA/Tools.h>
#include <TMVA/Config.h>
#include "nn_panalysis.h"

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

	for(unsigned int i=0; i<config->GetNData(); i++){
		PData *tempData = new PData(config, i);
		AddData(tempData);
	}
}

void PAnalysis::AddData(PData* data){
	#ifdef P_LOG
		cout << "Adding data " << data->GetName() << " to analysis " << myName << "." << endl;
	#endif

	myData.push_back(data);
	switch(data->GetType()){
		case 0:
			myBkgs.push_back(myData.size()-1);
			break;
		case 1:
			if(mySig >= 0){
				cerr << "Only one signal can be assigned to the analysis!" << endl;
				exit(1);
			}
			mySig = myData.size()-1;
			break;
		default:
			break;
	}
}

void PAnalysis::OpenAllData(void){
	for(unsigned int i=0; i<myData.size(); i++)
		myData.at(i)->Open();
}

void PAnalysis::CloseAllData(void){
	for(unsigned int i=0; i<myData.size(); i++)
		myData.at(i)->Close();
}

void PAnalysis::DefineAndTrainFactory(unsigned int iterations, TString method, TString topo){
	if(mySig < 0 || !myBkgs.size()){
		cerr << "Cannot compute input weights: at least two datasets (one signal and one background) have to be assigned to the analysis!" << endl;
		exit(1);
	}

	OpenAllData();

	// Computing input weights
	// Note: not quite clear how TMVA computes the weights (how are they combined with the gen weight?)
	//		... should be OK to pass as input weight xsection*eff*lumi/nSelected for each dataset

	for(unsigned int i=0; i<myData.size(); i++){
		double xS = myData.at(i)->GetXSection();
		double eff = myData.at(i)->GetEfficiency();
		double nSel = myData.at(i)->GetTree()->GetEntries();
		double lumi = myConfig->GetLumi(); 
		myData.at(i)->SetInputReweight(xS*eff*lumi/nSel);
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
	myFactory->AddSignalTree(myData.at(mySig)->GetTree(), myData.at(mySig)->GetInputReweight());
	for(unsigned int i=0; i<myBkgs.size(); i++)
		myFactory->AddBackgroundTree(myData.at(myBkgs.at(i))->GetTree(), myData.at(myBkgs.at(i))->GetInputReweight());

	// Will also use weights defined in the input datasets
	// Careful if these weights are negative!
	if(myConfig->GetGenWeight() != "")
		myFactory->SetWeightExpression(myConfig->GetGenWeight());

	for(unsigned int i=0; i<myConfig->GetNWeights(); i++)
		myFactory->AddVariable(myConfig->GetWeight(i));

	// Events: train/test/train/test/...
	// ? for each background tree or for all the brackgrounds together ?
	myFactory->PrepareTrainingAndTestTree("", "nTrain_Signal="+SSTR(myConfig->GetTrainEntries())+":nTrain_Background="+SSTR(myConfig->GetTrainEntries())+":nTest_Signal="+SSTR(myConfig->GetTrainEntries())+":nTest_Background="+SSTR(myConfig->GetTrainEntries())+":SplitMode=Alternate");

	// to do: specify structure, help, verbosity,
	
	if(method == "MLP")
		myFactory->BookMethod(TMVA::Types::kMLP, method+"_"+myName, "!H:V:NeuronType=sigmoid:VarTransform=Norm:IgnoreNegWeightsInTraining=True:NCycles="+SSTR(iterations)+":HiddenLayers="+topo+":TestRate=5:TrainingMethod=BFGS:SamplingTraining=False:Tau=15:ConvergenceTests=50:ResetStep=15");
	else if(method == "TMLP")
		myFactory->BookMethod(TMVA::Types::kTMlpANN, method+"_"+myName, "!H:V:VarTransform=Norm:NCycles="+SSTR(iterations)+":HiddenLayers="+topo+":LearningMethod=BFGS");
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

	CloseAllData();
}

void PAnalysis::DoHist(bool evalOnTrained){
	#ifdef P_LOG
		cout << "Filling output histograms.\n";
	#endif
	if(!myFactory){
		cerr << "Cannot draw NN output histograms without having defined and trained the factory! Attemping to call DefineAndTrainFactory().\n";
		DefineAndTrainFactory();
	}

	OpenAllData();

	// Computing event reweighting for the histograms

	double expBkg = 0;
	for(unsigned int i=0; i<myData.size(); i++){
		if(myData.at(i)->GetType() != 1){
			double xS = myData.at(i)->GetXSection();
			double eff = myData.at(i)->GetEfficiency();
			expBkg += xS*eff;
		}
	}
	double entriesSig;
	if(evalOnTrained)
		entriesSig = myData.at(mySig)->GetTree()->GetEntries();
	else
		entriesSig = max(floor(myData.at(mySig)->GetTree()->GetEntries()/2), myData.at(mySig)->GetTree()->GetEntries() - myConfig->GetTrainEntries());

	for(unsigned int i=0; i<myData.size(); i++){
		if(myData.at(i)->GetType() != 1){
			double xS = myData.at(i)->GetXSection();
			double eff = myData.at(i)->GetEfficiency();
			double entriesBkg = myData.at(i)->GetTree()->GetEntries();
			if(!evalOnTrained && myData.at(i)->GetType() == 0)
				entriesBkg = max(floor(myData.at(i)->GetTree()->GetEntries()/2), myData.at(i)->GetTree()->GetEntries() - myConfig->GetTrainEntries());
			myData.at(i)->SetHistReweight(xS*eff/entriesBkg);
		}
	}
	myData.at(mySig)->SetHistReweight(expBkg/entriesSig);

	// Filling histograms

	vector<float> inputs(myConfig->GetNWeights());

	for(unsigned int j=0; j<myData.size(); j++){
		PData* data = (PData*) myData.at(j);

		TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
		for(unsigned int k=0; k<myConfig->GetNWeights(); k++){
			myReader->AddVariable(myConfig->GetWeight(k), &inputs.at(k));
		}
		myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");
		
		for(long i=0; i<data->GetTree()->GetEntries(); i++){
			if(data->GetType() >= 0 && i%2==0 && i < 2*myConfig->GetTrainEntries() && !evalOnTrained)
				continue;
			data->GetTree()->GetEntry(i);
			for(unsigned int k=0; k<myConfig->GetNWeights(); k++)
				inputs.at(k) = (float) *data->GetHyp(myConfig->GetWeight(k));
			data->GetHist()->Fill(Transform(myMvaMethod, myReader->EvaluateMVA(myName)), data->GetHistReweight());
		}
		
		data->GetHist()->SetLineWidth(3);
		data->GetHist()->SetLineColor(data->GetColor());
		data->GetHist()->SetXTitle("MVA output");
		data->GetHist()->SetStats(0);
		if(data->GetType() == -1)
			data->GetHist()->SetLineStyle(2);
		else
			data->GetHist()->SetLineStyle(0);

		delete myReader;
	}

	CloseAllData();
}

double PAnalysis::Transform(TString method, double input){
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
	if(!myData.at(0)->GetHist()->GetEntries()){
		cerr << "Cannot plot MVA output histograms without histograms! Attemping to call DoHist().\n";
		DoHist();
	}
	
	myCnvPlot = (TCanvas*) new TCanvas(myName+"_MVA output","MVA output");
	myLegend = new TLegend(0.73,0.7,0.89,0.89);
	myLegend->SetFillColor(0);
	myStack = (THStack*) new THStack("output_stack","MVA output");
	
	for(unsigned int j=0; j<myData.size(); j++)
		myLegend->AddEntry(myData.at(j)->GetHist(), myData.at(j)->GetName(), "f");
	FillStack();

	TH1D* tempSigHist = (TH1D*) myData.at(mySig)->GetHist()->Rebin(myConfig->GetHistBins()/myConfig->GetPlotBins(),"rebinned");

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
	vector<PData*> pointers;
	for(unsigned int i=0; i<myData.size(); i++){
		if(myData.at(i)->GetType() != 1)
			pointers.push_back(myData.at(i));
	}
	sort(pointers.begin(), pointers.end(), &compareData);
	for(unsigned int i=0; i<pointers.size(); i++)
		myStack->Add(pointers.at(i)->GetHist()->Rebin(myConfig->GetHistBins()/myConfig->GetPlotBins(),"rebinned"));
}

void PAnalysis::DoROC(void){
	#ifdef P_LOG
		cout << "Drawing ROC curve.\n";
	#endif
	if(mySig<0 || !myBkgs.size()){
		cerr << "Cannot draw ROC curve without signal and background data!\n";
		exit(1);
	}else if(!myData.at(0)->GetHist()->GetEntries()){
		cerr << "Cannot draw ROC curve without data histograms! Attempting to call DoHist().\n";
		DoHist();
	}
	
	double countS = myData.at(mySig)->GetHist()->Integral();
	double totS = countS;
	double countBkg = 0;
	unsigned int nBins = myConfig->GetHistBins();
	for(unsigned int i=0; i<myBkgs.size(); i++)
		countBkg += myData.at(myBkgs.at(i))->GetHist()->Integral();
	double totBkg = countBkg;
	double sigEff[nBins+2];
	double bkgEff[nBins+2];

	for(unsigned int i=0; i<=nBins+1; i++){
		countS -= (double)myData.at(mySig)->GetHist()->GetBinContent(i);
		for(unsigned int j=0; j<myBkgs.size(); j++)
			countBkg -= (double)myData.at(myBkgs.at(j))->GetHist()->GetBinContent(i);
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
				myCut = myData.at(mySig)->GetHist()->GetXaxis()->GetBinLowEdge(i-1);
				break;
			}else{
				myBkgEff = bkgEff[i];
				mySigEff = sigEff[i];
				myCut = myData.at(mySig)->GetHist()->GetXaxis()->GetBinLowEdge(i);
				break;
			}
		}
	}
	if(myCut == 0){
		cerr << "Error finding cut for specified working point.\n";
		exit(1);
	}

	myCnvPlot->cd();
	myCutLine = (TLine*) new TLine(myCut,0,myCut,max(myStack->GetMaximum(), myData.at(mySig)->GetHist()->GetMaximum()));
	myCutLine->SetLineWidth(3);
	myCutLine->Draw();

	#ifdef P_LOG
		cout << "Found background efficiency = " << myBkgEff << " and signal efficiency = " << mySigEff << " at cut = " << myCut << ".\n";
	#endif
}

/*void PAnalysis::FiguresOfMerit(void){
	#ifdef P_LOG
		cout << "Computing figures of merit." << endl;
	#endif
	if(mySig<0 || !myBkgs.size()){
		cerr << "Cannot compute figures of merit without signal and background data!\n";
		exit(1);
	}else if(!myData.at(0)->GetHist()->GetEntries()){
		cerr << "Cannot compute figures of merit without data histograms! Attempting to call DoOutHist().\n";
		DoOutHist();
	}

	double totS = myData.at(mySig)->GetHist()->Integral();
	double totBkg = 0;
	for(unsigned int i=0; i<myBkgs.size(); i++)
		totBkg += myData.at(myBkgs.at(i))->GetHist()->Integral();
	double expBkg = myConfig->GetLumi()*totBkg;
	double expSig = myConfig->GetLumi()*myData.at(mySig)->GetXSection()*myData.at(mySig)->GetEfficiency();
	double tempSB, tempSRootB, tempSRootSB;
	double bestSRBsig = 0, bestSRBbkg = 0;

	for(int i=0; i<=P_NBINS+1; i++){
		expSig -= myConfig->GetLumi()*myData.at(mySig)->GetXSection()*myData.at(mySig)->GetEfficiency()*(double)myData.at(mySig)->GetHist()->GetBinContent(i)/totS;
		for(unsigned int j=0; j<myBkgs.size(); j++)
			expBkg -= myConfig->GetLumi()*(double)myData.at(myBkgs.at(j))->GetHist()->GetBinContent(i);

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
	if(myData.at(0)->GetHist()->GetEntries() && options.Contains("hist")){
		myData.at(mySig)->GetHist()->Scale(myData.at(mySig)->GetXSection()*myData.at(mySig)->GetEfficiency()/myData.at(mySig)->GetHist()->Integral());
		for(unsigned int i=0; i<myData.size(); i++){
			myData.at(i)->GetHist()->Scale(myConfig->GetLumi());
			myData.at(i)->GetHist()->Write();
		}
	}
	if(myROC && options.Contains("ROC"))
		myROC->Write("ROC curve");
}

void PAnalysis::WriteSplitData(TString outputDir){
	if(outputDir == "")
		outputDir = myConfig->GetOutputDir();
	#ifdef P_LOG
		cout << "Splitting data and writing output files.\n"; 
	#endif
	if(!myCut){
		cerr << "Cannot write split data without knowing the cut value! Attempting to call BkgEffWP().\n";
		BkgEffWP();
	}

	for(unsigned int j=0; j<myData.size(); j++){
		PData* data = (PData*) myData.at(j);

		data->Open();

		TFile* outFileSig = new TFile(outputDir + "/" + myName + "_siglike_data_" + data->GetName() + ".root","RECREATE");
		TTree* treeSig = data->GetTree()->CloneTree(0);
		
		TFile* outFileBkg = new TFile(outputDir + "/" + myName + "_bkglike_data_" + data->GetName() + ".root","RECREATE");
		TTree* treeBkg = data->GetTree()->CloneTree(0);
		
		if(outFileSig->IsZombie() || outFileBkg->IsZombie()){
			cerr << "Error creating split output files.\n";
			exit(1);
		}
		
		vector<float> inputs(myConfig->GetNWeights());
		TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
		for(unsigned int k=0; k<myConfig->GetNWeights(); k++)
			myReader->AddVariable(myConfig->GetWeight(k), &inputs.at(k));
		myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");
		
		for(long i=0; i<data->GetTree()->GetEntries(); i++){
			data->GetTree()->GetEntry(i);
			for(unsigned int k=0; k<myConfig->GetNWeights(); k++)
				inputs.at(k) = (float) *data->GetHyp(myConfig->GetWeight(k));
			if(Transform(myMvaMethod, myReader->EvaluateMVA(myName)) < myCut)
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

		delete myReader;
		data->Close();
	}
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

	for(unsigned i=0; i<myData.size(); i++)
		delete myData.at(i);
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

