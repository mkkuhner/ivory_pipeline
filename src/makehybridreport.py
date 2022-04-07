
import sys

if len(sys.argv) != 3:
  print("USAGE: python makehybridreport.py ebhybrids_outfile hybrid_cutoff")
  print("  ebhybrids_outfile often of the form foo_hybt.txt")
  exit(-1)

ebfile = sys.argv[1]
cutoff = float(sys.argv[2])

savcount = 0
forcount = 0
hybcount = 0
hyblist = []

import os
if os.path.isfile("hybout.txt"):
  print("previous hybout.txt detected. Move, Rename or Remove file\nNothing done")
  exit(-1)

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
    hybcount += 1
    hyblist.append(id)
  elif savannah >= forest:
    speciesdict[id] = "S"
    savcount += 1
  else:
    speciesdict[id] = "F"
    forcount += 1

outline = "Found " + str(savcount) + " savannah, " + str(forcount) + " forest and "
outline += str(hybcount) + " hybrids" + "\n"
print(outline)

hybout = open("hybout.txt","w")
hybout.write(outline)
outline = "\nHybrid sids:\n"
sids_inline = 5
cursid = 0
for sid in hyblist:
  outline += sid + "  "
  cursid += 1
  if cursid == sids_inline:
    outline += "\n"
    cursid = 0
hybout.write(outline)

print("Counts and listings written to hybout.txt")
