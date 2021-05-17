# update the seizure_metadata file with info from a new seizure

import sys
if len(sys.argv) != 4:
  print("USAGE:  update_metadata.py metafile.tsv PREFIX_unknowns.txt seizure_name")
  print("WARNING:  this program updates the file IN PLACE.")
  exit(-1)

metafile = sys.argv[1]
seizurefile = sys.argv[2]
seizure_name = sys.argv[3]

# read sample ids from new seizure
sids = set()
for line in open(seizurefile,"r"):
  line = line.rstrip().split()
  sids.add(line[0])

newsids = list(sids)

# read old metadata file
outlines = []
for line in open(metafile,"r"):
  saveline = line
  line = line.rstrip().split("\t")
  if line[0].startswith("Seizure"):  continue
  sid = line[1]
  if sid in newsids:
    print("Sample",sid,"already present in metadata file.")
    print("Run aborting without change to metadata.")
    exit(-1)
  outlines.append(saveline)

# add new sids to it
for sid in newsids:
  outline = seizure_name + "\t" + sid + "\n"
  outlines.append(outline)

# rewrite the file
outfile = open(metafile,"w")
for line in outlines:
  outfile.write(line)

outfile.close()
