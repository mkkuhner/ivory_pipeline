# This program makes a reference file with both forest and savannah, but
# no hybrids, based on EBhybrids output.  Note the hardwired cutoff!

cutoff = 0.5

import sys
if len(sys.argv) != 2:
  print("USAGE:  remove_hybrids_from_reference.py REF_PREFIX")
  exit(-1)

prefix = sys.argv[1]

reffile = prefix+"_known.txt"
ebfile = prefix+"_hybt.txt"

# read ebhybrids
speciesdict = {}
for line in open(ebfile,"r"):
  if line.startswith("Sample"):  continue
  line = line.rstrip().split()
  id = line[0]
  savannah = float(line[1])
  forest = float(line[2])
  hybs = [float(x) for x in line[3:]]
  sumhybs = sum(hybs)
  if sumhybs > cutoff:
    speciesdict[id] = "H"
  elif savannah >= forest:
    speciesdict[id] = "S"
  else:
    speciesdict[id] = "F"

# read and filter file
outfile = open(prefix+"_nohybrids.txt","w")
for line in open(reffile,"r"):
  saveline = line
  line = line.rstrip().split()
  id = line[0]
  if speciesdict[id] == "H":  continue  # discard hybrids
  outfile.write(saveline)

outfile.close()
