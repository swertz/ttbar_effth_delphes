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
  myEvalOnTrained = false;
  myBkgEff = 0;
  mySigEff = 0;
  
  myConfig = config;
  myName = myConfig->GetAnaName();
  myOutput = myConfig->GetOutputDir() + "/" + myConfig->GetOutputName();
  myMvaMethod = myConfig->GetMvaMethod();

  for(unsigned int i=0; i<myConfig->GetNProc(); i++)
    AddProc( (PProc*) new PProc(myConfig, i) );

  myOutputFile = (TFile*) new TFile(myOutput+".root", "RECREATE");
  if(!myOutputFile->IsOpen()){
    cerr << "Failure opening file " << myOutput+".root" << ".\n";
    exit(1);
  }

  myStack = NULL;
  myFactory = NULL;
  myCnvTraining = NULL;
  myCnvPlot = NULL;
  myLegend = NULL;
  myCnvEff = NULL;
  myROC = NULL;
  myLine = NULL;
  myCutLine = NULL;
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

void PAnalysis::DefineAndTrainFactory(void){
  if(mySig < 0 || !myBkgs.size()){
    cerr << "Cannot compute input weights: at least two processes (one signal and one background) have to be assigned to the analysis!" << endl;
    exit(1);
  }

  // Computing input weights
  // Note: not quite clear how TMVA computes the weights (how are they combined with the gen weight?)
  // HAS TO BE CHECKED

  // Defining Factory and MVA

  #ifdef P_LOG
    cout << "Initialising factory of type " << myMvaMethod;
    if(myMvaMethod == "MLP")
      cout << " and of topology " << myConfig->GetTopology() << ".\n";
    else
      cout << ".\n";
  #endif

  // Change MVA output file... Because myFactory::SetOutputDir() has been abducted by Aliens, do it a simpler way:
  TMVA::Tools::Instance();
  (TMVA::gConfig().GetIONames()).fWeightFileDir = myConfig->GetOutputDir();
  
  #ifdef P_LOG
    myFactory = (TMVA::Factory*) new TMVA::Factory(myName, myOutputFile, "!DrawProgressBar");
  #else
    myFactory = (TMVA::Factory*) new TMVA::Factory(myName, myOutputFile, "Silent:!DrawProgressBar");
  #endif

  // Open PProcs and define input trees
  
  OpenAllProc();
  
  myFactory->AddSignalTree(myProc.at(mySig)->GetTree(), myProc.at(mySig)->GetGlobWeight());
  for(unsigned int i=0; i<myBkgs.size(); i++)
    myFactory->AddBackgroundTree(myProc.at(myBkgs.at(i))->GetTree(), myProc.at(myBkgs.at(i))->GetGlobWeight());

  // Will also use weights defined in the input process dataset
  // Careful if these weights are negative!
  myFactory->SetWeightExpression(myConfig->GetCommonEvtWeight().c_str());

  for(unsigned int i=0; i<myConfig->GetNInputVars(); i++)
    myFactory->AddVariable(myConfig->GetInputVar(i));

  // Events: train/test/train/test/...
  // ? for each background tree or for all the brackgrounds together ?
  myFactory->PrepareTrainingAndTestTree(
    "", 
    "nTrain_Signal="+SSTR(myConfig->GetTrainEntries())
    +":nTrain_Background="+SSTR(myConfig->GetTrainEntries())
    +":nTest_Signal="+SSTR(myConfig->GetTrainEntries())
    +":nTest_Background="+SSTR(myConfig->GetTrainEntries())
    +":SplitMode=Alternate"
    +":NormMode=EqualNumEvents"
    );

  if(myMvaMethod == "MLP"){
    myFactory->BookMethod(
      TMVA::Types::kMLP, 
      myMvaMethod+"_"+myName, 
      TString("!H:V")
      +":NeuronType=tanh"
      +":VarTransform=Norm"
      +":IgnoreNegWeightsInTraining=True"
      +":NCycles="+SSTR(myConfig->GetIterations())
      +":HiddenLayers="+myConfig->GetTopology()
      +":TestRate=5"
      +":TrainingMethod=BFGS"
      +":SamplingTraining=False"
      +":ConvergenceTests=50"
      );
  }else if(myMvaMethod == "BDT"){
    myFactory->BookMethod(
      TMVA::Types::kBDT, 
      myMvaMethod+"_"+myName, 
      TString("!H:V")
      +":NTrees="+SSTR(myConfig->GetIterations())
      );
  }else{
    cerr << "Couldn't recognize MVA method.\n";
    exit(1);
  }

  // Training and stuff

  myFactory->TrainAllMethods();
  myFactory->TestAllMethods();
  myFactory->EvaluateAllMethods();

  CloseAllProc();
}

