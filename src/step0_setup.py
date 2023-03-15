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
  exit(-1)

refprefix = sys.argv[1]
refsheet = sys.argv[2]
seizuresheet = sys.argv[3]
pathsfile = sys.argv[4]

# fammatch archive; this must be done first as make_reference assumes it is done

newarchive = "elephant_archive_" + refprefix
command = ["python3","make_new_archive.py",pathsfile,newarchive]
iv.run_and_report(command,"Unable to make fammatch archive")

# reference files

command = ["python3","make_reference.py",refprefix,pathsfile]
iv.run_and_report(command,"Unable to make reference data files")

# seizure raw data files

command = ["python3","make_raw_seizure.py",seizuresheet]
iv.run_and_report(command,"Unable to make seizure data files")

