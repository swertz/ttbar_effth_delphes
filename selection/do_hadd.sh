for d in *_qCut50; do 
  rm $d/condor/output/output_selected.root
  hadd $d/condor/output/output_selected.root $d/condor/output/output_selected_*.root
  rm $d/condor/output/output_selected_*.root
done
