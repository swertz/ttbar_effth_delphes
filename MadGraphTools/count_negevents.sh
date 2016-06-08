#!/bin/bash

for dir in *; do
  if [ -f $dir/unweighted_events.lhe.gz ]; then
    gunzip $dir/unweighted_events.lhe.gz
  fi
  result=`cat $dir/unweighted_events.lhe | grep "4   0 -" | wc -l`
  echo "$dir: $result"
done
