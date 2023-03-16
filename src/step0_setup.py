# This program takes files from the Master Elephant Database Excel spreadsheet and
# sets up three components for the pipeline:

# 1.  Reference files
# 2.  Seizure raw data files
# 3.  Fammatch database

# Run this in the parent directory of all seizures 
# It will assume that files pulled from the spreadsheet are in the
# reference data directory mentioned in ivory_paths:
# reference file is called REFPREFIX_raw.csv
# seizure file is arbitrarily named and passed as input; should be .tsv

######################
# main

import sys
import ivory_lib as iv
import os

if len(sys.argv) != 4:
  print("USAGE: python3 step0_setup.py refprefix seizurefile.tsv ivory_paths")
  print("refprefix is a NEW prefix for this reference release") 
  print("a file refprefix_raw.csv must exist in reference directory")
  print("seizurefile.tsv is data pulled from the Master spreadsheet tab 'Ivory Stats'")
  exit(-1)

refprefix = sys.argv[1]
seizuresheet = sys.argv[2]
pathsfile = sys.argv[3]
pathdir = iv.readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]

# fammatch archive; this must be done first as make_reference assumes it is done

newarchive = "elephant_archive_" + refprefix
progname = ivory_dir + "src/make_new_archive.py"
command = ["python3",progname,pathsfile,newarchive]
iv.run_and_report(command,"Unable to make fammatch archive")

# reference files
progname = ivory_dir + "src/make_reference.py"
command = ["python3",progname,refprefix,pathsfile]
iv.run_and_report(command,"Unable to make reference data files")

# seizure raw data files

progname = ivory_dir + "src/make_raw_seizure.py"
command = ["python3",progname,seizuresheet,pathsfile]
iv.run_and_report(command,"Unable to make seizure data files")

