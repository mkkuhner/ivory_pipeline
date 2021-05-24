#!/bin/bash

# $1 is both the prefix name of the seizure to be run and
#    the new directory that will be created to run the seizure analysis in
# $2 is the path to the ivory pipeline directory
# $3 is the path to the source of raw seizure data files
# $4 is the path to a current scat2 executable
#
# plus a directory "refdata" containing:
#   REFELE_[Dbno]_known.txt, REFELE_[Dbno]_known_structure.txt_f
#   regionfile_[vno].txt

mkdir $1
cp -r $2/src/* $1
cp -r $2/auxillary_files/* $1
cp refdata/* $1
cp $3/$1_raw.tsv $1
cd $1
python prep_scat_data.py $1
python make_eb_input.py REFELE_4.3_known_structure.txt_f REFELE_4.3_known.txt $1 dropoutrates_savannahfirst.txt
source /gscratch/wasser/mkkuhner/.bashrc
Rscript ebscript.R
python filter_hybrids.py $1 mapfile_161220 regionfile.v38b.txt REFELE_4.3 T

if test -f "runfile_forest.sh"; then
  mkdir nforest
  cp $1_forest.txt nforest
  cp voronoi_runfile_forest.sh nforest
  cp *_forest_fammatch_longformat.csv nforest
  cp *_forest_fammatch_wide.csv nforest
  cp $4 nforest
  perl -p -i -e "s/SCAT2/scat2.4/" runfile_forest.sh
  python setupscatruns.py nforest runfile_forest.sh 1001
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
  python setupscatruns.py nsavannah runfile_savannah.sh 2001
  echo "nsavannah created"
fi

echo ""
echo "scat run directories now exist within nforest and/or nsavannah"
echo ""

