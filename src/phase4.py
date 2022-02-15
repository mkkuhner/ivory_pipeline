# Process all current seizures except those excluded by the seizure_modifications file,
# computing overall match probabilities and drawing a network diagrom.  NB:  This
# program is INTERACTIVE in the network diagram step; you have the opportunity to
# pretty up the diagram before it is saved.  You can always rerun that step, by itself,
# if dissatisfied.

# Takes an input argument of the path to a DM (direct matches, AKA exact matches)
# file; this is not kept in standard archives for security reasons as it has
# quite a bit of primary data in it.

# Run in the parent directory of all seizures, AFTER familial matching has
# been run on all of them.  (TO DO:  diagnose if it has not.)

import sys, os, subprocess
from subprocess import Popen

##########################################################################
# functions

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def run_and_report(command,errormsg):
  process = Popen(command)
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

##########################################################################
# main program

if len(sys.argv) != 5:
  print("USAGE:  python3 phase4.py ivory_paths.tsv dms.tsv LR_cutoff minloci")
  print("This program jointly does all available seizures")
  print("Be sure phase3.py has been run on all desired seizures first!")
  print("dms.tsv lists direct matches obtained by other means than fammatch")
  exit(-1)


# read ivory_paths and set up variables
ivory_paths = sys.argv[1]
pathdir = readivorypath(ivory_paths)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
mods = pathdir["seizure_modifications_prefix"]
modfile = mods[0] + mods[1]
archive = pathdir["fammatch_archive_dir"]
archivefile = archive[0] + archive[1]
metadata = pathdir["metadata_prefix"]
metafile = metadata[0] + metadata[1] + ".tsv"

dmfile = sys.argv[2]
LR_cutoff = float(sys.argv[3])
minloci = int(sys.argv[4])

# immediately test archive access

if not os.path.isfile(archivefile):
  print("Cannot find fammatch archive:  did you forget to hook up the external HD?")
  print("Location tried was",archivedir)
  exit(-1)

# read fprates.tsv for false positive rates from simulated data
fpfile = ivory_dir + "aux/fprates.tsv"
fps = {}
fps["forest"] = []
fps["savannah"] = []
whichspecies = None
for line in open(fpfile,"r"):
  line = line.rstrip().split()
  if line[0] == "forest"
    whichspecies = "forest"
    continue
  if line[0] == "savannah"
    whichspecies = "savannah"
    continue
  assert whichspecies is not None
  fps[whichspecies].append([float(line[0]),float(line[1])))

# check that DM file exists
if not os.path.isfile(dmfile):
  print("Cannot open DM file (exact matches): ",dmfile)
  exit(-1)

# pull an ALL seizures database report as input data
progname = ivory_dir + "src/fammatch_database.py"
reportfile = "fammatch_global.tsv"
command = ["python3",progname,archivefile,"report","ALL",reportfile,"2.0","13"]
run_and_report(command,"Unable to pull report from fammatch database ",archivefile")

# read seizure_modifications file
rejected_seizures = []
merged_seizures = {}
state = None
for line in open(modfile,"r"):
  line = line.rstrip().split("\t")
  if line[0] == "REJECT":
    state = "reject"
    continue
  if line[0] == "MERGE":
    state = "merge"
    continue
  if state == "reject":
    assert len(line) == 1
    rejected_seizures.append(line[0])
    continue
  if state == "merge":
    # merge requires a new name and at least two old names
    assert len(line) >= 3
    newname = line[0]
    for entry in line[1:]:
      merged_seizures[entry] = newname

# filter database report based on seizure_modifications
# rules:  delete all lines mentioning a REJECT seizure
#         rename MERGE seizures
for line in open(reportfile,"r"):
  line = line.rstrip().split("\t")



# run create_network_input.py
progname = ivory_dir + "src/create_network_input.py"
command = ["python3", progname, metafile, dmfile, modfile,

# run network creation program

