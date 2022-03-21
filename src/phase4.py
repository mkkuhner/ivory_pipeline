# Process all current seizures except those excluded by the seizure_modifications 
# file, computing overall match probabilities and drawing a network diagrom.  
# NB:  This program is INTERACTIVE in the network diagram step; you have the 
# opportunity to pretty up the diagram before it is saved.  You can always rerun 
# that step, by itself, if dissatisfied.

# Takes an input argument of the path to a DM (direct matches, AKA exact matches)
# file; this is not kept in standard archives for security reasons as it has
# quite a bit of primary data in it.

# Run in the parent directory of all seizures, AFTER familial matching has
# been run on all of them.  (TO DO:  diagnose if it has not.)

# NB:  LR is always handled in non-log form here, because it can be zero.
# The cutoff is taken in as log10(cutoff) and converted internally to non-log.

import sys, os, subprocess
from subprocess import Popen

##########################################################################
# functions

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def run_and_report(command,errormsg):
  process = Popen(command)
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

def whichbin(item,binbounds):
  if item < binbounds[0]:  return None
  if item >= binbounds[-1]:  return len(binbounds) - 1
  for i in range(0,len(binbounds)-1):
    if item >= binbounds[i] and item < binbounds[i+1]:
      return i
  assert False  # can't get here!?

def read_fprates(fpfile):
  fpbins = {}
  fprates = {}
  for line in open(fpfile,"r"):
    line = line.rstrip().split("\t")
    if line[0] == "forest":
      species = "forest"
      fpbins[species] = []
      fprates[species] = []
      continue
    if line[0] == "savannah":
      species = "savannah"
      fpbins[species] = []
      fprates[species] = []
      continue
    # transform out of log scale here
    fpbins[species].append(10.0**float(line[0]))
    fprates[species].append(float(line[1]))
  return fpbins, fprates

def read_sector_metadata(metafile):
  secdict = {}
  for line in open(metafile,"r"):
    line = line.rstrip().split()
    sec = int(line[0])
    species = line[1]
    secdict[sec] = species
  return secdict

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

# read sector metadata (mapping of sector to species)

##########################################################################
# main program

if len(sys.argv) != 5:
  print("USAGE:  python3 phase4.py ivory_paths.tsv dms.tsv LR_cutoff minloci")
  print("This program jointly does all available seizures")
  print("Be sure phase3.py has been run on all desired seizures first!")
  print("dms.tsv lists direct matches obtained by other means than fammatch")
  exit(-1)


# read ivory_paths and set up variables
ivory_paths = sys.argv[1]
pathdir = readivorypath(ivory_paths)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
mods = pathdir["seizure_modifications_prefix"]
modfile = mods[0] + mods[1]
archive = pathdir["fammatch_archive_dir"]
archivefile = archive[0] + archive[1]
metadata = pathdir["metadata_prefix"]
metafile = metadata[0] + metadata[1] + ".tsv"
sector_metafile = ivory_dir + "aux/sector_metadata.tsv"

dmfile = sys.argv[2]
LR_cutoff = float(sys.argv[3])
minloci = int(sys.argv[4])

# constants

dm_multiplier = 5.0
dm_LR = 100.0

# immediately test access to key files

if not os.path.isfile(archivefile):
  print("Cannot find fammatch archive:  did you forget to hook up the external HD?")
  print("Location tried was",archivedir)
  exit(-1)

# check that DM file exists
if not os.path.isfile(dmfile):
  print("Cannot open DM file (exact matches): ",dmfile)
  exit(-1)


splist = ["forest","savannah"]

# read fprates.tsv for false positive rates from simulated data
fpfile = ivory_dir + "aux/fprates.tsv"
fps = {}
for sp in splist:
  fps[sp] = []
whichspecies = None
for line in open(fpfile,"r"):
  line = line.rstrip().split()
  if line[0] == "forest"
    whichspecies = "forest"
    continue
  if line[0] == "savannah"
    whichspecies = "savannah"
    continue
  assert whichspecies is not None
  fps[whichspecies].append([float(line[0]),float(line[1])))

# pull an ALL seizures database report as input data
progname = ivory_dir + "src/fammatch_database.py"
reportfile = "fammatch_global.tsv"

