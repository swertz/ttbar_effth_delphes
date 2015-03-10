##### Code for a model-independent analysis ####

The code consists of:

1) plots: 
Quick and dirty code to produce not too ugly plots from config files.

2) MG interference patches:
A collection of patches to
 * Get MadGraph to generate effective field theory events according to the interference between an operator and the SM amplitude.
 * Get MadWeight to compute weights according to the interference between an operator and the SM amplitude. See https://cp3.irmp.ucl.ac.be/projects/cp3admin/wiki/UsersPage/Physics/Exp/MEMforTopEffTh

3) analyzer:
 * tmva: A C++ program which reads a config file (see examples/tmva_standalone_example.conf), uses ROOT::TMVA to separate a signal from brackgrounds, and evaluates the resulting NN or BDT on all the processes defined, to separate them into signal-like or background-like samples. Usage: 
```
$ make tmva
$ mkdir outdir_specified_in_config_file
$ ./tmva examples/config_file.conf
```

 * python/driver.py: Builds a tree of "boxes" separating different processes according to a user-defined strategy. See examples/mischief_example.conf for more details. Usage: 
```
$ python/driver.py config_file.conf relative_path_to_tmva_executable
```
