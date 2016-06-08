#!/bin/bash

# Setup our environment
#module load pheno/pheno_gcc49

#pushd /home/fynu/swertz/scratch/CMSSW_7_4_15/src/
#source /cvmfs/cms.cern.ch/cmsset_default.sh
#eval `scram runtime --sh`
#popd
#
#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/

cms_card_path=/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/cards/delphes_card_CMS_PileUp.tcl
delphes_path=/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/DelphesSTDHEP
#delphes_cms_path=/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/DelphesCMSFWLite
#delphes_pythia_cmd=/home/fynu/swertz/storage/Delphes/condorDelphes/myPythiaCmd.cmnd

selectionner=/home/fynu/swertz/ttbar_effth_delphes/selection/preselection_llbbX

mg_event_dir=#MG_EVENT_DIR#


cp ${mg_event_dir}/#LHE_INPUT_FILE# .
lhe_input_file=$(basename #LHE_INPUT_FILE# .gz)
gunzip ${lhe_input_file}.gz

#lhe_input_file=${mg_event_dir}/$(basename #LHE_INPUT_FILE# .gz)
#if [ ! -e ${lhe_input_file} ]; then
#  echo "Decompressing LHE file."
#  gunzip ${lhe_input_file}.gz
#fi

# CMS PART

fragment=Configuration/Generator/python/Hadronizer_TuneCUETP8M1_13TeV_MLM_5f_max2j_qCut50_LHE_pythia8_cff.py
cms_fileout=output_pythia8_#JOB_ID#.root

cmsDriver.py ${fragment} -s GEN --mc --conditions auto:mc --filein file:${lhe_input_file} --datatier 'GEN-SIM-RAW' --eventcontent RAWSIM --filetype LHE -n 50000 --fileout ${cms_fileout}

# DELPHES PART

${delphes_cms_path} ${cms_card_path} output_delphes_#JOB_ID#.root output_pythia8_#JOB_ID#.root
${delphes_cms_path} ${cms_card_path} output_delphes_#JOB_ID#.root #OUTDIR_PATH#/output_pythia8_#JOB_ID#.root

# SELECTION PART

module purge
module load pheno/pheno_gcc49
${selectionner} output_delphes_#JOB_ID#.root output_selected_#JOB_ID#.root

# FINALIZE

mv output_pythia8_#JOB_ID#.root #OUTDIR_PATH#/
mv output_delphes_#JOB_ID#.root #OUTDIR_PATH#/
mv output_selected_#JOB_ID#.root #OUTDIR_PATH#/

#cp ${delphes_pythia_cmd} pythia8.cmnd
## Use columns for sed because of the '/' in the path
#sed -i "s:input_file:${lhe_input_file}:g" pythia8.cmnd
#
#
#${delphes_pythia8_path} ${cms_card_path} pythia8.cmnd output_pythia_#JOB_ID#.root
#mv output_pythia_#JOB_ID#.root #OUTDIR_PATH#/

#if [ ! -e ${lhe_input_file}.gz ]; then
#  echo "Compressing LHE file."
#  gzip ${lhe_input_file}
#fi

rm ${lhe_input_file}
