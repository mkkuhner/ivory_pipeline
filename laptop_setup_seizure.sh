#!/bin/bash

# $1 is both the prefix name of the seizure to be run and
#    the new directory that will be created to run the seizure analysis in
# $2 is the path to the elephant pipeline directory
# $3 is the path to the source of raw seizure data files
# $4 is the path to a current scat2 executable

mkdir $1
cp -r $2/* $1
cp $3/$1_raw.tsv $1
cd $1
python3 prep_scat_data.py $1
python3 make_eb_input.py data/REFELE_21_known_structure.txt_f data/REFELE_21_known.txt $1 data/dropoutrates_savannahfirst.txt
Rscript ebscript.R
cp data/mapfile_161220_* .
cp data/regionfile.v36.txt .
python3 make_species_files.py $1 mapfile_161220 regionfile.v36.txt REFELE_21

if test -f "runfile_forest.sh"; then
  mkdir nforest
  cp $1_forest.txt nforest
  cp voronoi_runfile_forest.sh nforest
  cp *_forest_fammatch_longformat.csv nforest
  cp *_forest_fammatch_wide.csv nforest
  cp $4 nforest
  perl -p -i -e "s/SCAT2/scat2.4/" runfile_forest.sh
  python3 setupscatruns.py nforest runfile_forest.sh 1001
  echo "nforest created"
fi
if test -f "runfile_savannah.sh"; then
  mkdir nsavannah
  cp $1_savannah.txt nsavannah
  cp voronoi_runfile_savannah.sh nsavannah
  cp *_savannah_fammatch_longformat.csv nsavannah
  cp *_savannah_fammatch_wide.csv nsavannah
  cp $4 nsavannah
  perl -p -i -e "s/SCAT2/scat2.4/" runfile_savannah.sh
  python3 setupscatruns.py nsavannah runfile_savannah.sh 2001
  echo "nsavannah created"
fi

echo ""
echo "scat run directories now exist within nforest and/or nsavannah"
echo ""
