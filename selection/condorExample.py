#!/nfs/soft/python/python-2.7.5-sl6_amd64_gcc44/bin/python

## Example usage of condorTools
## Run `python condorExample.py`

from condorTools import condorSubmitter

submitters = []

#submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph5/TTbar_2j_sm_5f_MSdecay_0", baseDir = "TTbar_qCut50", usedMadSpin = True) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_OtG_NPsq2_QED1_MSdecay", baseDir = "OtG_qCut50", usedMadSpin = True) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_OG_NPleq2_QED1_MEdecay", baseDir = "OG_qCut50_1", usedMadSpin = False) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_OphiG_NPleq2_QED1_MEdecay", baseDir = "OphiG_qCut50", usedMadSpin = False) )
##submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_O13qq_NPleq2_QED1_MEdecay", baseDir = "O13qq", usedMadSpin = False) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_O8dt_NPleq2_QED1_MEdecay", baseDir = "O8dt_qCut50", usedMadSpin = False) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/sbrochet/scratch/EffOperators/Madgraph/MG5_aMC_v2_3_3/TTbar_2j_TopEffTh_O8ut_NPleq2_QED1_MEdecay", baseDir = "O8ut_qCut50", usedMadSpin = False) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/sbrochet/scratch/EffOperators/Madgraph/MG5_aMC_v2_3_3/TTbar_2j_TopEffTh_O83qq_NPleq2_QED1_MEdecay", baseDir = "O83qq_qCut50_1", usedMadSpin = False) )
#submitters.append( condorSubmitter(MGdir = "/home/fynu/sbrochet/scratch/EffOperators/Madgraph/MG5_aMC_v2_3_3/TTbar_2j_TopEffTh_O81qq_NPleq2_QED1_MEdecay", baseDir = "O81qq_qCut50", usedMadSpin = False) )


submitters.append( condorSubmitter(MGdir = "/home/fynu/swertz/scratch/Madgraph/madgraph5/pp_tth_fullyLept_hInv/", baseDir = "ttH_H_inv", usedMadSpin = False) )

for sub in submitters:

    ## Create test_condor directory and subdirs
    sub.setupCondorDirs()

    ## Write command and data files in the condor directory
    sub.createCondorFiles()

    ## Actually submit the jobs
    ## It is recommended to do a dry-run first without submitting to condor
    sub.submitOnCondor()
