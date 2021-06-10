# This program takes the results of a SCAT2 -H2 run on joint savannah
# and forest (no hybrids) data, and an archive of old fammatch inputs.
# It creates subregion directories for all subregions in which samples
# were found, pulls old inputs from the archive, and sets up for fammatch
# runs (but does not run them).

# It updates the archive with files from this seizure.  The archive must
# exist and contain a subdirectory for each subregion, but need not contain
# any data, in which case a single-seizure fammatch will be set up. 

# If no prior samples were in a subregion, and this seizure contributes
# exactly one sample, the sample will be archived as usual but fammatch
# cannot be run.  This will be signaled by creation of a file
# named ONLY_ONE_SAMPLE in the subregion run directory.

# This program also writes run scripts to the subregional directories,
# where needed.

# BE SURE TO SET "nsub" APPROPRIATELY (number of subregions)!
# Also, if you change which subregions are forest versus savannah, you
# will need to check both this program and all downstream programs.
# They all assume that sub0 and sub1 are forest and all others are savannah.

nsub = 6

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

def write_run_script(subreg):
  # takes a NUMERIC subregion, derives the other forms
  subregid = str(subreg)
  subdir = "sub" + subregid
  outfile = open(subdir+"/"+"runrscript.sh","w")
  if subreg == 0 or subreg == 1:
    species = "forest"
  else:
    species = "savannah"
  refname = "refs" + subregid + "_fammatch.csv"
  oldname = "old" + subregid + ".txt"
  newname = "new" + subregid + ".txt"
  outline = "Rscript calculate_LRs.R " + species + " " + refname + " " + oldname + " " + newname + "\n"
  outfile.write(outline)
  outfile.close()

#############################
# main program

import sys
import os
from os import path
from os import listdir

if len(sys.argv) != 5:
  print("USAGE:  make_fammatch_incremental prefix scatdir famarchive regionfile.txt")
  exit(-1)

prefix = sys.argv[1]
scatdir = sys.argv[2]
if not scatdir.endswith("/"):
  scatdir += "/"
archivedir = sys.argv[3]
if not archivedir.endswith("/"):
  archivedir += "/"
regionfile = sys.argv[4]
hybfile = scatdir + "Output_hybrid"
genofile = "../" + prefix + "_conjoint_nohybrids.txt"

# read subregion assignments from scat
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

refheader = "FH67,FH71,FH19,FH129,FH60,FH127,FH126,FH153,FH94,FH48,FH40,FH39,FH103,FH102,S03,S04\n"

for subreg in range(0,nsub):
  if len(seizure[subreg]) == 0:  continue  # nothing to be done for this one

  # make the subregional directories
  subregid = str(subreg)
  subdir = "sub" + subregid
  os.mkdir(subdir)
  subdir += "/"

  # write reference files
  # "long" format -- 2 lines per sample, no ID, with headers
  outfile = open(subdir+"ref"+str(subreg)+"_fammatch.csv","w")
  outfile.write(refheader)
  for line in reference[subreg]:
    data = line[2:]
    outline = ",".join(data) + "\n"
    outfile.write(outline)
  outfile.close()

  # collect lines for new file
  # "wide" format -- 1 line per sample, doubled header with Match ID
  newlines = []
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
    newlines.append(outline)

  # archive the new file 
  archfilename = archivedir + prefix + "_" + subregid + ".txt"
  write_fammatch(archfilename,header,newlines)

  # construct working new and old files
  # two possibilities:  old files for this subregion do or do not exist in archive
  # if they exist, we make the working old file by catenation and use new file as-is
  # if they do not exist, we make the working old file as the first entry from the new file
  # and the working new file as the remainder
  # in either case we have to archive the whole new file (including the first entry)

  # SPECIAL CASE:  there is exactly one entry in the new file, and no entries in old
  # then we do not make old and new files (though we still archive) and we write a
  # signal file ONLY_ONE_SAMPLE instead.

  # obtain old files from archive
  oldfiles = []
  for filename in listdir(archivedir):
    # only use the right kind of files
    if not filename.endswith(subregid + ".txt"):  continue
    # don't use files for this seizure
    if filename.startswith(prefix):  continue
    oldfiles.append(filename)

  oldfilename = subdir + "old" + subregid + ".txt"
  newfilename = subdir + "new" + subregid + ".txt"

  # case 1:  no old files for this subregion
  # we will make an old file using first line of new file, and new file containing the rest
  if len(oldfiles) == 0:
    if len(newlines) > 1:
      # usual case
      oldlines = newlines[0]
      newlines = newlines[1:]
      write_fammatch(oldfilename,header,oldlines)
      write_fammatch(newfilename,header,newlines)
      write_run_script(subreg)
    else:
      # special case:  only one new sample, can't run fammatch
      sigfile = open(subdir + "ONLY_ONE_SAMPLE","w")
      outline = "We found only one sample in this subregion and there were no prior samples."
      sigfile.write(outline)
      outline = "Sample has been archived, but fammatch cannot be run on one sample."
      sigfile.write(outline)
      sigfile.close()
    continue

  # case 2:  old files exist
  write_fammatch(newfilename,header,newlines)
  oldlines = []
  for oldpart in oldfiles:
    print("Adding",oldpart)
    header, outlines = read_infile(oldpart)
    oldlines += outlines
  write_fammatch(oldfilename,header,oldlines)
  write_run_script(subreg)

print("Ready to run familial matching")
