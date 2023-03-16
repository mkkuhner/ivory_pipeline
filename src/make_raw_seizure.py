# This program takes the data from the Ivory Genotypes Stats tabe
# of the master elephant database and creates _raw files for it.
# It does NOT create seizure directories or do any downstream processing;
# that is done by step1_fammatch.py.

# TO DO:
# read in ivory_paths.tsv
# obtain seizure_modifications from ivory_paths
# implement seizure_modifications while making raw data files

def read_seizure_mods(modfile):
  rejected_seizures = []
  merged_seizures = {}
  state = None
  for line in open(modfile,"r"):
    line = line.rstrip().split("\t")
    if line[0] == "REJECT":
      state = "reject"
      continue
    if line[0] == "MERGE":
      state = "merge"
      continue
    if state == "reject":
      assert len(line) == 1
      rejected_seizures.append(line[0])
      continue
    if state == "merge":
      # merge requires a new name and at least two old names
      assert len(line) >= 3
      newname = line[0]
      for entry in line[1:]:
        merged_seizures[entry] = newname
  return rejected_seizures, merged_seizures

################################
# main

import sys
import ivory_lib as iv

if len(sys.argv) != 3:
  print("USAGE: make_raw_seizure.py masterfile.tsv ivorypathfile")
  exit(-1)

locinames = ["FH67","FH71","FH19","FH129","FH60","FH127","FH126","FH153","FH94","FH48","FH40","FH39","FH103","FH102","S03","S04" ]
rawhdr = "MatchID\t" + "\t".join(locinames) + "\n"
xcel_seizurename = "OfficialSeizureName"
xcel_sidname = "Match ID"

ivorydict = iv.readivorypath(sys.argv[2])
ivory_seizuremod = "seizure_modifications_prefix"
seizuremodfilename = ivorydict[ivory_seizuremod][1] + ivorydict[ivory_seizuremod][2]
reject_seizures, merge_seizure = read_seizure_mods(seizuremodfilename)

masterlines = open(sys.argv[1],"r").readlines()

pline = masterlines[0].rstrip().split("\t")
seizure_ind = pline.index(xcel_seizurename)
sid_ind = pline.index(xcel_sidname)
loci_ind = {}
for lname in locinames:
  loci_ind[lname] = pline.index(lname)

outlines = {}
for line in masterlines[1:]:
  pline = line.rstrip().split("\t")
  seizure = pline[seizure_ind]
  if ", " in seizure:
    print("FAILURE: seizure named",seizure,"needs to be in mary format")
    exit(-1)
  if " " in seizure:
    print("FAILURE: seizure named",seizure,"has a name containing a space")
    exit(-1)
  if seizure in reject_seizures:
    continue
  if seizure in merge_seizure:
    seizure = merge_seizure[seizure]
  if seizure not in outlines:
    outlines[seizure] = [rawhdr,]
  sid = pline[sid_ind]
  outline1 = sid
  outline2 = sid
  for loc in loci_ind.values():
    if pline[loc] == "" or pline[loc+1] == "":
      pline[loc] = "-999"
      pline[loc+1] = "-999"
    outline1 += "\t" + pline[loc]
    outline2 += "\t" + pline[loc+1]
  outline1 += "\n"
  outline2 += "\n"
  outlines[seizure].append(outline1)
  outlines[seizure].append(outline2)

for seizure in outlines:
  seizurefile = open(seizure + "_raw.tsv","w")
  for line in outlines[seizure]:
    seizurefile.write(line)
  seizurefile.close()

print("Wrote all",len(outlines),"seizure raw files")
