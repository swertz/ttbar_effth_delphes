# Not to be used as standalone file

from treeStructure import MISAnalysis
from treeStructure import MISBox 

def defineNewCfgs(box, locks):
	""" Create specific tmva configuration object and define a list with all the configurations.
	Each of them will be used to launch a thread. The list is stored in box.MVA."""

	# Define "config" for new MVA, then:
	newMVA = MISAnalysis(box, config)
	box.MVA.append(newMVA)


def analyseResults(box, locks):
	""" Based on the current box and the results stored in box.MVA, decide what to do next. 
	Failed tmva calls have box.MVA.result=None => careful!.
	This function defines box.daughters[] with configs which have been adapted from the current config and the results. Each of these will be passed to a new tryMisChief instance, to get to the next node. 
	If the list is empty, or if all the daughter boxes have isEnd=True, this branch is simply stopped (with no other action taken... be sure to do everything you need to do here). """

	# Define "config" for next step (e.g. sig-like branch of current box), then:
	sigBox = MISBox(box, config) # "sigBox" will be a daughter of "box", and "box" the parent of "sigBox"
	box.goodMVA = aChosenMISAnalysis object # Keep track of the MVA chosen to define the sig- and bkg-like subsets
	box.goodMVA.sigLike = sigBox # Keep track that the sig-like subset of this MVA is the box we have just defined
	sigBox.isEnd = True # If we want to stop here
	

if __name__ == "__main__":
	print "Do not run on this file."
