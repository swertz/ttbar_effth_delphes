##### Code for a model-independent analysis ####

How to install:
 * Fork this repo and/or clone it: 
```
$ git clone https://github.com/(username)/ttbar_effth_delphes
```
 
 * Setup environment (works on both ingrid-ui1 and lxplus):
```
$ cd ttbar_effth_delphes/analyzer/
$ source init.sh
```

 * Build yaml-cpp: 
```
$ cd external 
$ source build_external.sh
$ cd ..
```

 * Build tmva:
```
$ make tvma -j8 
```


The code consists of:

1) plots: 
Quick and dirty code to produce not too ugly plots from config files (to be updated).

2) MG interference patches:
A collection of patches to
 * Get MadGraph to generate effective field theory events according to the interference between an operator and the SM amplitude.
 * Get MadWeight to compute weights according to the interference between an operator and the SM amplitude. See https://cp3.irmp.ucl.ac.be/projects/cp3admin/wiki/UsersPage/Physics/Exp/MEMforTopEffTh

3) analyzer:
 * tmva: A C++ program which reads a config file (see examples/tmva_standalone_example.yml), uses ROOT::TMVA to separate a signal from brackgrounds, and evaluates the resulting NN or BDT on all the processes defined, to separate them into signal-like or background-like samples. Usage: 
```
$ mkdir outdir_specified_in_config_file
$ ./tmva config_file.yml
```

 * python/driver.py: Builds a tree of "boxes" separating different processes according to a user-defined strategy. See examples/mischief_example.yml for more details. The strategy is defined by two functions implemented in a module passed to the driver (see python/treeStratgyMIS.py or python/treeStrategyOps.py for two examples). Usage: 
```
$ python/driver.py -c config_file.yml -t relative_path_to_tmva_executable -s strategyModule
```

 * python/replay.py: Evaluates a previously built tree of boxes on an additional process, using a config file (see examples/replay_example.yml). Usage:
```
$ python/replay.py config_file.yml
```

 * python/mcstudy.py: Do pseudo-experiments and fits on signal strengths. See examples/mcstudy_updated.conf and examples/template_fit_boxYields.yml. Usage:
```
$ python/mcstudy.py fit_config.conf
```

* python/readTree.py: Open pickle file and navigate in Tree object in an interactive python console. Some examples on how to find information in the Tree are printed out when loading a pickle file. To start looking a tree, do:
```
$ python -i python/readTree.py path_to_pickle_file
```
