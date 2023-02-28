# make_reference.py (based on former phase1.py and phase3.py)
 
# Create reference files needed by all parts of the pipeline,
# given a copy of the reference database file.  

# this includes:
#   reference data by forest and savannah for SCAT
#   reference data by sectors for fammatch

import sys
import os
import subprocess
from subprocess import Popen, PIPE
import csv

# constants
hybrid_cutoff = 0.5

############################################################################
## functions

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

# read master reference-data csv file
def read_raw_reference(reffile):
  rdat = {}
  with open(reffile,newline="") as csvfile:
    reader = csv.reader(csvfile)
    for line in reader:
      if line[0].startswith("Match"):
        header = line
        regionindex = header.index("Region")
        matchindex = header.index("Match ID")
        firstmsat = header.index("FH67")
        lastmsat = firstmsat+32
        continue
      sid = line[matchindex]
      region = line[regionindex]
      if region == "NA":  continue   # can't use this region-unknown individual
      assert len(line[firstmsat:lastmsat]) == 32
      rdat[sid] = [region,line[firstmsat:lastmsat]]
  return rdat

def reference_to_scat(reference_prefix, refdata):
  # process reference and write refprefix_known.tsv
  sortsids = sorted(list(refdata.keys()))
  refknown = reference_prefix + "_known.tsv"
  outfile = open(refknown,"w")
  numinds = 0
  for sid in sortsids:
    region = refdata[sid][0]
    outline1 = sid + "\t" + region
    outline2 = sid + "\t" + region
    msats = refdata[sid][1]
    for m1,m2 in zip(msats[0::2],msats[1::2]):
      bad = False
      if m1 == "" or m2 == "":  bad = True
      if m1 == "NA" or m2 == "NA":  bad = True
      if m1 == "-999" or m2 == "-999":  bad = True
      if bad:
        m1 = "-999"
        m2 = "-999"
      outline1 += "\t" + m1
      outline2 += "\t" + m2
    outline1 += "\n"
    outline2 += "\n"
    outfile.write(outline1)
    outfile.write(outline2)
    numinds += 1
  outfile.close()
  return numinds, refknown

############################################################################
## main program

if len(sys.argv) != 3:
  print("USAGE:  python3 make_reference.py REFPREFIX pathsfile.tsv")
  print("and if it is, you will need to rename, move or delete the old fammatch archive.")
  exit(-1)
refprefix = sys.argv[1]
pathsfile = os.path.abspath(sys.argv[2])


# read ivory_paths.tsv file
# set up needed variables
pathdir = readivorypath(pathsfile)

ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_dir, scat_exec = pathdir["scat_executable"]
reference_path, reference_prefix = pathdir["reference_prefix"]

if reference_prefix != refprefix:
  print("Asked to make reference",refprefix,"but pathfile",pathsfile)
  print("points to",reference_path + reference_prefix)
  print("Correct this before continuing.")
  exit(-1)

zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
meta_path, meta_prefix = pathdir["metadata_prefix"]
fammatch_archive_dir, fammatch_archive_name = pathdir["fammatch_archive_dir"]
structure_dir, structure_exec = pathdir["structure_executable"]
new_fammatch_archive_name = "elephant_archive_" + refprefix

# protocol on the fammatch archive:

# base directory must exist
if not os.path.isdir(fammatch_archive_dir):
  print("Parent directory of fammatch archive",fammatch_archive_dir,"does not exist")
  print("Did you forget to mount the hard drive?")
  exit(-1)

#numinds) name in ivory_paths must match name deduced by this program
if fammatch_archive_name != new_fammatch_archive_name:
  print("Convention for elephant archive name in pathsfile would be",new_fammatch_archive_name)
  print("Correct and rerun.")
  exit(-1)

# fammatch directory under that name must NOT exist
if isdir(fammatch_archive_dir + fammatch_archive_name):
  print("Requested familial matching directory already exists")
  print("as" + fammatch_archive_dir + fammatch_archive_name)
  print("If you wish to replace it, move it away or rename it")
  exit(-1)

# all is well, so create fammatch archive
command = ["mkdir",fammatch_archive_dir + fammatch_archive_name]
run_and_report(command,"Unable to create fammatch archive")

