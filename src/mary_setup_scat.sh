#!/bin/bash

# $1 is both the prefix name of the seizure to be run and
#    the new directory that will be created to run the seizure analysis in
# $2 is the path to the source of raw seizure data files
#
# plus a directory "refdata" containing:
#   REFELE_[Dbno]_known.txt, REFELE_[Dbno]_known_structure.txt_f
#   regionfile_[vno].txt


mkdir $1
cp $2/$1_raw.tsv $1
cd $1
python3 ../verifymsat.py 16 ../REFELE_4.3_raw.csv $1_raw.tsv
if [ $? -ne 0 ] 
then
  echo "TERMINATING:  sample(s) with too many unfamiliar alleles detected."
  echo "Likely problem:  microsatellites out of order in file."
  exit 1 
fi
python3 ../prep_scat_data.py $1
cp ../*.R .
python3 ../make_eb_input.py ../REFELE_4.3_known_structure.txt_f ../REFELE_4.3_known.txt $1 ../dropoutrates_savannahfirst.txt
Rscript ebscript.R
cp ../mapfile* .
cp ../regionfile.v38b.txt .
cp ../master*runfile.sh .
python3 ../filter_hybrids.py $1 mapfile_161220 regionfile.v38b.txt REFELE_4.3 F

if test -f "runfile_forest.sh"; then
  mkdir nforest
  cp $1_forest.txt nforest
  cp voronoi_runfile_forest.sh nforest
  cp ../SCAT2 nforest
  python3 ../setupscatruns.py nforest runfile_forest.sh 1001
  echo "nforest created"
fi
if test -f "runfile_savannah.sh"; then
  mkdir nsavannah
  cp $1_savannah.txt nsavannah
  cp voronoi_runfile_savannah.sh nsavannah
  cp ../SCAT2 nsavannah
  python3 ../setupscatruns.py nsavannah runfile_savannah.sh 2001
  echo "nsavannah created"
fi

cd ..

echo ""
echo "scat run directories now exist within nforest and/or nsavannah"
echo ""

