#!/bin/bash

# $1 prefix for seizure being analyzed
# $2 path to a voronoi executable

# this is run in the parent directory of nforest and nsavannah

#### CHANGE THESE LINES FOR SPECIFIC MACHINE

# main ivory pipeline directory (not /src)
pipedir="/home/mkkuhner/scat/ivory_pipeline"

# reference data
datadir="/home/mkkuhner/data"

# SCAT /src
scatdir="/home/mkkuhner/scat/scat-master/src"

# VORONOI /src
vordir="/home/mkkuhner/scat/voronoi-master/src"

####

# run VORONOI in forest
if [ -d nforest ]
then
  cd nforest
  python3 ${pipedir}/src/scat2voronoi.py ${pipedir}/auxillary_files/masterfile
  cp $2 .
  cp ${datadir}/mapfile_161220_forest.txt .
  source voronoi_runfile_forest.sh
  python3 ${pipedir}/src/prep_reports.py $1 voronoiin.txt
  python3 ${pipedir}/src/plot_scat_vor.py $1
  python3 ${pipedir}/src/cleanup_voronoi.py
  echo "Forest run completed"
  cd ..
fi

# run VORONOI in savannah
if [ -d nsavannah ]
then
  cd nsavannah
  python3 ${pipedir}/src/scat2voronoi.py ../../masterfile
  cp $2 .
  cp ${datadir}/mapfile_161220_savannah.txt .
  source voronoi_runfile_savannah.sh
  python3 ${pipedir}/src/prep_reports.py $1 voronoiin.txt
  python3 ${pipedir}/src/plot_scat_vor.py $1
  python3 ${pipedir}/src/cleanup_voronoi.py
  echo "Savannah run completed"
  cd ..
fi
