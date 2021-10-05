# Perform incremental familial matching on a new seizure
# This is meant to be run in the parent directory of all seizures.
# It does the fammatch runs one at a time, which is inefficient 
# but safe.

import sys
import os
import subprocess
from subprocess import Popen, PIPE

###################################################################
# functions

# assumes a file "ivory_paths.tsv" exists in the same directory as the
# calling function

def readivorypath():
  ivorypaths = {}
  inlines = open("ivory_paths.tsv","r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def run_and_report(command,errormsg):
  #process = Popen(command, stdout=PIPE,stderr=PIPE)
  process = Popen(command)
  stdout, stderr = process.communicate()
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

def safecopy(fromfile,tofile):
  if not os.path.isfile(tofile):
    command = ["cp",fromfile,tofile]
    run_and_report(command, "Unable to copy file " + fromfile)


###################################################################
# main program

if len(sys.argv) != 2:
  print("USAGE:  python phase3.py PREFIX")
  print("This should be run in the parent directory of all seizures")
  print("and relies on presence of ivory_paths.tsv there")
  exit(-1)

prefix = sys.argv[1]

# read paths file
pathdir = readivorypath()
ivory_dir = pathdir["ivory_pipeline_dir"][0]
zones_path, zones_prefix = pathdir["zones_prefix"]
scat_exec = pathdir["scat_executable"][0]
fam_dir = pathdir["fammatch_archive_dir"][0]
meta_path, meta_prefix = pathdir["metadata_prefix"]

# create fammatch directory 
os.chdir(prefix)
if os.path.isdir("fammatch"):
  print("Overwriting previous familial matching results")
else:
  command = "mkdir fammatch"
  os.system(command)

# for each species present:
outprefix = "outdir"
species_present = []
os.chdir("fammatch")
for species in ["forest","savannah"]:
  speciesdir = "n" + species
  if not os.path.isdir("../" + speciesdir):  continue   # this species is not present
  species_present.append(species)
  # create species subdirectory
  outdirname = outprefix + "_" + species
  if not os.path.isdir(outdirname):
    command = "mkdir " + outdirname
    os.system(command)

  # create SCAT sector run command and run SCAT
  datafile = "../" + prefix + "_" + species + ".txt"
  zonefile = zones_path + zones_prefix + "_" + species + ".txt"
  command = [scat_exec,"-Z","-H2",datafile,zonefile,outdirname,"16"]
  run_and_report(command,"Unable to run SCAT to determine sectors")

# run make_fammatch_incremental
sector_metafile = fam_dir + "sector_metadata.txt"
progname = ivory_dir + "src/make_fammatch_incremental.py"
command = ["python3",progname]
command += [prefix, outprefix, fam_dir, zones_path + zones_prefix]
run_and_report(command,"Failure in" + progname)

# count the sectors, just in case
lines = open(sector_metafile,"r").readlines()
numsectors = len(lines)

# for each sector:
for sec in range(0,numsectors):
  secname = "sub" + str(sec)
  # diagnose if sector is needed
  if not os.path.isdir(secname):  continue   # no data for this sector
  os.chdir(secname)
  if os.path.isfile("ONLY_ONE_SAMPLE"):
    print("Skipping",secname,"because only one sample")
    continue
  else:
    print("Processing",secname)

  # copy in fammatch code
  safecopy(ivory_dir + "src/calculate_LRs.R",".")
  safecopy(ivory_dir + "src/LR_functions.R",".")

  # run fammatch
  command = ["/bin/bash","runrscript.sh"]
  run_and_report(command,"Unable to run familial matching R program")

for species in species_present:
  # run 1_add_seizures.py
  prog1 = ivory_dir + "src/1_add_seizures.py"
  lrfile = "obsLRs." + species + ".txt"
  metafile = meta_path + meta_prefix + ".tsv"
  command = ["python3",prog1,"--input_file",lrfile,"--seizure_file",metafile]
  run_and_report(command,"Failure to run" + prog1 + "for species" + species)

  # run 2_filter_results.py
  prog2 = ivory_dir + "src/2_filter_results.py"
  lrfile = "obsLRs." + species + ".seizures.txt"
  command = ["python3",prog2,"--input_file",lrfile,"--cutoff","2.0"]
  run_and_report(command,"Failure to run" + prog2 + "for species" + species)
  
print("Fammatch runs completed.  Results are in sub_* subdirectories")
