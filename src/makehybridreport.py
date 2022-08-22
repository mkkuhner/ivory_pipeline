
import sys

if len(sys.argv) != 3:
  print("USAGE: python makehybridreport.py prefix hybrid_cutoff")
  print("  uses the file prefix_hybt.txt as input")
  exit(-1)

prefix = sys.argv[1]
ebfile = prefix + "_hybt.txt"
cutoff = float(sys.argv[2])
hyboutname = prefix + "_hybout.txt"

savcount = 0
forcount = 0
hybcount = 0
hyblist = []

import os
if os.path.isfile(hyboutname):
  print("previous output detected. Move, Rename or Remove file",hyboutname,"\nNothing done")
  exit(-1)

# read the _raw file and make a list of SIDs; we will use this to distinguish
# seizure from reference data

rawfile = prefix + "_raw.tsv"
wanted_ids = []
for line in open(rawfile,"r"):
  if line.startswith("MatchID"):  continue
  line = line.rstrip().split()
  wanted_ids.append(line[0])

# read ebhybrids
speciesdict = {}
for line in open(ebfile,"r"):
  if line.startswith("Sample"):  continue
  line = line.rstrip().split()
  id = line[0] 
  if id not in wanted_ids:  continue
  savannah = float(line[1])
  forest = float(line[2])
  hybs = [float(x) for x in line[3:]]
  sumhybs = sum(hybs)
  if sumhybs >= cutoff:
    speciesdict[id] = "H"
    hybcount += 1
    hyblist.append([id,sumhybs])
  elif savannah >= forest:
    speciesdict[id] = "S"
    savcount += 1
  else:
    speciesdict[id] = "F"
    forcount += 1

outline = "Found " + str(savcount) + " savannah, " + str(forcount) + " forest and "
outline += str(hybcount) + " hybrids" + "\n"
print(outline)

hybout = open(hyboutname,"w")
hybout.write(outline)
outline = "\nHybrid SIDs and probabilities:\n"
hybout.write(outline)
hyblist.sort()
for sid,prob in hyblist:
  outline = sid + "\t" + str(prob) + "\n"
  hybout.write(outline)
hybout.close()

#print("Counts and listings written to",hyboutname)
