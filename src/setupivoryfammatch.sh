#!/bin/bash

#python3 rembadseizures.py SEIZ37_joint.txt seizure_modifications_nature seizure_metadata_2021_04_29.tsv
#./scat3.0 -Z -H2 SEIZ37_joint_filtered.txt regionfile.v38b.txt scatout 16
#python3 make_fammatch_subregion.py scatout/Output_hybrid SEIZ37_joint_filtered.txt regionfile.v38b.txt

for i in 0 1 2 3 4 5
do
  if test -f "new$i"; then
    rm -rf sub$i
    mkdir sub$i
    cp ../calculate_LRs.R ../LR_functions.R sub$i
    mv new${i}.txt sub$i
    mv old${i}.txt sub$i
    mv ref${i}_fammatch.csv sub$i
    cd sub$i
    species='forest'
    if [ $i -gt 1 ]
    then
      species='savannah'
    fi
    echo "Rscript calculate_LRs.R ${species} ref${i}_fammatch.csv old${i}.txt new${i}.txt" > runrscript.sh
    cd .. 
  fi
done
