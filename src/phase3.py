u Perform incremental familial matching on a new seizure
# This is meant to be run in the parent directory of all seizures.
# It does the fammatch runs one at a time, which is inefficient 
# but safe.

# Post-processing is done by phase4.py, once for all current seizures.

import sys
import os
import subprocess
from subprocess import Popen, PIPE

###################################################################
# functions

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def run_and_report(command,errormsg):
  #print("command is ",command)
  #print("running in ",os.getcwd())
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

if len(sys.argv) != 3:
  print("USAGE:  python phase3.py PREFIX pathsfile.tsv")
  print("This should be run in the parent directory of all seizures")
  print("and the pathsfile must be the same as used in phase1.py and phase2.py")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]
formalseizurename = prefix.replace("_", ", ")
print("Seizure will be called",formalseizurename)

# NB:  We do NOT check seizure_modifications and avoid running on "REJECT" seizures.
# We may still be interested in their fammatch results; they just should not be
# treated as a "seizure".  This is handled by phase4.py.

# save what directory we were run in (should be root directory of all seizures)
startdir = os.getcwd()

# read paths file
pathdir = readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
zones_path, zones_prefix = pathdir["zones_prefix"]
scat_exec = pathdir["scat_executable"][0]
fam_dir = pathdir["fammatch_archive_dir"][0]
meta_path, meta_prefix = pathdir["metadata_prefix"]
mod_path, mod_prefix = pathdir["seizure_modifications_prefix"]
ref_path, ref_prefix = pathdir["reference_prefix"]
fam_db = pathdir["fammatch_database"][0]

# create fammatch subdirectory in seizure directory
os.chdir(prefix)
if os.path.isdir("fammatch"):
  print("Overwriting previous familial matching results")
else:
  command = "mkdir fammatch"
  os.system(command)

# update seizure metadata IN PLACE
seizure_metafile = meta_path + meta_prefix + ".tsv"
if not os.path.isfile(seizure_metafile):
  print("FAILURE:  unable to locate seizure metadata file ",seizure_metafile)
  print("Location of this file must be given in ivory_paths.tsv")
  exit(-1)
prog = ivory_dir + "src/update_metadata.py"
command = ["python3",prog,seizure_metafile,prefix,formalseizurename]
run_and_report(command,"Unable to update seizure metadata")

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

# run prep_fammatch.py
os.chdir(startdir)     # return to root directory of all seizures
sector_metafile = fam_dir + "sector_metadata.txt"
progname = ivory_dir + "src/prep_fammatch.py"
command = ["python3",progname]
command += [prefix, zones_prefix, zones_path]
run_and_report(command,"Failure in program " + progname)

# run run_fammatch.py
# this calls rout2db.py to tidy up the fammatch output
progname = ivory_dir + "src/run_fammatch.py"
command = ["python3",progname]
command += [prefix,pathsfile]
run_and_report(command,"Failure in program " + progname)
print("Fammatch runs completed and archived")
