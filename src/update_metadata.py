# update the seizure_metadata file with info from a new seizure
# this program updates its input file IN PLACE
# note that it takes both PREFIX and seizure name; the latter should
# be in comma-separated format
# it will silently rename previously seen samples

import sys
if len(sys.argv) != 4:
  print("USAGE:  update_metadata.py metafile.tsv PREFIX seizure_name")
  print("WARNING:  this program updates the file IN PLACE.")
  exit(-1)

metafile = sys.argv[1]
seizurefile = sys.argv[2]+"_unknowns.txt"
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
  outline = line
  line = line.rstrip().split("\t")
  if line[0].startswith("Seizure"):  continue
  sid = line[1]
  if sid in newsids:
    # renaming an existing entry
    outline = seizure_name + "\t" + sid + "\n"
  outlines.append(outline)

# add new sids to it
for sid in newsids:
  # adding a new entry
  outline = seizure_name + "\t" + sid + "\n"
  outlines.append(outline)

# rewrite the file
outfile = open(metafile,"w")
for line in outlines:
  outfile.write(line)

outfile.close()
