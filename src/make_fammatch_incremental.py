# This program sets up all needed files to run familial matching for
# a new seizure, matching with archived results from previous seizures.
# It does not actually run the familial matching code.

# Inputs:
# PREFIX
# Directory with results of a SCAT subregion assignment (-H2) run on the seizure
# Archive of old fammatch input files
# Regionfile (used to assign reference samples to subregions)

# The archive of old fammatch inputs must contain 1 directory per subregion.
# However, it is acceptable for any or all of these directories to be
# empty.  It must also contain a file named "subregion_metadata.txt"
# which establishes the number and kind of subregions.

# Files assumed to be present:
# ../PREFIX_conjoint_nohybrids.txt (note this is one directory rootwards)
# archive/subregion_metadata.txt

# Outputs:
# subdirectory (named subN) for each subregion for which matching should be run
# in each subdirectory:
#   reference file
#   old seizure and new seizure sample files 
#   run script 

# NOTE:  If there was just one sample in a given subregion in this seizure,
# and no previous samples in the archive, the subdirectory will be created
# but fammatch cannot be run.  This will be signaled by presence of a file
# ONLY_ONE_SAMPLE in the subdirectory, and absence of the other files.

# Updating:
# input files for this seizure are added to the archive

#############################
# functions

def read_infile(infilename):
  outlines = []
  for line in open(infilename,"r"):
    if line.startswith("Match"):
      header = line
      continue
    outlines.append(line)
  return [header, outlines]

def write_fammatch(filename,header,body):
  outfile = open(filename,"w")
  outfile.write(header)
  outfile.writelines(body)
  outfile.close()

def write_reference(subdir,subregid,refdata):
  # write reference files
  # "long" format -- 2 lines per sample, no ID, with headers
  refheader = "FH67,FH71,FH19,FH129,FH60,FH127,FH126,FH153,FH94,FH48,FH40,FH39,FH103,FH102,S03,S04\n"
  outfile = open(subdir + "ref" + subregid + "_fammatch.csv","w")
  outfile.write(refheader)
  for line in refdata:
    data = line[2:]
    outline = ",".join(data) + "\n"
    outfile.write(outline)
  outfile.close()

def write_run_script(subreg, subdict):
  # takes a NUMERIC subregion, derives the other forms
  subregid = str(subreg)
  subdir = "sub" + subregid
  outfile = open(subdir+"/"+"runrscript.sh","w")
  species = subdict[subreg]
  refname = "ref" + subregid + "_fammatch.csv"
  oldname = "old" + subregid + ".txt"
  newname = "new" + subregid + ".txt"
  outline = "Rscript calculate_LRs.R " + species + " " + refname + " " + oldname + " " + newname + "\n"
  outfile.write(outline)
  outfile.close()

def read_subregion_metadata(metafile):
  subdict = {}
  for line in open(metafile,"r"):
    line = line.rstrip().split()
    subreg = int(line[0])
    species = line[1]
    subdict[subreg] = species
  return subdict

def dirpath(dirname):
  if not dirname.endswith("/"):
    dirname += "/"
  return dirname

#############################
# main program

import sys
import os
from os import path
from os import listdir

if len(sys.argv) != 5:
  print("USAGE:  make_fammatch_incremental prefix scatdir famarchive regionfile.txt")
  print("Expects a file ../PREFIX_conjoint_nohybrids.txt to exist")
  exit(-1)

prefix = sys.argv[1]
scatdir = dirpath(sys.argv[2])
archivedir = dirpath(sys.argv[3])
if not archivedir.endswith("/"):  archivedir += "/"
regionfile = sys.argv[4]
hybfile = scatdir + "Output_hybrid"
genofile = "../" + prefix + "_conjoint_nohybrids.txt"

# read subregion metadata file from archive directory
# this establishes number and type of subregions
metafile = archivedir + "subregion_metadata.txt"
subdict = read_subregion_metadata(metafile)
nsub = len(subdict)

# read subregion assignments from SCAT subregion-assignment results
# for use with seizure data
id_subreg = {}
for line in open(hybfile,"r"):
  line = line.rstrip().split()
  if line[0] == "Hybridcheck": 
    assert line[1] == "=2"
    continue
  if line[0] == "Individual":
    continue
  id = line[0]
  probs = [float(x) for x in line[1:nsub+1]]
  bestprob = max(probs)
  subreg = probs.index(bestprob)
  id_subreg[id] = subreg

