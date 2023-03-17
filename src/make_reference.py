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
import ivory_lib as iv

# constants
hybrid_cutoff = 0.5

############################################################################
## functions

# read master reference-data csv file
def read_raw_reference(reffile):
  rdat = {}
  with open(reffile,newline="") as csvfile:
    reader = csv.reader(csvfile)
    for line in reader:
      if line[0].startswith("Match"):
        header = line
        regionindex = header.index("Input Zone")
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

def reference_to_scat(ref_prefix, refdata):
  # process reference and write refprefix_known.tsv
  sortsids = sorted(list(refdata.keys()))
  refknown = ref_prefix + "_known.tsv"
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
  exit(-1)
refprefix = sys.argv[1]
pathsfile = os.path.abspath(sys.argv[2])

# read ivory_paths.tsv file
# set up needed variables
pathdir = iv.readivorypath(pathsfile)

ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_dir, scat_exec = pathdir["scat_executable"]
reference_path, non_used = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
meta_path, meta_prefix = pathdir["metadata_prefix"]
fammatch_archive_dir, fammatch_archive_name = pathdir["fammatch_archive_dir"]
structure_dir, structure_exec = pathdir["structure_executable"]
new_fammatch_archive_name = "elephant_archive_" + refprefix

# read raw reference file
refname = reference_path + refprefix + "_raw.csv"
refdata = read_raw_reference(refname)

# make working directory for processed reference
ref_subdir = reference_path + refprefix + "/"
if os.path.isdir(ref_subdir):
  print("Reference directory",ref_subdir,"already exists; move or rename it.")
  exit(-1)
command = ["mkdir",ref_subdir]
iv.run_and_report(command,"Unable to create reference subdirectory")
os.chdir(ref_subdir)

# write refprefix_known.tsv
numinds, refknown = reference_to_scat(refprefix, refdata)
print("Found",numinds,"location-known samples")

# prep STRUCTURE run

# make a version of ref data with header for STRUCTURE
structure_header = ivory_dir + "aux/header_for_structure"
structure_infile = refprefix + "_structure.txt"
# NB we do not use run_and_report here because it doesn't work with
# the > redirect for some reason.
command = ["cat",structure_header,refknown,">",structure_infile]
command = " ".join(command)
os.system(command)
command = ["cp",structure_infile,structure_dir]
command = " ".join(command)
os.system(command)

# write mainparams; overwrites version in STRUCTURE directory
paramfile = ivory_dir + "aux/mainparams"
outfile = open(structure_dir + "mainparams","w")
structure_outfile = refprefix + "_known_structure.txt"
infiletag = "MY_INFILE_HERE"
outfiletag = "MY_OUTFILE_HERE"
numindtag = "MY_NUMINDS_HERE"
for line in open(paramfile,"r"):
  line = line.replace(infiletag,structure_infile)
  line = line.replace(outfiletag,structure_outfile)
  line = line.replace(numindtag,str(numinds))
  outfile.write(line)
outfile.close()

# run STRUCTURE
currentdir = os.path.abspath(".")
if not currentdir.endswith("/"):
  currentdir += "/"
os.chdir(structure_dir)
command = ["./"+structure_exec]
iv.run_and_report(command,"Unable to run STRUCTURE")
os.chdir(currentdir)

# run make_eb_input to prepare data for EBhybrids
# Note:  STRUCTURE puts "_f" on the end of its output file name--dunno why
# it can't just use the name it's given...

structure_outfile = structure_outfile + "_f"
command = ["cp",structure_dir + structure_outfile,currentdir + structure_outfile]
iv.run_and_report(command,"Unable to copy STRUCTURE output to working directory")

# marshall files for ebhybrids
command = ["cp",ivory_dir + "aux/ebscript_template.R","."]
iv.run_and_report(command,"Failure to find ebscript template")
command = ["cp",ivory_dir + "src/inferencefunctions.R","."]
iv.run_and_report(command,"Failure to find EBhybrids source code")
command = ["cp",ivory_dir + "src/calcfreqs.R","."]
iv.run_and_report(command,"Failure to find EBhybrids source code")
command = ["cp",ivory_dir + "src/likelihoodfunctionsandem.R","."]
iv.run_and_report(command,"Failure to find EBhybrids source code")

progname = ivory_dir + "src/make_eb_input.py"
dropoutfile = ivory_dir + "aux/dropoutrates_savannahfirst.txt"
command = ["python3",progname,structure_outfile,refknown,refprefix,dropoutfile,"reference"]
iv.run_and_report(command,"Unable to run make_eb_input.py")

#run EBhybrids
command = ["Rscript","ebscript.R"]
iv.run_and_report(command,"Failure in EBhybrids")

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
savannahfile = refprefix + "_filtered_savannah.txt"
forestfile = refprefix + "_filtered_forest.txt"
savannah_output = open(savannahfile,"w")
forest_output = open(forestfile,"w")
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

# copy files to data directory for use
command = ["cp",savannahfile,"../" + savannahfile]
iv.run_and_report(command,"Cannot copy " + savannahfile + " into data directory")
command = ["cp",forestfile,"../" + forestfile]
iv.run_and_report(command,"Cannot copy " + forestfile + " into data directory")
command = ["cp",structure_outfile,"../" + structure_outfile]
iv.run_and_report(command,"Cannot copy " + structure_outfile + " into data directory")


print("Savannah samples after filtering:",int(savcount))
print("Forest samples after filtering:",int(forcount))
print("Hybrid samples (removed):",int(hybcount))
