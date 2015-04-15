# Not to be used as standalone file

from treeStructure import MISAnalysis
from treeStructure import MISBox 

def defineNewCfgs(box, locks):
    """ Create specific tmva configuration objects ("PConfig") based on the current "box.cfg".
    Use them to create MVA objects ("MISAnalysis"), which are then stored in "box.MVA".
    Each of them will be used to launch a thread.."""

    newMVA = MISAnalysis(box, config)
    box.MVA.append(newMVA)


def analyseResults(box, locks):
    """ Based on the current box and the results stored in "box.MVA", decide what to do next. 
    Failed tmva calls have "box.MVA.result=None" => careful!.
    This function defines "box.daughters[]" by building new boxes using configs which have been adapted from the current config ("box.cfg") and the results of the "box.MVA"'s. 
    Each new box not marked as "isEnd=True" will be passed to a new "tryMisChief" instance, to get to the next level of the tree.
    If the list is empty, or if all the daughter boxes have "isEnd=True", this branch is simply stopped (with no other action taken... be sure to do everything you need to do here). """

    box.goodMVA = aChosenMISAnalysis # Keep track of the MVA chosen to define the new sig- and bkg-like subsets. This must be specified before building a daughter box (otherwise the daughter box will not know how she was conceived, poor thing...)
    box.goodMVA.sigLike = sigBox # Keep track that the sig-like subset of this MVA is the box we have just defined
    # Define "config" for next step (e.g. sig-like branch of current box), then:
    sigBox = MISBox(parent = box, cfg = config, type = "sig") # "sigBox" will be a daughter of "box", and "box" the parent of "sigBox"
    sigBox.isEnd = True # If we want to stop here (usually, when stopping, we have NO goodMVA)
    

if __name__ == "__main__":
    print "Do not run on this file."
