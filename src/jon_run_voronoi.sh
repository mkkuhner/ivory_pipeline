#!/bin/bash

# $1 prefix for seizure being analyzed
# $2 abs path to a voronoi executable
# $3 abs path to base of ivorypipeline

# this is run in the base seizures directory

cd $1

# run VORONOI in forest
if [ -d nforest ]
then
  cd nforest
  python3 $3/src/scat2voronoi.py $3/auxillary_files/masterfile
  cp $2 .
  cp $3/auxillary_files/mapfile_161220_forest.txt .
  source voronoi_runfile_forest.sh
  python3 $3/src/prep_reports.py $1 voronoiin.txt
  python3 $3/src/plot_scat_vor.py $1
  python3 $3/src/cleanup_voronoi.py
  echo "Forest run completed"
  cd ..
fi

# run VORONOI in savannah
if [ -d nsavannah ]
then
  cd nsavannah
  python3 $3/src/scat2voronoi.py $3/auxillary_files/masterfile
  cp $2 .
  cp $3/auxiliary_files/mapfile_161220_savannah.txt .
  source voronoi_runfile_savannah.sh
  python3 $3/src/prep_reports.py $1 voronoiin.txt
  python3 $3/src/plot_scat_vor.py $1
  python3 $3/src/cleanup_voronoi.py
  echo "Savannah run completed"
  cd ..
fi

cd ..
