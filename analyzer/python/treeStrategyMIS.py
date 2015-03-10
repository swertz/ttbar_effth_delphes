# Not to be used as standalone file

def defineNewCfgs(cfg):
	""" Create specific tmva configuration object and return a list with all the configurations.
	Each of them will be used to launch a thread. The analysis tree, locks and level are also passed, in case they are needed."""
	
	configs = []

	# ...

	return configs



def analyseResults(cfg, results, locks, tree, level):
	""" Based on the current config and the list of results=[(sigEff,bkgEff,minMCEventsSigLike,minMCEventsBkgLike,config),...], decide what to do next. 
	The results are sorted according to decreasing sigEff/bkgEff values.
	Failed tmva calls are not included in the result list => have to be investigated separately.
	Analysis tree, locks and level might be used. 
	Function returns a list of configs which have been adapted from the current config and the results. Each of these will be passed to a new tryMisChief instance, to get to the next node. 
	If the list is empty, this branch is simply stopped (with no other action taken... be sure to everything you need to do here. """

	configs = []
	
	# ...
	
	return configs