void PAnalysis::DoHist(void){
  #ifdef P_LOG
    cout << "Filling output histograms.\n";
  #endif
  
  if(!myFactory){
    cerr << "Cannot fill MVA output histograms without having defined and trained the factory! Attempting to call DefineAndTrainFactory().\n";
    DefineAndTrainFactory();
  }
  
  vector<float> inputs(myConfig->GetNInputVars());
  TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
  for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
    myReader->AddVariable(myConfig->GetInputVar(k), &inputs.at(k));
  myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");

  // Filling histograms

  for(unsigned int j=0; j<myProc.size(); j++){
    PProc* proc = (PProc*) myProc.at(j);
    proc->Open();

    for(long i=0; i<proc->GetTree()->GetEntries(); i++){
      // this would have to be discussed
      //if(proc->GetType() >= 0 && i%2==0 && i < 2*myConfig->GetTrainEntries() && !myEvalOnTrained)
      //  continue;
      
      proc->GetTree()->GetEntry(i);
      
      for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
        inputs.at(k) = (float) proc->GetInputVar(myConfig->GetInputVar(k));
      
      proc->GetHist()->Fill(Transform(myReader->EvaluateMVA(myName)), proc->GetEvtWeight()*proc->GetGlobWeight());
      proc->GetAbsHist()->Fill(Transform(myReader->EvaluateMVA(myName)), abs( proc->GetEvtWeight()*proc->GetGlobWeight() ) );
    }

    proc->GetHist()->SetLineWidth(3);
    proc->GetHist()->SetLineColor(proc->GetColor());
    proc->GetHist()->SetXTitle("MVA output");
    proc->GetHist()->SetStats(0);
    if(proc->GetType() < 0)
      proc->GetHist()->SetLineStyle(2);
    else
      proc->GetHist()->SetLineStyle(0);

    proc->GetAbsHist()->SetLineWidth(3);
    proc->GetAbsHist()->SetLineColor(proc->GetColor());
    proc->GetAbsHist()->SetXTitle("MVA output");
    proc->GetAbsHist()->SetStats(0);
    if(proc->GetType() < 0)
      proc->GetAbsHist()->SetLineStyle(2);
    else
      proc->GetAbsHist()->SetLineStyle(0);

    proc->Close();
  }
  
  delete myReader; myReader = NULL;
}

float PAnalysis::Transform(float input){
  // BDT output is between -1 and 1 => get it between 0 and 1, just as NN
  // And be sure all the output is between 0 and 1.

  float output;
  
  if(myMvaMethod == "BDT")
    output = (input + 1.)/2.;
  else
    output = input;
  
  if(output > 1)
    return 1;
  else if(output < 0)
    return 0;
  else
    return output;
}

void PAnalysis::DoPlot(void){
  #ifdef P_LOG
    cout << "Plotting output histograms.\n";
  #endif
  if(!myProc.at(0)->GetHist()->GetEntries()){
    cerr << "Cannot plot MVA output histograms without histograms! Attempting to call DoHist().\n";
    DoHist();
  }
  
  myCnvPlot = (TCanvas*) new TCanvas(myName+"_MVA output","MVA output");
  myLegend = new TLegend(0.73,0.7,0.89,0.89);
  myLegend->SetFillColor(0);
  myStack = (THStack*) new THStack("output_stack","MVA output");
  
  for(unsigned int j=0; j<myProc.size(); j++)
    myLegend->AddEntry(myProc.at(j)->GetHist(), myProc.at(j)->GetName().c_str(), "f");

  TH1D* tempSigHist = (TH1D*) myProc.at(mySig)->GetHist()->Rebin(myConfig->GetHistBins()/myConfig->GetPlotBins(),"rebinned");

  FillStack(tempSigHist->Integral());
  
  if(myStack->GetMaximum() > tempSigHist->GetMaximum()){
    myStack->Draw("hist");
    tempSigHist->Draw("same hist");
  }else{
    tempSigHist->Draw("hist");
    myStack->Draw("same hist");
  }

  myLegend->Draw();
}

