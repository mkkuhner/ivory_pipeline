# this program imports false-positive rates from previously
# conducted simulations, and uses them to weight observed matches
# in seizure data. 
# DMs are upweighted compared to relative matches by a factor
# "dm_bonus".  Only logLR >= "cutoff' is considered as a match.

# we assume that the input obsLRs files produced by the family matching
# code are in a hardcoded list of directories (see "obsnames").

# this version separates forest and savannah matches

# we also read a local file of seizure modifications and modify the
# seizures used accordingly.

#  NOTE:
# there is a horrible hack which transforms elephant sample 64.23 into 
# its correct name, 64.230.  This should be REMOVED when we switch over
# to calling elephants like this TW64.230.  We also remove elephant
# UWA.EBB.029 who is a dupe of UWA.EBB.017-USA.EBB.029.

## functions

def whichbin(item,binbounds):
  if item < binbounds[0]:  return None
  if item >= binbounds[-1]:  return len(binbounds) - 1
  for i in range(0,len(binbounds)-1):
    if item >= binbounds[i] and item < binbounds[i+1]:
      return i
  assert False  # can't get here!?

def munge_name(name):
  # turn a name of form "UGA, 01-19, 3.3t" to "UGA 01-19 3.3"
  newname = name.split(",")
  if newname[2][-1] == "t":
    newname[2] = newname[2][:-1]
  elif newname[2][-1] == "t":
    newname[2] = newname[2][0:-2] + newname[2][-1]
  newname = "".join(newname)
  return newname


## main program

import sys
import numpy
import math
import statistics

if len(sys.argv) != 6:
  print("USAGE: python3 create_network_input.py metadata dmfile seizure_modifications LR_cutoff minloci")
  print("Familial matching filenames are HARDCODED--check before running!")
  print("Assumes the existance of a file 'fprates.tsv' in run directory")
  exit()

metafilename = sys.argv[1]
dmfilename = sys.argv[2]
seizure_modname = sys.argv[3]
cutoff = float(sys.argv[4])
minloci = int(sys.argv[5])
dm_bonus = 5.0

obsnames = {}
obsnames["forest"] = ["sub0/obsLRs.forest.txt","sub1/obsLRs.forest.txt"]
obsnames["savannah"] = ["sub2/obsLRs.savannah.txt","sub3/obsLRs.savannah.txt",
  "sub4/obsLRs.savannah.txt", "sub5/obsLRs.savannah.txt"]

splist = ["forest","savannah"]

# read metadata file and construct mapping of match ID to seizure name
sdict = {}
for line in open(metafilename,"r"):
  line = line.rstrip().split("\t")
  if line[0] == "Seizure file":
    continue    # skip header
  matchid = line[1]
  seizure = line[0]
  sdict[matchid] = seizure

# read seizure modifications file
rejected_seizures = []
merged_seizures = {}
state = None
for line in open(seizure_modname,"r"):
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

# read the file of direct matches
dmspec = {}
dmseiz = {}
for line in open(dmfilename,"r"):
  pline = line.rstrip().split("\t")
  sid1 = pline[0]
  sid2 = pline[1]
  seiz1 = pline[2]
  seiz2 = pline[3]
  spec = pline[4]

  sids = tuple(sorted([sid1,sid2]))
  seizs = tuple(sorted([seiz1,seiz2]))

  if spec not in ["F","S","H"]:
    print("In file",dmfilename,"an invalid species of",spec,"was found")
    print("on line:",line)
    exit()

  if sids in dmspec:  # or sids in dmseiz
    print("In file",dmfilename,"a duplicate entry for samples",sid1,"and",sid2,"was found")
    print("on line:",line)
    origline = "\t".join([sid1,sid2,dmseiz[0],dmseiz[1],dmspec[sids],"\n"])
    print("and on line:",origline)
    exit()

  # the following must be synced with the internal definition of variable "splist"
  if spec == "F":
    spec = "forest"
   
  if spec == "S":
    spec = "savannah"

  if spec == "H":
    spec = "forest" 

  dmspec[sids] = spec
  dmseiz[sids] = seizs
         
