#!/bin/bash

MGDIR=$HOME/scratch/Madgraph/MG5_aMC_v2_2_1/

MGWORKDIR=$MGDIR/$1/SubProcesses/

SUBPROCS=("gg" "ccx" "ddx" "dsx" "sdx" "ssx" "uux")
DECAYS=("t_bwp_wp_vlep_tx_bxwm_wm_vlem" "t_bwp_wp_vlep_tx_bxwm_wm_vlmum" "t_bwp_wp_vlmup_tx_bxwm_wm_vlem" "t_bwp_wp_vlmup_tx_bxwm_wm_vlmum") 

for ((i=0;i<${#SUBPROCS[*]};i++)); 
do
	proc=${SUBPROCS[$i]}
	for ((j=0;j<${#DECAYS[*]};j++)); 
	do
		decay=${DECAYS[$j]}
		dir=$MGWORKDIR/P0_${proc}_ttx_$decay
		if [ -d "$dir" ]
		then
			echo "Back-uping and patching $dir/matrix1.f"
			cp $dir/matrix1.f $dir/matrix1.f.old
			patch $dir/matrix1.f patch_$proc.f
		else
			echo "Couldn't find directory $dir".
		fi
	done
done

