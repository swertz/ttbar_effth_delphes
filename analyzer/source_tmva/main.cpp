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

  myAna->DefineAndTrainFactory();
  myAna->DoHist();
  myAna->DoPlot();
  myAna->DoROC();
  myAna->BkgEffWPPrecise();
  
  if(contains(myConfig->GetOutputTasks(), "output"))
    myAna->WriteOutput();

  if(contains(myConfig->GetOutputTasks(), "split"))
    myAna->WriteSplitRootFiles();

  if(contains(myConfig->GetOutputTasks(), "result"))
    myAna->WriteResult();

  delete myAna;
  delete myConfig;
  
  return 0;
}