void PAnalysis::FillStack(double integralSig){
  vector<PProc*> pointers;
  for(unsigned int i=0; i<myProc.size(); i++){
    if(myProc.at(i)->GetType() != 1)
      pointers.push_back(myProc.at(i));
  }
  
  sort(pointers.begin(), pointers.end(), &compareProc);

  double integralBkg = 0;
  for(unsigned int i=0; i<pointers.size(); i++)
    integralBkg += pointers.at(i)->GetHist()->Integral();
  
  for(unsigned int i=0; i<pointers.size(); i++){
    TH1D* tempHist = (TH1D*)pointers.at(i)->GetHist()->Rebin(myConfig->GetHistBins()/myConfig->GetPlotBins(), "rebinned_" + i);
    tempHist->Scale(integralSig/integralBkg);
    myStack->Add(tempHist);
  }
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
  double totS = myProc.at(mySig)->GetAbsHist()->Integral();
  
  double countBkg = 0, totBkg = 0;
  for(unsigned int i=0; i<myBkgs.size(); i++){
    countBkg += myProc.at(myBkgs.at(i))->GetHist()->Integral();
    totBkg += myProc.at(myBkgs.at(i))->GetAbsHist()->Integral();
  }
  
  unsigned int nBins = myConfig->GetHistBins();
  double sigEff[nBins+2];
  double bkgEff[nBins+2];

  for(unsigned int i=0; i<=nBins+1; i++){
    countS -= myProc.at(mySig)->GetHist()->GetBinContent(i);
    for(unsigned int j=0; j<myBkgs.size(); j++)
      countBkg -= myProc.at(myBkgs.at(j))->GetHist()->GetBinContent(i);
    sigEff[i] = abs(countS)/totS;
    bkgEff[i] = abs(countBkg)/totBkg;
  }

  //sigEff[0] = 1.;
  sigEff[nBins+1] = 0.;
  //bkgEff[0] = 1.;
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

// We will want to sort the (MVA,weight) vectors according to increasing MVA values
bool mvaOutputSorter(std::vector<float> i, std::vector<float> j){ return i[0] < j[0]; }

void PAnalysis::BkgEffWPPrecise(void){
  double workingPoint = myConfig->GetWorkingPoint();
  
  #ifdef P_LOG
    cout << "Computing precise cut for signal efficiency = " << workingPoint << "... " << endl;
  #endif
  
  if(!myFactory){
    cerr << "Cannot compute precise working point without having defined and trained the factory! Attempting to call DefineAndTrainFactory().\n";
    DefineAndTrainFactory();
  }
  
  if(workingPoint >= 1 || workingPoint <= 0){
    cerr << "Working point must be a double strictly between 0 and 1!\n";
    exit(1);
  }

  std::string condition = "";
  if(!myEvalOnTrained)
    condition = "!(Entry$%2==0 && Entry$ < " + std::to_string(2*myConfig->GetTrainEntries()) + ")";

  // We will evaluate the MVA on the signal, 
  // build a vector of (MVA output, weight), 
  // sort it according to increasing values of MVA output, 
  // and find the MVA cut value X such that abs(sum(weights|mva>=X))/sum(abs(weights)) = working point

  std::vector<float> inputs(myConfig->GetNInputVars());
  
  TMVA::Reader* myReader = (TMVA::Reader*) new TMVA::Reader("!V:Color");
  for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
    myReader->AddVariable(myConfig->GetInputVar(k), &inputs.at(k));
  myReader->BookMVA(myName, myConfig->GetOutputDir()+"/"+myName+"_"+myMvaMethod+"_"+myName+".weights.xml");

  // Fetching the signal
  PProc* sig = (PProc*) myProc.at(mySig);
  sig->Open();
  TTree* tree = sig->GetTree();
  float sigEffEntriesAbs = sig->GetEffEntriesAbs(condition);
  float sigEffEntries = sig->GetEffEntries(condition);
  
  if(workingPoint > abs(sigEffEntries)/sigEffEntriesAbs){
    cout << "Error in BkgEffWPPrecise(): not possible to achieve requested working point, since the maximum attainable efficiency \
given the negative event weights is " << abs(sigEffEntries)/sigEffEntriesAbs << "." << endl;
    exit(1);
  }

  std::vector< std::vector<float> > mvaOutput;

  for(uint64_t i=0; i < static_cast<uint64_t>(tree->GetEntries()); i++){
    if(!myEvalOnTrained && i%2==0 && i<myConfig->GetTrainEntries()*2)
      continue;

    tree->GetEntry(i);
    
    for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
      inputs.at(k) = (float) sig->GetInputVar(myConfig->GetInputVar(k));
    float mva = Transform(myReader->EvaluateMVA(myName));

    std::vector<float> outputAndWeight;

    outputAndWeight.push_back(mva);
    outputAndWeight.push_back((float)sig->GetEvtWeight());

    mvaOutput.push_back(outputAndWeight);
  }

  sort(mvaOutput.begin(), mvaOutput.end(), mvaOutputSorter);
  
  // the sort is in ascending MVA values, so we have to cut st. abs(sum(weights|mva>X))/sum(abs(weights)) = abs(sum(weights))/sum(abs(weights)) - working point
  int cutIndex = 0;
  float integral = 0.;
  for(unsigned int i = 0; i < mvaOutput.size(); ++i){
    if( (abs(sigEffEntries) - abs(integral) )/sigEffEntriesAbs <= workingPoint)
      break;
    
    integral += mvaOutput[i][1];
    cutIndex++;
  }

  mySigEff = (abs(sigEffEntries) - abs(integral))/sigEffEntriesAbs;

  // just a security in the limiting case of workingPoint = 0.
  if(cutIndex == tree->GetEntries())
    myCut = (double) (*mvaOutput.end())[0] + 1.;
  else
    myCut = (double) mvaOutput[cutIndex][0];

  sig->Close();
  
  if(abs(mySigEff - workingPoint)/workingPoint > 0.1){
    cout << "Error in BkgEffWPPrecise(): computed signal efficiency is more than 10% off from the requested working point." << endl;
    exit(1);
  }

  
  // Draw cut line on plot canvas, if it exists
  if(myCnvPlot){
    myCnvPlot->cd();
    myCutLine = (TLine*) new TLine(myCut, min(myStack->GetMinimum(), sig->GetHist()->GetMinimum()), myCut, max(myStack->GetMaximum(), sig->GetHist()->GetMaximum()));
    myCutLine->SetLineWidth(3);
    myCutLine->Draw();
  }

  // Compute background efficiency using this cut:
  
  double bkgSelectedYield = 0.;
  double bkgTotYieldAbs = 0.;
  
  for(unsigned int j=0; j<myBkgs.size(); j++){
    PProc* proc = (PProc*) myProc.at(myBkgs.at(j));

    proc->Open();

    double integral = 0;

    for(uint64_t i=0; i < static_cast<uint64_t>(proc->GetTree()->GetEntries()); i++){
      if(!myEvalOnTrained && i%2==0 && i<myConfig->GetTrainEntries()*2)
        continue;
      
      proc->GetTree()->GetEntry(i);
      
      for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
        inputs.at(k) = (float) proc->GetInputVar(myConfig->GetInputVar(k));
      
      if(Transform(myReader->EvaluateMVA(myName)) >= myCut)
        integral += proc->GetEvtWeight();
    }

    bkgSelectedYield += proc->GetGlobWeight() * integral;
    bkgTotYieldAbs += proc->GetYieldAbs(condition);

    proc->Close();
  }

  myBkgEff = abs(bkgSelectedYield)/bkgTotYieldAbs;
  
  delete myReader; myReader = NULL;
  
  if(mySigEff*myBkgEff == 0.){
    cout << "Error in BkgEffWPPrecise(): found cut value which rejects all the data!" << endl;
    exit(1);
  }
  
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
    cout << "  S/B = " << sB << endl;
    cout << "  S/sqrt(B) = " << sRootB << ": signal=" << bestSRBsig << ", background=" << bestSRBbkg << endl;
    cout << "  S/sqrt(S+B) = " << sRootSB << endl;
  #endif
}*/

void PAnalysis::WriteOutput(void){
  #ifdef P_LOG
    cout << "Writing output to " << myOutput << ".root.\n"; 
  #endif
  
  const std::vector<std::string>& options = myConfig->GetWriteOptions();

  myOutputFile->cd();
  
  if(myCnvEff && contains(options, "ROC"))
    myCnvEff->Write("ROC");
  
  if(myCnvPlot && contains(options, "plot"))
    myCnvPlot->Write("Plot");

  if(myProc.at(0)->GetHist()->GetEntries() && contains(options, "hist")) {
    for(unsigned int i=0; i<myProc.size(); i++){
      myProc.at(i)->GetHist()->Write();
      myProc.at(i)->GetAbsHist()->Write();
    }
  }
  
  if(myROC && contains(options, "ROC"))
    myROC->Write("ROC curve");
}

void PAnalysis::WriteSplitRootFiles(void){
  #ifdef P_LOG
    cout << "Splitting root files and writing output files.\n"; 
  #endif
  
  if(!myCut){
    cerr << "Cannot write split root files without knowing the cut value! Attempting to call BkgEffWPPrecise().\n";
    BkgEffWPPrecise();
  }
  
  TString outputDir = myConfig->GetOutputDir();
   
  // While double-type inputs are OK for TMVA training, evaluation requires float
  // See http://sourceforge.net/p/tmva/mailman/message/33528693/ (no further answer received)
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
    
    if(!outFileSig->IsOpen() || !outFileBkg->IsOpen()){
      cerr << "Error creating split output files.\n";
      exit(1);
    }
  
    // Adding this MVA's output to the output trees
    float mvaOutput;
    TString outBranchName = "MVAOUT__" + outputDir + "/" + myName;
    outBranchName.ReplaceAll("//","__");
    outBranchName.ReplaceAll("/","__");
    treeSig->Branch(outBranchName, &mvaOutput, outBranchName + "/F");
    treeBkg->Branch(outBranchName, &mvaOutput, outBranchName + "/F");
    
    for(long i=0; i<proc->GetTree()->GetEntries(); i++){
      proc->GetTree()->GetEntry(i);
      for(unsigned int k=0; k<myConfig->GetNInputVars(); k++)
        inputs.at(k) = (float) proc->GetInputVar(myConfig->GetInputVar(k));
      mvaOutput = Transform(myReader->EvaluateMVA(myName));
      if(mvaOutput < myCut)
        treeBkg->Fill();
      else
        treeSig->Fill();
    }

    outFileSig->cd();
    treeSig->Write();
    outFileSig->Close();
    
    outFileBkg->cd();
    treeBkg->Write();
    outFileBkg->Close();

    proc->Close();
  }
  
  delete myReader; myReader = NULL;
}

