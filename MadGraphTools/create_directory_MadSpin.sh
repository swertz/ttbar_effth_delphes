#!/bin/bash

basedir=/home/fynu/swertz/scratch/Madgraph/
ops=("OtG" "OG" "OphiG" "O13qq" "O81qq" "O83qq" "O8ut" "O8dt" "O1qu" "O1qd" "O1qt")

echo "Choose one of the following:"
for i in {0..10}; do
  echo "$i...${ops[$i]}"
done

read choice
op=${ops[${choice}]}

echo -e "\nGenerating directory for ${op}.\n"

cp -r ${basedir}/MSpatches .

if [ ! -e models/done_patch ]; then
  echo "Patching import module."
  patch -b -i MSpatches/patch_import.patch models/import_ufo.py
  touch models/done_patch
  echo ""
fi

if [ ! -e models/TopEffTh/decays.py ]; then
  echo "Updating TopEffTh model."
  mv models/TopEffTh models/TopEffTh_old
  cp -r ${basedir}/standalone_cpp_mem/models/TopEffTh models/
  echo ""
else
  if [ ! -e models/TopEffTh/restrict_${op}.dat ]; then
    echo "Retrieving restrict card."
    cp ${basedir}/standalone_cpp_mem/models/TopEffTh/restrict_${op}.dat models/TopEffTh/
  fi
  echo ""
fi

ms_test=`grep "patch" MadSpin/decay.py`
if [ -z "${ms_test}" ]; then
  echo "Patching MadSpin."
  patch -b -i MSpatches/patch_MadSpin_decay.patch MadSpin/decay.py
  echo ""
fi

echo -e "Calling MadGraph.\n"

import_string="import model TopEffTh-${op}"
proc_string="generate p p > t t~ NP^2==2 QED=1 @0; add process p p > t t~ j NP^2==2 QED=1 @1; add process p p > t t~ j j NP^2==2 QED=1 @2"
output_dir="TTbar_2j_TopEffTh_${op}_NPsq2_QED1_MSdecay"
output_string="output ${output_dir} -nojpeg"

bin/mg5_aMC <<< "${import_string}; ${proc_string}; ${output_string}"

echo "Retrieving madspin card."
cp MSpatches/madspin_card.dat ${output_dir}/Cards/

echo "Retrieving MadSpin matrix element patches."
mkdir ${output_dir}/MadSpin_patches
cp MSpatches/5f_2j/patch_MadSpin_getInterference_prodME_${op}.patch ${output_dir}/MadSpin_patches/patch_MadSpin_prodME.patch
#cp MSpatches/patch_MadSpin_prodME.patch ${output_dir}/MadSpin_patches/
cp MSpatches/5f_2j/patch_MadSpin_getInterference_${op}.patch ${output_dir}/MadSpin_patches/patch_MadSpin_getInterference.patch

echo -e "\nYou're all set!"
echo "All that remains is:"
echo "- cd ${output_dir}"
echo "- call bin/madevent"
echo "- enter multi_run 50 try0 --cluster"
echo "- in the run_card, change to 50000 events"
echo "- in the param_card, change the operator coupling from 2 to 1"
echo "- ask to run Pythia"
echo ""
