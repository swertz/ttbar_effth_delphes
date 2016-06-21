#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 process_dir"
    exit 1
fi

if [ ! -d $1 -o ! -d $1/SubProcesses ]; then
    echo "Error: $1 does not exist or is not a valid MadEvent directory"
    exit 1
fi

echo "Patching matrix elements."

pushd $1/SubProcesses

for init in gg qq; do

    for dir in P*${init}*; do
        pushd $dir
    
        for matrix in matrix*.f; do
            name=`basename ${matrix} .f`
            i=`sed s/matrix//g <<< ${name}`
            sed "s/MATRIX1/MATRIX$i/g" MEPatches/5f_0j/base_patch_MadEvent_${init}.patch > patch_MATRIX$i.patch
            patch -b -i patch_MATRIX$i.patch ${matrix}
        done
    
        popd
    
    done

done

popd

echo -e "\nYou're all set!"
