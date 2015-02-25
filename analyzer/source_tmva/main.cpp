#include <iostream>
#include <cstdlib>

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
	myAna->BkgEffWP();
	if(myConfig->GetOutputTasks().Contains("results"))
		myAna->WriteOutput();
	if(myConfig->GetOutputTasks().Contains("split"))
		myAna->WriteSplitData();
	if(myConfig->GetOutputTasks().Contains("log"))
		myAna->WriteLog();

	delete myAna;
	delete myConfig;
	
	return 0;
}

