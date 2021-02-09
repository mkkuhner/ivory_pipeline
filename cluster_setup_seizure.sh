#!/bin/bash

mkdir $1
cp -r 091220/* $1
cp cluster* $1
cp data/$1_raw.tsv $1
cd $1
python prep_scat_data.py $1
python make_eb_input.py data/reference_structure.txt data/REFELE_20_known.txt $1 data/dropoutrates_savannahfirst.txt
source /gscratch/wasser/mkkuhner/.bashrc
Rscript ebscript.R
cp data/mapfile_new_* .
cp data/regionfile.v36.txt .
python cluster_make_species_files.py $1 new regionfile.v36.txt
