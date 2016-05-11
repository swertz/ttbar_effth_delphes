#include <iostream>
#include <cstdlib>
#include <algorithm>

#include "panalysis.h"
#include "pconfig.h"

using namespace std;

int main(int argc, char **argv){

  PConfig* myConfig = 0;
  if(argc > 1)
    myConfig = new PConfig(argv[1]);
  else{
    cerr << "No config file specified!" << endl;
    exit(1);
  }

  PAnalysis* myAna = new PAnalysis(myConfig);

  myAna->BuildDiscriminant();
  
  if( contains(myConfig->GetWriteOptions(), "plot") || contains(myConfig->GetWriteOptions(), "hist") )
    myAna->DoHist();
  
  if( contains(myConfig->GetWriteOptions(), "plot") )
    myAna->DoPlot();
  
  if( contains(myConfig->GetWriteOptions(), "ROC") )
    myAna->DoROC();

  if( myConfig->GetSplitMode() == "SoverB" || myConfig->GetSplitMode() == "SoverSqrtB" || myConfig->GetSplitMode() == "SoverSqrtSB" )
    myAna->WPFromFigureOfMerit();
  else if( myConfig->GetSplitMode() == "fixedSigEff" )  
    myAna->BkgEffWPPrecise();
  else{
    cerr << "No splitmode specified!" << endl;
    exit(1);
  }
  
  if( contains(myConfig->GetOutputTasks(), "output") )
    myAna->WriteOutput();

  if( contains(myConfig->GetOutputTasks(), "split") )
    myAna->WriteSplitRootFiles();

  if( contains(myConfig->GetOutputTasks(), "result") )
    myAna->WriteResult();

  delete myAna; myAna = NULL;
  delete myConfig; myConfig = NULL;
  
  return 0;
}

