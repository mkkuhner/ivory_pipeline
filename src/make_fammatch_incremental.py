# This program sets up all needed files to run familial matching for
# a new seizure, matching with archived results from previous seizures.
# It does not actually run the familial matching code.

# Inputs:
# PREFIX
# prefix of SCAT output directories
# Archive of old fammatch input files
# prefix of zonefiles (used to assign reference samples to sectors)

# The archive of old fammatch inputs must contain 1 directory per sector.
# However, it is acceptable for any or all of these directories to be
# empty.  It must also contain a file named "sector_metadata.txt"
# which establishes the number and kind of sectors.

# Files assumed to be present:
# ../PREFIX_[species].txt (note this is one directory rootwards) for species used
# archive/sector_metadata.txt

# Outputs:
# secdirectory (named subN) for each sector for which matching should be run
# in each secdirectory:
#   reference file
#   old seizure and new seizure sample files 
#   run script 

# NOTE:  If there was just one sample in a given sector in this seizure,
# and no previous samples in the archive, the secdirectory will be created
# but fammatch cannot be run.  This will be signaled by presence of a file
# ONLY_ONE_SAMPLE in the secdirectory, and absence of the other files.

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

def write_reference(secdir,sectorid,refdata):
  # write reference files
  # "long" format -- 2 lines per sample, no ID, with headers
  refheader = "FH67,FH71,FH19,FH129,FH60,FH127,FH126,FH153,FH94,FH48,FH40,FH39,FH103,FH102,S03,S04\n"
  outfile = open(secdir + "ref" + sectorid + "_fammatch.csv","w")
  outfile.write(refheader)
  for line in refdata:
    data = line[2:]
    outline = ",".join(data) + "\n"
    outfile.write(outline)
  outfile.close()

def write_run_script(sector, secdict):
  # takes a NUMERIC sector, derives the other forms
  secid = str(sector)
  secdir = "sub" + secid
  outfile = open(secdir+"/"+"runrscript.sh","w")
  species = secdict[sector]
  refname = "ref" + secid + "_fammatch.csv"
  oldname = "old" + secid + ".txt"
  newname = "new" + secid + ".txt"
  outline = "Rscript calculate_LRs.R " + species + " " + refname + " " + oldname + " " + newname + "\n"
  outfile.write(outline)
  outfile.close()

def read_sector_metadata(metafile):
  secdict = {}
  for line in open(metafile,"r"):
    line = line.rstrip().split()
    sec = int(line[0])
    species = line[1]
    secdict[sec] = species
  return secdict

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

# rewrite plan:
# read sector_metadata.txt to establish which sectors are which species
# for each species present in seizure; do the whole setup, with the
# appropriate zonefile etc.
# when all species are done, write sector-specific output files

if len(sys.argv) != 5:
  print("USAGE:  make_fammatch_incremental PREFIX scatdir_prefix famarchive zone_prefix")
  print("Expects file ../PREFIX_[species].txt for each species in this seizure to exist")
  exit(-1)

prefix = sys.argv[1]
scatdir_prefix = sys.argv[2]
archivedir = dirpath(sys.argv[3])
if not archivedir.endswith("/"):  archivedir += "/"
zone_prefix = sys.argv[4]

header = "Match ID,FH67,FH67,FH71,FH71,FH19,FH19,FH129,FH129,FH60,FH60,FH127,FH127,FH126,FH126,FH153,FH153,FH94,FH94,FH48,FH48,FH40,FH40,FH39,FH39,FH103,FH103,FH102,FH102,S03,S03,S04,S04\n"

specieslist = ["forest","savannah"]
hybfile = {}
genofile = {}
zonefile = {}
for species in specieslist:
  hybfile[species] = scatdir_prefix + "_" + species + "/" + "Output_hybrid"
  genofile[species] = "../" + prefix + "_" + species + ".txt"
  zonefile[species] = zone_prefix + "_" + species + ".txt"

# read sector metadata file from archive directory
# this establishes number and type of sectors
metafile = archivedir + "sector_metadata.txt"
secdict = read_sector_metadata(metafile)
nsec = len(secdict)
seizure = [[] for x in range(0,nsec)]
reference = [[] for x in range(0,nsec)]

