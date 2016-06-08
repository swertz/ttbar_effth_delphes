#!/bin/bash

source /cvmfs/cp3.uclouvain.be/root/root-6.06.02-sl6_amd64_gcc49/bin/thisroot.sh

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/

cms_card_path=/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/cards/delphes_card_CMS_PileUp.tcl
delphes_path=/home/fynu/swertz/storage/Delphes/Delphes-3.3.0/DelphesSTDHEP

selectionner=/home/fynu/swertz/ttbar_effth_delphes/selection/preselection_llbbX

mg_event_dir=#MG_EVENT_DIR#

cp ${mg_event_dir}/#MG_INPUT_FILE# .
mg_input_file=$(basename #MG_INPUT_FILE# .gz)
gunzip ${mg_input_file}.gz

# DELPHES PART

${delphes_path} ${cms_card_path} output_delphes_#JOB_ID#.root ${mg_input_file} 

# SELECTION PART

${selectionner} output_delphes_#JOB_ID#.root output_selected_#JOB_ID#.root

# FINALIZE

mv output_delphes_#JOB_ID#.root #OUTDIR_PATH#/
mv output_selected_#JOB_ID#.root #OUTDIR_PATH#/

rm ${mg_input_file}
