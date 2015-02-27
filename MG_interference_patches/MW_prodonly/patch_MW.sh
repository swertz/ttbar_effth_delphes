#!/bin/bash

MGDIR=$HOME/scratch/Madgraph/MG5_aMC_v2_2_1/

MGWORKDIR=$MGDIR/$1/

SUBPROCS=("gg" "uux" "ccx" "ddx" "dsx" "sdx" "ssx")
DECAYS=("t_bwp_wp_veep_tx_bxwm_wm_vexem" "t_bwp_wp_veep_tx_bxwm_wm_vmxmum" "t_bwp_wp_vmmup_tx_bxwm_wm_vexem" "t_bwp_wp_vmmup_tx_bxwm_wm_vmxmum")

for ((j=0;j<${#DECAYS[*]};j++)); 
do
	for ((i=0;i<${#SUBPROCS[*]};i++)); 
	do
		proc=${SUBPROCS[$i]}
		decay=${DECAYS[$j]}
		dir=$MGWORKDIR/SubProcesses/P0_gg_ttx_$decay
		if [ -d "$dir" ]
		then
			echo "Back-uping and patching $dir/matrix$(($i+1)).f"
			cp $dir/matrix$(($i+1)).f $dir/matrix$(($i+1)).f.backup
			patch $dir/matrix$(($i+1)).f patch_$(($i+1))_$proc.f
		else
			echo "Couldn't find directory $dir".
		fi
	done
done

dir=$MGWORKDIR/Source/MadWeight/tools
if [ -d $dir ]
then
	echo "Back-uping and patching $dir/vegas.f"
	cp $dir/vegas.f $dir/vegas.f.backup
	patch $dir/vegas.f patch_vegas.f
else
	echo "Couldn't find directory $dir".
fi

dir=$MGWORKDIR/bin/internal/
if [ -d $dir ]
then
	echo "Back-uping and patching $dir/madweight_interface.py"
	cp $dir/madweight_interface.py $dir/madweight_interface.py.backup
	patch $dir/madweight_interface.py patch_interface.py
else
	echo "Couldn't find directory $dir".
fi
	

