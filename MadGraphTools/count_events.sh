#!/bin/bash

for i in {1..11}; do
  number=`cat events_reweight_${i}.lhe | grep "4      0 +0.0" | wc -l`
  #number=`cat events_reweight_${i}.lhe | grep "<event>" | wc -l`
  param=`cat events_reweight_${i}.lhe | grep "1.000000e+00 #"`
  echo "Operator $param: $number"
done
