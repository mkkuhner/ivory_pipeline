#!/bin/bash

# $1 is both the prefix name of the seizure to be run and
#    the new directory that will be created to run the seizure analysis in
# $2 is the path to the source of raw seizure data files
# $3 is either "laptop" or "cluster", depending if you want to
#    run SCAT on a laptop or on the Klone cluster.  (Note that this script,
#    itself, does not run on the cluster; but it can make runfiles which will.)
#
# Assumes that directory .. contains:
#   REFELE_[Dbno]_known.txt, REFELE_[Dbno]_known_structure.txt_f
#   zones_[vno]_[species].txt
 
# To run on Jon's laptop, change the following lines to point to appropriate
# directories

#### CHANGE THESE LINES FOR SPECIFIC MACHINE

# pipeline main directory (not /src!)
pipedir="/home/mkkuhner/scat/ivory_pipeline"

# reference data files, maps, etc.
datadir="/home/mkkuhner/data"

# SCAT /src
scatdir="/home/mkkuhner/scat/scat-master/src"

# VORONOI /src
vordir="/home/mkkuhner/scat/voronoi-master/src"

####

if [ "$3" != "cluster" ];
then
  if [ "$3" != "laptop" ];
  then
    echo "Must specify either cluster or laptop as third argument"
    exit 1 
  fi
fi

### validations

mkdir $1
cp $2/$1_raw.tsv $1
cd $1
python3 ${pipedir}/src/verifymsat.py 16 ${datadir}/REFELE_4.3_raw.csv $1_raw.tsv
if [ $? -ne 0 ] 
then
  echo "TERMINATING:  sample(s) with too many unfamiliar alleles detected."
  echo "Likely problem:  microsatellites out of order in file."
  exit 1 
fi
python3 ${pipedir}/src/detect_duplicates.py $1_raw.tsv
if [ $? -ne 0 ]
then
  echo "TERMINATING:  duplicate genotypes in input file"
  echo "Likely problem:  undetected exact matches"
  exit 1
fi

### EBhybrids

python3 ${pipedir}/src/prep_scat_data.py $1
cp ${pipedir}/audillary_files/ebscript_template.R .
cp ${pipedir}/src/inference_functions.R .
cp ${pipedir}/src/calcfreqs.R .
cp ${pipedir}/src/likelihoodfunctionsandem.R .
python3 ${pipedir}/make_eb_input.py ${datadir}/REFELE_4.3_known_structure.txt_f ${datadir}/REFELE_4.3_known.txt $1 ${pipedir}/auxillary_files/dropoutrates_savannahfirst.txt
Rscript ebscript.R
cp ${datadir}/mapfile* .
cp ${datadir}/zones*txt .
cp ${pipedir}/auxillary_files/master*runfile.sh .

# make either cluster-type or laptop-type run files
if [ "$3" == "laptop" ];
then
  python3 ${pipedir}/src/filter_hybrids.py $1 mapfile_161220 zones_39 REFELE_4.3 F
else
  python3 ${pipedir}/src/filter_hybrids.py $1 mapfile_161220 zones_39 REFELE_4.3 T
fi

### set up species-specific SCAT runs (does not run them)

if test -f "runfile_forest.sh"; then
  mkdir nforest
  cp $1_forest.txt nforest
  cp voronoi_runfile_forest.sh nforest
  cp ${scatdir}/SCAT2 nforest
  if [ "$3" == "laptop" ]; then
    python3 ${pipedir}/src/setupscatruns.py nforest runfile_forest.sh 1001
  else
    python3 ${pipedir}/src/cluster_setupscatruns.py prefix nforest runfile_forest.sh 1001
  fi
  echo "nforest created"
fi
if test -f "runfile_savannah.sh"; then
  mkdir nsavannah
  cp $1_savannah.txt nsavannah
  cp voronoi_runfile_savannah.sh nsavannah
  cp ${scatdir}/SCAT2 nsavannah
  if [ "$3" == "laptop" ]; then
    python3 ${pipedir}/src/setupscatruns.py nsavannah runfile_savannah.sh 2001
  else
    python3 ${pipedir}/src/cluster_setupscatruns.py prefix nsavannah runfile_savannah.sh 2001
  fi
  echo "nsavannah created"
fi

cd ..

echo ""
echo "scat run directories now exist within nforest and/or nsavannah"
echo ""

