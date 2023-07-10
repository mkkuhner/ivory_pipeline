# This program reports on hybrids detected (and excluded) from a
# pipeline run.  hybrid_cutoff should be a number between 0.0 and 1.0;
# animals with that chance or higher of being hybrid will be tagged
# as such.

import sys

if len(sys.argv) != 3:
  print("USAGE: python makehybridreport.py prefix hybrid_cutoff")
  print("  uses the file prefix_hybt.txt as input")
  exit(-1)

prefix = sys.argv[1]
ebfile = prefix + "_hybt.txt"
cutoff = float(sys.argv[2])
hyboutname = prefix + "_hybout.tsv"

savcount = 0
forcount = 0
hybcount = 0
call_list = []

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

# read ebhybrids and classify
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
    call_list.append([id,sumhybs])
  elif savannah >= forest:
    speciesdict[id] = "S"
    savcount += 1
  else:
    speciesdict[id] = "F"
    forcount += 1
  vals = [max([savannah,forest,sumhybs]),sumhybs,savannah,forest]
  vals = [str(round(x,4)) for x in vals]
  outentry = [id,speciesdict[id]] + vals
  call_list.append(outentry)

hybout = open(hyboutname,"w")
outline = "SID\tCall\tCallProb\tHybrid\tSavannah\tForest\n"
hybout.write(outline)
call_list.sort()
for entry in call_list:
  entry = "\t".join(entry) + "\n"
  hybout.write(entry)
hybout.close()

#print("Counts and listings written to",hyboutname)
