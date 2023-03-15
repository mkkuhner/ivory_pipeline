# This program takes files from the Master Elephant Database Excel spreadsheet and
# sets up three components for the pipeline:

# 1.  Reference files
# 2.  Seizure raw data files
# 3.  Fammatch database

# Run this in the parent directory of all seizures 

######################
# main

import sys
import ivory_lib as iv
import os

if len(sys.argv) != 5:
  print("USAGE: python3 step0_setup.py refprefix refsheet seizuresheet ivory_paths")
  print("refprefix is a NEW prefix for this reference release") 
  print("refsheet is data pulled from the Master spreadsheet tab 'Reference Stats'")
  print("seizuresheet is data pulled from the Master spreadsheet tab 'Ivory Stats'")
  exit(-1)

refprefix = sys.argv[1]
refsheet = sys.argv[2]
seizuresheet = sys.argv[3]
pathsfile = sys.argv[4]
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
command = ["python3",progname,seizuresheet]
iv.run_and_report(command,"Unable to make seizure data files")