for species in specieslist:
  if not path.exists(hybfile[species]):
    continue   # no samples for this species, it can be ignored

  # assign seizure samples to sectors based on SCAT
  id_sector = {}
  for line in open(hybfile[species],"r"):
    line = line.rstrip().split()
    if line[0] == "Hybridcheck": 
      assert line[1] == "=2"
      continue
    if line[0] == "Individual":
      continue
    id = line[0]
    probs = [float(x) for x in line[1:nsec+1]]
    bestprob = max(probs)
    sector = probs.index(bestprob)
    id_sector[id] = sector

  # assign reference samples to sectors based on zonefiles
  # note that some zones have different sectors depending on species, so
  # this is done for one species at a time and not pooled!
  reg_sector = {}
  for line in open(zonefile[species],"r"):
    line = line.rstrip().split()
    reg = line[1]
    sector = line[2]
    reg_sector[reg] = sector

  # read and classify genotypes

  for line in open(genofile[species],"r"):
    line = line.rstrip().split()
    id = line[0]
    reg = line[1]
    if reg == "-1":      # ivory sample
      sector = id_sector[id]
      sector = int(sector)
      seizure[sector].append(line)
    else:                # reference sample
      sector = reg_sector[reg]
      sector = int(sector)
      reference[sector].append(line)

# write fammatch input files

for sector in range(0,nsec):
  if len(seizure[sector]) == 0:  continue  # nothing to be done for this one

  # make the sector directory
  sectorid = str(sector)
  secdir = "sub" + sectorid
  os.mkdir(secdir)
  secdir += "/"

  # collect lines for this seizure's samples
  # "wide" format -- 1 line per sample, doubled header with Match ID
  currlines = []
  for line1, line2 in zip(seizure[sector][0::2], seizure[sector][1::2]):
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
  archfilename = archivedir + secdir + prefix + "_" + sectorid + ".txt"
  write_fammatch(archfilename,header,currlines)

  # fammatch uses an input file of previous seizure data ("old") and
  # an input file of current seizure data ("new"):  it matches old with new,
  # and new with new, but not old with old.

  # If previous seizure data for this sector are in the archive, the
  # "old" file contains these data and "new" contains current seizure data.

  # If the archive has nothing, the "old" file contains the first entry for
  # the current seizure and "new" contains the remainder.  If there is
  # only one entry for the current seizure, familial matching cannot
  # be run for this sector:  we write a signal file ONLY_ONE_SAMPLE
  # and no "old" and "new" files. 

  # obtain previous seizures from archive
  oldfiles = []
  for filename in listdir(archivedir + secdir):
    # only use the right kind of files
    if not filename.endswith(sectorid + ".txt"):  continue
    # don't use files for this seizure
    if filename.startswith(prefix):  continue
    oldfiles.append(archivedir + secdir + filename)

  oldfilename = secdir + "old" + sectorid + ".txt"
  newfilename = secdir + "new" + sectorid + ".txt"

  # case 1:  no previous data for this sector
  # we will make an "old" file using first line of current seizure data, 
  # and a "new" file containing the remainder
  if len(oldfiles) == 0:
    if len(currlines) > 1:
      # usual case
      prevlines = currlines[0]
      currlines = currlines[1:]
      write_fammatch(oldfilename,header,prevlines)
      write_fammatch(newfilename,header,currlines)
      write_run_script(sector, secdict)
      write_reference(secdir,sectorid,reference[sector])
    else:
      # special case:  only one new sample, can't run fammatch
      sigfile = open(secdir + "ONLY_ONE_SAMPLE","w")
      outline = "We found only one sample in this sector and there were no prior samples."
      sigfile.write(outline)
      outline = "Sample has been archived, but fammatch cannot be run on one sample."
      sigfile.write(outline)
      sigfile.close()
      # note we do not write any other files (new, old, ref, runscript)

  # case 2:  old files exist
  else:
    write_fammatch(newfilename,header,currlines)
    prevlines = []
    for oldpart in oldfiles:
      print("Adding",oldpart)
      header, outlines = read_infile(oldpart)
      prevlines += outlines
    write_fammatch(oldfilename,header,prevlines)
    write_run_script(sector, secdict)
    write_reference(secdir,sectorid,reference[sector])

print("Ready to run familial matching")