# read subregion assignments from regionfile
# for use with reference data
reg_subreg = {}
for line in open(regionfile,"r"):
  line = line.rstrip().split()
  reg = line[1]
  subreg = line[2]
  reg_subreg[reg] = subreg

seizure = [[] for x in range(0,nsub)]
reference = [[] for x in range(0,nsub)]

# read and classify genotypes
for line in open(genofile,"r"):
  line = line.rstrip().split()
  id = line[0]
  reg = line[1]
  if reg == "-1":      # ivory sample
    subreg = id_subreg[id]
    subreg = int(subreg)
    seizure[subreg].append(line)
  else:                # reference sample
    subreg = reg_subreg[reg]
    subreg = int(subreg)
    reference[subreg].append(line)

# write fammatch input files

header = "Match ID,FH67,FH67,FH71,FH71,FH19,FH19,FH129,FH129,FH60,FH60,FH127,FH127,FH126,FH126,FH153,FH153,FH94,FH94,FH48,FH48,FH40,FH40,FH39,FH39,FH103,FH103,FH102,FH102,S03,S03,S04,S04\n"


for subreg in range(0,nsub):
  if len(seizure[subreg]) == 0:  continue  # nothing to be done for this one

  # make the subregional directory
  subregid = str(subreg)
  subdir = "sub" + subregid
  os.mkdir(subdir)
  subdir += "/"

  # collect lines for this seizure's samples
  # "wide" format -- 1 line per sample, doubled header with Match ID
  currlines = []
  for line1, line2 in zip(seizure[subreg][0::2], seizure[subreg][1::2]):
    data1 = line1[2:]
    data2 = line2[2:]
    id = line1[0]
    if not line2[0] == id:
      print ("unpaired entry",line1[0],line2[0])
      exit()
    outline = id
    for d1,d2 in zip(data1,data2):
      outline += "," + d1
      outline += "," + d2
    outline += "\n"
    currlines.append(outline)

  # archive this seizure's samples
  archfilename = archivedir + subdir + prefix + "_" + subregid + ".txt"
  write_fammatch(archfilename,header,currlines)

  # fammatch uses an input file of previous seizure data ("old") and
  # an input file of current seizure data ("new"):  it matches old with new,
  # and new with new, but not old with old.

  # If previous seizure data for this subregion are in the archive, the
  # "old" file contains these data and "new" contains current seizure data.

  # If the archive has nothing, the "old" file contains the first entry for
  # the current seizure and "new" contains the remainder.  If there is
  # only one entry for the current seizure, familial matching cannot
  # be run for this subregion:  we write a signal file ONLY_ONE_SAMPLE
  # and no "old" and "new" files. 
  
  # obtain previous seizures from archive
  oldfiles = []
  for filename in listdir(archivedir + subdir):
    # only use the right kind of files
    if not filename.endswith(subregid + ".txt"):  continue
    # don't use files for this seizure
    if filename.startswith(prefix):  continue
    oldfiles.append(filename)

  oldfilename = subdir + "old" + subregid + ".txt"
  newfilename = subdir + "new" + subregid + ".txt"

  # case 1:  no previous data for this subregion
  # we will make an "old" file using first line of current seizure data, 
  # and a "new" file containing the remainder
  if len(oldfiles) == 0:
    if len(currlines) > 1:
      # usual case
      prevlines = currlines[0]
      currlines = currlines[1:]
      write_fammatch(oldfilename,header,prevlines)
      write_fammatch(newfilename,header,currlines)
      write_run_script(subreg, subdict)
      write_reference(subdir,subregid,reference[subreg])
    else:
      # special case:  only one new sample, can't run fammatch
      sigfile = open(subdir + "ONLY_ONE_SAMPLE","w")
      outline = "We found only one sample in this subregion and there were no prior samples."
      sigfile.write(outline)
      outline = "Sample has been archived, but fammatch cannot be run on one sample."
      sigfile.write(outline)
      sigfile.close()
      # note we do not write any other files (new, old, ref, runscript)
    continue

  # case 2:  old files exist
  write_fammatch(newfilename,header,currlines)
  prevlines = []
  for oldpart in oldfiles:
    print("Adding",oldpart)
    header, outlines = read_infile(oldpart)
    prevlines += outlines
  write_fammatch(oldfilename,header,prevlines)
  write_run_script(subreg, subdict)
  write_reference(subdir,subregid,reference[subreg])

print("Ready to run familial matching")