# I thought we could filter on LR here but we can't, as we need to calculate
# numcompares; I therefore send 0 as the minimum LR
command = ["python3",progname,archivefile,"report","ALL",reportfile,"0.0",str(minloci)]
run_and_report(command,"Unable to pull report from fammatch database ",archivefile")

# read seizure_modifications file
rejected_seizures, merged_seizures = read_seizure_mods(modfile)
secdict = read_sector_metadata(sector_metafile)

# read DM file; if we later find these entries in the database we will
# discard them.  We discard DMs for rejected seizures here, and correct
# names for modified ones
dms = {}
for line in open(dmfile,"r"):
  line = line.rstrip().split("\t")
  sz1 = line[2]
  sz2 = line[3]
  if sz1 or sz2 in rejected_seizures:  continue
  if sz1 in merged_seizures:
    sz1 = merged_seizures[sz1]
  if sz2 in merged_seizures:
    sz2 = merged_seizures[sz2]
  spec = line[4]
  if spec == "F":  species = "forest"
  elif spec == "S":  species = "savannah"
  else:  continue  # don't want hybrids
  sid1 = line[0]
  sid2 = line[1]
  sids = tuple(sorted([sid1,sid2])
  if species not in dms:
    dms[species] = {}
  dms[species][sids] = [sz1, sz2]

# filter database report based on seizure_modifications and DMs
# rules:  delete all lines mentioning a REJECT seizure
#         rename MERGE seizures
#         delete previously identified DMs
# we do not need to handle minloci as this is done by the fammatch_database.
# we do not filter out low LRs as we have to count them
datalines = {}
for line in open(reportfile,"r"):
  line = line.rstrip().split("\t")
  if line[0] == "secno":     # header
    s1_index = line.index["s1"]
    s2_index = line.index["s2"]
    sz1_index = line.index["sz1"]
    sz2_index = line.index["sz2"]
    sec_index = line.index["secno"]
    dm_ind = line.index["DM"]
    loci_ind = line.index["nloci"]
    continue
  sz1 = line[sz1_index]
  sz2 = line[sz2_index]
  # rejected seizure
  if sz1 or sz2 in rejected_seizures:  continue
  # merged seizure
  if sz1 in merged_seizures:
    line[sz1_index] = merged_seizures[sz1]
  if sz2 in merged_seizures:
    line[sz2_index] = merged_seizures[sz2]
  s1 = line[s1_index]
  s2 = line[s2_index]
  key = tuple(sorted([s1,s2]))
  species = secdict[line[sec_index]]
  # remove previously identified DMs
  if key in dms[species]:
    continue
  if species not in datalines:
    datalines[species] = {}
  datalines[species][key] = line

# read false positives rates from sims
fpfile = ivory_dir + "aux/fprates.tsv"
fpbins, fprates = read_fprates(fpfile)

allseizures = set()
LRs = {}
relpairs = {}
dmpairs = {}
ncompares = {}
cutoff_nonlog = 10.0**cutoff
allpairs = set()

for species in splist:
  LRs[species] = []
  relpairs[species] = {}
  dmpairs[species] = {}
  ncompares[species] = {}
  for key, line in datalines[species]:
    # removed some mangled-elephant-name code here, hopefully no longer needed!
    # problem elephants were 64.230 and UWA.EBB.029
    sz1 = line[sz1_index]
    sz2 = line[sx1_index]
    allseizures.add(sz1)
    allseizures.add(sz2)
    LRs = [float(x) for x in line[dm_ind:loci_ind]]
    top_LR = max(LRs)
    LRs[species].append(top_LR)
    seizepair = [sz1,sz2]
    seizepair.sort()
    seizepair = tuple(seizepair)
    if seizepair not in ncompares[species]:
      ncompares[species][seizepair] = 0
    ncompares[species][seizepair] += 1
    if top_LR >= cutoff_nonlog:
      allpairs.add(seizepair)
      if LRs[0] == top_LR:   # a DM not found in the DMs file
        if seizepair not in dmpairs[species]:
          dmpairs[species][seizepair] = []
        dmpairs[species][seizepair].append(top_LR)
      else:                  # not a DM
        if seizepair not in relpairs[species]:
          relpairs[species][seizepair] = []
        relpairs[species][seizepair].append(top_LR)
        
  # handle pre-identified DMs
  print("Pre-specified DMs for",species)
  for match in dms[species]: 
    sz1, sz2 = dms[species][match]
    seizepair = tuple(sorted([sz1,sz2]))
    allpairs.add(seizepair)
    if seizepair not in dmpairs[species]:
      dnpairs[species][seizepair] = []
    dmpairs[species][seizepair].append(dm_LR)
    LRs[species].append(dm_LR)
    if seizepair not in ncompares[species]:
      ncompares[species][seizepair] = 0
    ncompares[species][seizepair] += 1
    allseizures.add(sz1)
    allseizures.add(sz2)
    print(match[0],match[1],sz1,sz2)

# sort observations into bins
allseizures = list(allseizures)
observed = {}
weights = {}
for species in splist:
  numbins = len(fpbins[species])
  observed[species] = [0.0 for x in fpbins[species]]
  weights[species] = [0.0 for x in fpbins[species]]
  for bestLL in LRs[species]:   # this includes DMs:  I think that's OK
    mybin = whichbin(bestLL, fpbins[species])
    if mybin is not None:
      observed[species][mybin] += 1
    # obtain weights for each bin 
    numcompares = len(LRs[species])
    for binno, obs, rate in zip(range(0,numbins),observed[species],fprates[species])
      expected = rate * numcompares
    assert obs > expected
    if obs > 0:
      wt = float(obs-expected)/obs
    else:
      assert False
    weights[species][binno] = wt
    print(fpbins[species][binno],obs,expected,weights[species][binno])

# calculate seizure-pair matches for all pairs that have any
similarity = {}
allpairs = list(allpairs)
allpairs.sort()
for seizepair in allpairs:
  compval = 0.0
  for species in splist:
    if seizepair in relpairs[species]:
      for item in relpairs[species][seizepair]:
        mybin = whichbin(item,fpbins[species])
        compval += weights[species][mybin]
    if seizepair in dmpairs[species]:
      for item in dmpairs[species][seizepair]:
        mybin = whichbin(item,fpbins[species])
        compval += dm_bonus * weights[species][mybin]
  similarity[seizepair] = compval

# write nodes and edges files for network analysis
# values are similarities, not distances

# node file
nodefile = open("seizure_nodes.csv","w")
nline= "Seizure\n"
nodefile.write(nline)
for sz in allseizures:
  nline = sz + "\n"
  nodefile.write(nline)
nodefile.close()

# edge file
edgefile = open("seizure_edges.csv","w")
eline = "Seizure1,Seizure2,Similarity\n"
edgefile.write(eline)
for sz1, sz2 in allpairs:
  if sz1 == sz2:  
    print("Found a within-seizure match in ",sz1)
    continue
  eline = [sz1,sz2,str(similarity((sz1,sz2)))]
  eline = ",".join(eline) + "\n"
  edgefile.write(eline)
edgefile.close()
