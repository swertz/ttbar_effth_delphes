# No shebang here as this script must be sourced and not executed

if [[ $HOSTNAME == lxplus* ]]; then

    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/gcc/4.9.1-cms/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/boost/1.57.0-cms/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/python/2.7.6-cms/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/libjpg/8b-cms/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/libpng/1.6.16/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/xz/5.0.3__5.1.2alpha-cms/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/lcg/root/6.02.00-cms4/etc/profile.d/init.sh
    source /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/git/1.8.3.1-cms2/etc/profile.d/init.sh
    export PYTHONPATH="/afs/cern.ch/user/s/sbrochet/.local/lib/python2.7/site-packages:$PYTHONPATH"

else

    module load python/python27_sl6_gcc49
    module load gcc/gcc-4.9.1-sl6_amd64
    #module load root/6.02.05-sl6_gcc49
    source /home/fynu/swertz/soft/root-6.02.12/bin/thisroot.sh
    export PYTHONPATH="/home/fynu/sbrochet/.local/lib/python2.7/site-packages:$PYTHONPATH"

fi

