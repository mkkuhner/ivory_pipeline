#!/bin/bash

# $1 prefix for seizure being analyzed
# $2 path to a voronoi executable

# this is run in the parent directory of nforest and nsavannah

# run VORONOI in forest
if [ -d nforest ]
then
  cd nforest
  python3 ../../scat2voronoi.py ../../masterfile
  cp $2 .
  cp ../../mapfile_161220_forest.txt .
  source voronoi_runfile_forest.sh
  python3 ../../prep_reports.py $1 voronoiin.txt
  python3 ../../plot_scat_vor.py $1
  python3 ../../cleanup_voronoi.py
  echo "Forest run completed"
  cd ..
fi

# run VORONOI in savannah
if [ -d nsavannah ]
then
  cd nsavannah
  python3 ../../scat2voronoi.py ../../masterfile
  cp $2 .
  cp ../../mapfile_161220_savannah.txt .
  source voronoi_runfile_savannah.sh
  python3 ../../prep_reports.py $1 voronoiin.txt
  python3 ../../plot_scat_vor.py $1
  python3 ../../cleanup_voronoi.py
  echo "Savannah run completed"
  cd ..
fi