void PAnalysis::WriteResult(void){
  TString output = myConfig->GetOutputDir()+"/"+myConfig->GetLogName();
  
  #ifdef P_LOG
    cout << "Writing cut efficiencies to " << output << ".\n";
  #endif
  
  if(mySigEff == 0){
    cerr << "The cut efficiencies have to be computed first. Attempting to call BkgEffWPPrecise().\n";
    BkgEffWPPrecise();
  }
  
  ofstream logFile;
  logFile.open(output);
  logFile << mySigEff << endl << myBkgEff << endl << myCut;
  logFile.close();
}  

PAnalysis::~PAnalysis(){
  #ifdef P_LOG
    cout << "Destroying PAnalysis " << myName << ".\n";
  #endif

  for(unsigned i=0; i<myProc.size(); i++){
    delete myProc.at(i); myProc.at(i) = NULL;
  }
  delete myStack; myStack = NULL;
  delete myCnvPlot; myCnvPlot = NULL;
  delete myLegend; myLegend = NULL;
  delete myCnvEff; myCnvEff = NULL;
  delete myROC; myROC = NULL;
  delete myLine; myLine = NULL;
  delete myCutLine; myCutLine = NULL;
  delete myOutputFile; myOutputFile = NULL;
  delete myFactory; myFactory = NULL;
}