# read raw reference file
refname = reference_path + reference_prefix + "_raw.csv"
refdata = read_raw_reference(refname)

# make directory for processed reference
ref_subdir = reference_path + reference_prefix + "/"
if os.path.isdir(ref_subdir):
  print("Reference directory",ref_subdir,"already exists; move or rename it.")
  exit(-1)
command = ["mkdir",ref_subdir]
run_and_report(command,"Unable to create reference subdirectory")
os.chdir(ref_subdir)

# write refprefix_known.tsv
numinds, refknown = reference_to_scat(refprefix)
print("Found",numinds,"location-known samples")

# prep STRUCTURE run

# make a version of ref data with header for STRUCTURE
structure_header = ivory_dir + "aux/header_for_structure"
structure_infile = refprefix + "_structure.txt"
command = ["cat",structure_header,refknown,">",structure_infile]
run_and_report(command,"Unable to create structure input file")

# write mainparams; overwrites version in STRUCTURE directory
paramfile = ivory_dir + "aux/mainparams"
outfile = open(structure_dir + "mainparams","w")
structure_infile = refprefix + "_structure.txt"
structure_outfile = refprefix + "_structure_out.txt"
infiletag = "MY_INFILE_HERE"
outfiletag = "MY_OUTFILE_HERE"
numindtag = "MY_NUMINDS_HERE"
for line in open(paramfile,"r"):
  line = line.rstrip().split()
  line = line.replace(infiletag,structure_infile)
  line = line.replace(outfiletag,structure_outfile)
  line = line.replace(numindtag,numinds)
  outfile.write(line)
outfile.close()

# run STRUCTURE
command = [structure_dir + structure_exec]
run_and_report(command,"Unable to run STRUCTURE")

# run make_eb_input to prepare data for EBhybrids
# Note:  STRUCTURE puts "-f" on the end of its output file name--dunno why
# it can't just use the name it's given...

structure_outfile = structure_outfile + "-f"
progname = ivory_dir + "src/make_eb_input.py"
dropoutfile = ivory_dir + "aux/dropoutrates_savannahfirst.txt"
command = ["python3",progname,structure_outfile,refknown,refprefix,dropoutfile,"reference"]
run_and_report("Unable to run make_eb_input.py")

#run EBhybrids
command = ["Rscript","ebscript.R"]
run_and_report(command,"Failure in EBhybrids")

# make species specific SCAT reference files
# code excerpted from filter_hybrids.py

# classify samples by species
ebfile = refprefix + "_hybt.txt"
speciesdict = {}
for line in open(ebfile,"r"):
  if line.startswith("Sample"):  continue
  line = line.rstrip().split()
  id = line[0]
  savannah = float(line[1])
  forest = float(line[2])
  hybs = [float(x) for x in line[3:]]
  sumhybs = sum(hybs)
  if sumhybs >= hybrid_cutoff:
    speciesdict[id] = "H"
  elif savannah >= forest:
    speciesdict[id] = "S"
  else:
    speciesdict[id] = "F"

# write savannah and forest files
savannah_output = open(refprefix + "_savannah.txt","w")
forest_output = open(refprefix + "_forest.txt","w")
savcount = 0.0
forcount = 0.0
hybcount = 0.0
for line in open(refknown,"r"):
  saveline = line
  line = line.rstrip().split()
  sid = line[0]
  if sid not in speciesdict:
    print("Found an SID in",refknown,"that is not in",ebfile)
    print("Data files are incoherent:  terminating.")
    exit(-1)
  if speciesdict[sid] == "H":  
    hybcount += 0.5
    continue   # discard hybrids
  if speciesdict[sid] == "S":
    savcount += 0.5
    savannah_output.write(saveline)
  elif speciesdict[sid] == "F":
    forcount += 0.5
    forest_output.write(saveline)
  else:
    print("Logic error in parsing EBhybrids data")
    exit(-1)
savannah_output.close()
forest_output.close()
print("Savannah samples after filtering:",int(savcount))
print("Forest samples after filtering:",int(forcount))
print("Hybrid samples (removed):",int(hybcount))
