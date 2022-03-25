
# update the seizure_metadata file with info from a new seizure
# this program updates its input file IN PLACE
# it will silently rename previously seen samples

# meant to be run in the main directory of the specific seizure

##########################################################################
# main program

import sys
if len(sys.argv) != 3:
  print("USAGE:  update_metadata.py metafile.tsv PREFIX")
  print("WARNING:  this program updates the file IN PLACE.")
  exit(-1)

metafile = sys.argv[1]
prefix = sys.argv[2]
seizurefile = sys.argv[2]+"_unknowns.txt"

# read sample ids from new seizure
sids = set()
for line in open(seizurefile,"r"):
  line = line.rstrip().split()
  sids.add(line[0])

newsids = list(sids)

# read old metadata file, if any
outlines = []
import os
if os.path.isfile(metafile):
  for line in open(metafile,"r"):
    outline = line
    line = line.rstrip().split("\t")
    if line[0].startswith("Seizure"):  continue
    sid = line[1]
    if sid in newsids:
      # renaming an existing entry
      outline = prefix + "\t" + sid + "\n"
    outlines.append(outline)

# add new sids to it
for sid in newsids:
  # adding a new entry
  outline = prefix + "\t" + sid + "\n"
  outlines.append(outline)

# rewrite the file
outfile = open(metafile,"w")
for line in outlines:
  outfile.write(line)

outfile.close()