# do the following for each species separately
# read obsLRs files and collect logLRs
# DMs are collected separately because they will get a higher weight

allseizures = set()
LRs = {}
relpairs = {}
dmpairs = {}
ncompares = {}

for species in splist:
  LRs[species] = []
  relpairs[species] = {}
  dmpairs[species] = {}
  ncompares[species] = {}

  for obsfilename in obsnames[species]:
    for line in open(obsfilename,"r"):
      line = line.rstrip().split("\t")
      if line[0] == "s1":  
        s1_ind = line.index("s1")
        s2_ind = line.index("s2")
        dm_ind = line.index("DM_LR")
        loci_ind = line.index("nloci")
        continue
      s1 = line[s1_ind]
      # this elephant's name is mangled by R code
      if s1 == "64.23":  s1 = "64.230"
      s2 = line[s2_ind]
      if s2 == "64.23":  s2 = "64.230"
      # this elephant is a duplicate that should have been removed
      if s1 == "UWA.EBB.029" or s2 == "UWA.EBB.029":
        continue

      sids = tuple(sorted([s1,s2]))
      if sids in dmspec:
        continue
      
      seize1 = sdict[s1]
      seize2 = sdict[s2]
      # if either seizure has been rejected, bail out
      if seize1 in rejected_seizures or seize2 in rejected_seizures:
        continue
      # if either seizure has been merged, rename to merged name
      if seize1 in merged_seizures:
        seize1 = merged_seizures[seize1]
      if seize2 in merged_seizures:
        seize2 = merged_seizures[seize2]
      allseizures.add(seize1)
      allseizures.add(seize2)
      data = line[dm_ind:loci_ind]
      data = [float(x) for x in data]
      nloci = int(line[-1])
      if nloci < minloci:  continue   # discard pairs with too much missing
      top_LR = math.log10(max(data))
      LRs[species].append(top_LR)
      s = [seize1,seize2]
      s.sort()
      s = tuple(s)
      if s not in ncompares[species]:
        ncompares[species][s] = 0
      ncompares[species][s] += 1
      if top_LR >= cutoff:
        if data[0] != 0.0:
          if math.log10(data[0]) == top_LR:   # it's a DM
            print("Found a Charlie DM not previously seen?")
            print(s1,s2,seize1,seize2)
            if s not in dmpairs[species]:
              dmpairs[species][s] = []
            dmpairs[species][s].append(top_LR)
        else:
          if s not in relpairs[species]:
            relpairs[species][s] = []
          relpairs[species][s].append(top_LR)

# now merge in the cannonical list of seizure direct matches
# it is assumed that the cannonical list seizure names are correct
# and that each one has at least 13 out of 16 loci
dm_LR = 10.0
print("DMs used in this analysis:")
for sids in dmspec:
  species = dmspec[sids]
  s = dmseiz[sids]
  if s not in dmpairs[species]:
    dmpairs[species][s] = []
  dmpairs[species][s].append(dm_LR)
  LRs[species].append(dm_LR)
  if s not in ncompares[species]:
    ncompares[species][s] = 0
  ncompares[species][s] += 1
  allseizures.add(s[0])
  allseizures.add(s[1])
  print(sids[0],sids[1],s[0],s[1])

# correct seizure comparisons for fp rates
allseizures = list(allseizures)

# read false-positive rates from file (these come from sims)
fprates = {}
fprates["forest"] = []
fprates["savannah"] = []
fpbins = {}
fpbins["forest"] = []
fpbins["savannah"] = []

for line in open("fprates.tsv","r"):
  line = line.rstrip().split("\t")
  if line[0] == "forest":
    species = "forest"
    continue
  if line[0] == "savannah":
    species = "savannah"
    continue
  fpbins[species].append(float(line[0]))
  fprates[species].append(float(line[1]))

# sort ivory observations into logLR bins
observed = {}
weights = {}
for species in splist:
  observed[species] = [0.0 for x in fpbins[species]]
  weights[species] = [0.0 for x in fpbins[species]]

