# step1_fammatch.py (based on former phase1.py and phase3.py)
# Take a seizure from raw file to processed data, but does NOT
# run any part of fammatch.
# Run this program in the parent directory of all seizures.

# NB:  This program does not use the seizure_modifications file but 
# instead runs everything; it does not omit or rename/merge any seizures.  
# This allows us to change our mind about modifications without having to
# rerun (which takes a very long time).  Seizure_modifications
# are implemented in a later step.

import sys
import os
import subprocess
from subprocess import Popen, PIPE
import ivory_lib as iv

############################################################################
## functions

def check_seizure_present(sfile,seizurename):
  oldseizures = open(sfile,"r").readlines()
  for line in oldseizures:
    line = line.rstrip().split()
    if line[0] == seizurename:
      return (True, oldseizures)
  return (False, oldseizures)

############################################################################
## main program

if len(sys.argv) != 3:
  print("USAGE:  python3 step1_nofam.py PREFIX pathsfile.tsv")
  exit(-1)

prefix = sys.argv[1]
# we do not do the short SCAT runs needed for fammatch on the
# cluster, so we force "laptop" version here
runtype = "laptop"
pathsfile = os.path.abspath(sys.argv[2])

specieslist = ["forest","savannah"]

# read ivory_paths.tsv file
# set up needed variables
pathdir = iv.readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_dir, scat_exec = pathdir["scat_executable"]
scat_path = scat_dir + scat_exec
reference_path, reference_prefix = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
seizure_data_dir = pathdir["seizure_data_dir"][0]

homedir = os.path.abspath(".")
if not homedir.endswith("/"):
  homedir += "/"

###
# Directory setup and checking

# seizure directory should not exist yet
seizure_dir = os.path.abspath(prefix)
if not seizure_dir.endswith("/"):
  seizure_dir += "/"
if os.path.isdir(seizure_dir):
  print("FAILURE:  The seizure directory",seizure_dir,"already exists")
  print("If you want to replace all previous results, delete or move away")
  print("the previous seizure directory before proceeding.")
  exit(-1)

# raw data file should exist
rawdata = seizure_data_dir + prefix + "_raw.tsv"
if not os.path.isfile(rawdata):
  print("FAILURE:  raw data file " + rawdata + " not found")
  exit(-1)

# filtered forest and savannah reference files should exist
for species in specieslist:
  filterfile = reference_path + reference_prefix + "_filtered_" + species + ".txt"
  if not os.path.isfile(filterfile):
    print("Reference file",filterfile,"not found:  need to create filtered reference")
    exit(-1)

# Create the seizure directory and its fammatch subdirectory
command = ["mkdir",seizure_dir]
iv.run_and_report(command, "Unable to create seizure directory")
command = ["mkdir",seizure_dir+"fammatch"]
iv.run_and_report(command, "Unable to create fammatch subdirectory within" + seizure_dir)

# copy raw data file into seizure directory
command = ["cp", rawdata, seizure_dir]
iv.run_and_report(command,"Could not copy in raw data file " + rawdata)

###
# Prepping and validating data

# run log_seizure.py
# this program creates a logfile recording run parameters
command = ["python3", ivory_dir+"src/log_seizure.py",prefix,pathsfile]
iv.run_and_report(command,"Failed to log the run")

# cd to newly created directory
os.chdir(prefix)

# run verifymsat
command = ["python3",ivory_dir + "src/verifymsat.py", "16"] 
command.append(reference_path + reference_prefix+"_raw.csv")
command.append(prefix + "_raw.tsv")
iv.run_and_report(command,"Microsat validation failed")

# run prep_scat_data
command = ["python3",ivory_dir + "src/prep_scat_data.py",prefix]
iv.run_and_report(command,"Failure in prep_scat_data.py")
print("Data validated and prepared")

# run detect_duplicates
# this is done after prep_scat_data to avoid duplicate testing on
# individuals with too much missing data
command = ["python3",ivory_dir + "src/detect_duplicates.py",prefix+"_unknowns.txt"]
iv.run_and_report(command,"Duplicate samples detected")

###
# Separating the species and discarding hybrids

# marshall files for ebhybrids
command = ["cp",ivory_dir + "aux/ebscript_template.R","."]
iv.run_and_report(command,"Failure to find ebscript template")

command = ["cp",ivory_dir + "src/EBhybrids/inferencefunctions.R","."]
iv.run_and_report(command,"Failure to find EBhybrids source code")

command = ["cp",ivory_dir + "src/EBhybrids/calcfreqs.R","."]
iv.run_and_report(command,"Failure to find EBhybrids source code")

command = ["cp",ivory_dir + "src/EBhybrids/likelihoodfunctionsandem.R","."]
iv.run_and_report(command,"Failure to find EBhybrids source code")

# run make_eb_input
command = ["python3",ivory_dir + "src/make_eb_input.py"]
command.append(reference_path + reference_prefix + "_known_structure.txt_f")
command.append(reference_path + reference_prefix + "_known.txt")
command.append(prefix)
command.append(ivory_dir + "aux/dropoutrates_savannahfirst.txt")
iv.run_and_report(command,"Failure to make EBhybrids input files")

# run ebhybrids
command = ["Rscript","ebscript.R"]
iv.run_and_report(command,"Failure in EBhybrids")
print("EBhybrids run completed")

# generate report on hybrids
hybrid_reportfile = prefix + "_hybout.txt"
ebhyrbid_output = prefix + "_hybt.txt"
hybrid_cutoff = 0.50
command = ["rm","-rf",hybrid_reportfile]
iv.run_and_report(command,"Could not delete previous hybrid report")
command = ["python3",ivory_dir + "src/makehybridreport.py",
  prefix,str(hybrid_cutoff)]
iv.run_and_report(command,"Could not generate hybrid report")

# prep files for filter_hybrids
for species in specieslist:
  mapfile = map_path + map_prefix + "_" + species + ".txt"
  command = ["cp",mapfile,"."]
  iv.run_and_report(command,"Could not copy in map file" + mapfile)

  zonesfile = zones_path + zones_prefix + "_" + species + ".txt"
  command = ["cp",zonesfile,"."]
  iv.run_and_report(command,"Could not copy in zones file" + zonesfile)

command = ["cp",ivory_dir + "aux/master_scat_runfile.sh","."]
iv.run_and_report(command,"Could not copy in master scat runfile")

# run filter_hybrids

command = ["python3",ivory_dir + "src/filter_hybrids.py"]
command.append(prefix)
command.append(pathsfile)
if runtype == "laptop":
  command.append("F")
else:
  command.append("T")
# the following T means "canned" reference; we already verified this exists
command.append("T")
iv.run_and_report(command,"Could not filter hybrids")

# make species directories; various programs expect they'll exist
# we do not populate them yet as they're for regular SCAT runs, not fammatch

for species in specieslist:
  if os.path.isfile("runfile_" + species + ".sh"):
    # set up species specific directory
    dirname = "n" + species
    if not os.path.isdir(dirname):
      command = ["mkdir",dirname]
      iv.run_and_report(command,"Could not create " + dirname)
    else:
      print("FAILURE: ",dirname," directory already exists")
      exit(-1)

