#!/bin/bash

# $1 prefix for seizure being analyzed
# $2 path to a voronoi executable
# $3 is species, either "forest" or "savannah"

# setup and run VORONOI
python3 ../scat2voronoi.py ../masterfile
cp $2 .
cp ../mapfile_161220* .
source voronoi_runfile_*.sh
python3 prep_reports.py $1 voronoiin.txt

# run familial matching R scripts
mkdir fammatch
mv *_long.csv fammatch
cp ../calculate_LRs.R ../LR_functions.R fammatch
cp ../1_add_seizures.py ../2_filter_results.py ../3_seizure_analysis.py fammatch
mv *_wide.csv fammatch
cp ../data/seizure_$3_wide.csv fammatch
cp ../data/seizure_metadata.tsv fammatch
cd fammatch
python3 partition_genotypes.py $3 $1_genotypes_$3_wide.csv seizure_$3_wide.csv
Rscript LRs.R $3 *_$3_long.csv other_genotypes_$3_wide.csv $1_genotypes_$3_wide.csv
python3 1_add_seizures.py --input_file obsLRs.$3.txt --seizure_file seizure_metadata.tsv
python3 2_filter_results.py --input_file obsLRs.$3.seizures.txt --cutoff 2.0
python3 3_seizure_analysis.py --filtered_file obsLRs.$3.seizures.2.0.filtered.txt
cd ..

echo ""
echo "Now run plot_scat_vor.py for graphical output on SCAT and VORONOI"
echo ""