for species in splist:
  print(species)
  for bestLL in LRs[species]:   # this includes DMs:  I think that's OK
    mybin = whichbin(bestLL,fpbins[species])
    if mybin is not None:
      observed[species][mybin] += 1

  # obtain the weight for each bin
  numcompares = len(LRs[species])
  for binno,obs,rate in zip(range(0,len(fpbins[species])),observed[species],fprates[species]):
    expected = rate * numcompares
    assert obs > expected
    if obs > 0:
      wt = float(obs-expected)/obs
    else:
      assert False
    weights[species][binno] = wt
    print(fpbins[species][binno],obs,expected,weights[species][binno])
  
# weight the ivory matches between each pair of seizures that has any
similarity = {}
# union of relpairs and dmpairs keys
seizepairs = list(relpairs["forest"].keys()) + list(dmpairs["forest"].keys()) + list(relpairs["savannah"].keys()) + list(dmpairs["savannah"].keys())
seizepairs = list(set(seizepairs))
seizepairs.sort()
for s in seizepairs:
  compval = 0.0
  for species in splist:
    if s in relpairs[species]:
      for item in relpairs[species][s]:
        mybin = whichbin(item,fpbins[species])
        compval += weights[species][mybin]
    if s in dmpairs[species]:
      for item in dmpairs[species][s]:
        mybin = whichbin(item,fpbins[species])
        compval += dm_bonus * weights[species][mybin] 
  similarity[s] = compval

# write two input files for network analysis
# these are similarities, not distances as before

nodefile = open("seizure_nodes.csv","w")
nline = "Seizure\n"
nodefile.write(nline)

edgefile = open("seizure_edges.csv","w")
eline = "Seizure1,Seizure2,Similarity\n"
edgefile.write(eline)

# write node file
for s1 in allseizures:
  name1 = munge_name(s1)
  nline = name1 + "\n"
  nodefile.write(nline)
  
# write edge file
for s in seizepairs:
  name1 = munge_name(s[0])
  name2 = munge_name(s[1])
  if name1 == name2:  continue
  eline = name1 + "," + name2 + "," + str(similarity[s]) + "\n"
  edgefile.write(eline)
    
nodefile.close()
edgefile.close()

# write seperate forest and savannah counts of number of comparisons
totalcompares = {}
for species in splist:
  totalcompares[species] = 0
  for p in ncompares[species]:
    totalcompares[species] += ncompares[species][p]
outfilename = "totalcompares.tsv"
outfile = open(outfilename,"w")
for species in splist:
  line = species + "\t" + str(totalcompares[species]) + "\n"
  outfile.write(line)
print("Wrote comparison counts for each species to",outfilename)

# write seperate forest and savannah lists for ryan
forestpairs = list(set(list(relpairs["forest"].keys()) + list(dmpairs["forest"].keys())))
savannahpairs = list(set(list(relpairs["savannah"].keys()) + list(dmpairs["savannah"].keys())))

spsim = {}
for species in splist:
  spsim[species] = {}
for s in seizepairs:
  compval = {}
  compval["forest"] = 0
  compval["savannah"] = 0
  for species in splist:
    if s in relpairs[species]:
      for item in relpairs[species][s]:
        mybin = whichbin(item,fpbins[species])
        compval[species] += weights[species][mybin]
    if s in dmpairs[species]:
      for item in dmpairs[species][s]:
        mybin = whichbin(item,fpbins[species])
        compval[species] += dm_bonus * weights[species][mybin] 
  for species in splist:
    spsim[species][s] = compval[species]

ryanfile  = open("ryanfile.tsv","w")
ryanfile.write("forest\n")
for s in forestpairs:
  if s[0] == s[1]: continue
  outline = s[0] + "\t" + s[1] + "\t" + str(spsim["forest"][s]) + "\n"
  ryanfile.write(outline)

ryanfile.write("savannah\n")
for s in savannahpairs:
  if s[0] == s[1]: continue
  outline = s[0] + "\t" + s[1] + "\t" + str(spsim["savannah"][s]) + "\n"
  ryanfile.write(outline)

