# Process all current seizures except those excluded by the seizure_modifications 
# file, computing overall match probabilities and writing files for the
# network drawing program.

# Takes an input argument of the path to a DM (direct matches, AKA exact matches)
# file; this is not kept in standard archives for security reasons as it has
# quite a bit of primary data in it.

# Run in the parent directory of all seizures, AFTER familial matching has
# been run on all of them.  (TO DO:  diagnose if it has not.)

# NOTE:  cutoff is taken in as a log, but always used as non-log to compare
# with LR values (which cannot be logged as they are often zero!)

# Results from this program will be in a directory /fammatch_overall off of
# the directory in which it is run.  Any previous results in that directory
# will be destroyed.

import sys, os, subprocess
from subprocess import Popen
import math

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
    print("Exit code " + str(exit_code))
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
archivedir = archive[0] + archive[1]
archivefile = archivedir + "elephant_msat_database.tsv"
metadata = pathdir["metadata_prefix"]
metafile = metadata[0] + metadata[1] + ".tsv"
sector_metafile = ivory_dir + "aux/sector_metadata.tsv"

dmfile = sys.argv[2]
LR_cutoff = math.log(float(sys.argv[3]),10)
minloci = int(sys.argv[4])

# constants

dm_multiplier = 5.0
dm_LR = 10.0**10.0
splist = ["forest","savannah"]

# immediately test access to key files

# check that archive file exists
if not os.path.isfile(archivefile):
  print("Cannot find fammatch archive:  did you forget to hook up the external HD?")
  print("Location tried was",archivefile)
  exit(-1)

# check that DM file exists
if not os.path.isfile(dmfile):
  print("Cannot open DM file (exact matches): ",dmfile)
  exit(-1)

# check that fprates.tsv exists
fpfile = ivory_dir + "aux/fprates.tsv"
if not os.path.isfile(fpfile):
  print("Cannot find fprates.tsv file")
  print("Location tried was",fpfile)
  exit(-1)

# check that seizure_modifications exists
if not os.path.isfile(modfile):
  print("Cannot find seizure modifications file")
  print("Location tried was",modfile)
  exit(-1)

# create output directory
outdir = "fammatch_overall/"
if os.path.isdir(outdir):
  command = ["rm","-rf",outdir]
  run_and_report(command,"Unable to delete previous results in " + outdir)
command = ["mkdir",outdir]
run_and_report(command,"Unable to create output directory " + outdir)

# get sector info
secdict = read_sector_metadata(sector_metafile)

# pull an ALL seizures database report as input data
progname = ivory_dir + "src/fammatch_database.py"
reportfile = outdir + "fammatch_global.tsv"

# I thought we could filter on LR here but we can't, as we need to calculate
# numcompares; I therefore send None as the minimum LR
command = ["python3",progname,archivefile,"report","ALL",reportfile,"None",str(minloci)]
run_and_report(command,"Unable to pull report from fammatch database " + archivefile)

# read seizure_modifications file
rejected_seizures, merged_seizures = read_seizure_mods(modfile)

# read DM file; if we later find these entries in the database we will
# discard them.  We discard DMs for rejected seizures here, and correct
# names for modified ones
dms = {}
for line in open(dmfile,"r"):
  line = line.rstrip().split("\t")
  sz1 = line[2]
  sz2 = line[3]
  if sz1 in rejected_seizures or sz2 in rejected_seizures:  continue
  if sz1 in merged_seizures:
    sz1 = merged_seizures[sz1]
  if sz2 in merged_seizures:
    sz2 = merged_seizures[sz2]
  if sz1 == sz2:  # after merges this is a within-seizure match, discard
    continue
  spec = line[4]
  if spec == "F":  species = "forest"
  elif spec == "S":  species = "savannah"
  else:  continue  # don't want hybrids
  sid1 = line[0]
  sid2 = line[1]
  sids = tuple(sorted([sid1,sid2]))
  if species not in dms:
    dms[species] = {}
  dms[species][sids] = [sz1, sz2]

# filter database report based on seizure_modifications and DMs
# rules:  delete all lines mentioning a REJECT seizure
#         rename MERGE seizures
#         delete pre-identified DMs (even if they are not DMs here)
# we do not need to handle minloci as this is done by the fammatch_database.
# we do not filter out low LRs as we have to count them
datalines = {}
for line in open(reportfile,"r"):
  line = line.rstrip().split("\t")
  if line[0] == "secno":     # header
    s1_index = line.index("s1")
    s2_index = line.index("s2")
    sz1_index = line.index("sz1")
    sz2_index = line.index("sz2")
    sec_index = line.index("secno")
    dm_ind = line.index("DM_LR")
    loci_ind = line.index("nloci")
    continue
  sz1 = line[sz1_index]
  sz2 = line[sz2_index]
  # rejected seizure
  if sz1 in rejected_seizures or sz2 in rejected_seizures:  
    continue
  # merged seizure
  if sz1 in merged_seizures:
    sz1 = merged_seizures[sz1]
    line[sz1_index] = merged_seizures[sz1]
  if sz2 in merged_seizures:
    sz2 = merged_seizures[sz2]
    line[sz2_index] = merged_seizures[sz2]
  if sz1 == sz2:  # this is a within-seizure match now, discard
    continue
  s1 = line[s1_index]
  s2 = line[s2_index]
  key = tuple(sorted([s1,s2]))
  secno = int(line[sec_index])
  species = secdict[secno]
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
allpairs = set()

# score pairs and identify DMs
for species in splist:
  LRs[species] = []
  relpairs[species] = {}
  dmpairs[species] = {}
  ncompares[species] = {}
  for key in datalines[species]:
    line = datalines[species][key]
    # removed some mangled-elephant-name code here, hopefully no longer needed!
    # problem elephants were 64.230 and UWA.EBB.029
    sz1 = line[sz1_index]
    sz2 = line[sz2_index]
    myLRs = [float(x) for x in line[dm_ind:loci_ind]]
    top_LR = max(myLRs)
    LRs[species].append(top_LR)
    seizepair = [sz1,sz2]
    seizepair.sort()
    seizepair = tuple(seizepair)
    if seizepair not in ncompares[species]:
      ncompares[species][seizepair] = 0
    ncompares[species][seizepair] += 1
    if top_LR >= LR_cutoff:
      allseizures.add(sz1)
      allseizures.add(sz2)
      allpairs.add(seizepair)
      if myLRs[0] == top_LR:   # a DM not found in the DMs file
        if seizepair not in dmpairs[species]:
          dmpairs[species][seizepair] = []
        dmpairs[species][seizepair].append(top_LR)
      else:                  # not a DM
        if seizepair not in relpairs[species]:
          relpairs[species][seizepair] = []
        relpairs[species][seizepair].append(top_LR)
        
  # handle pre-identified DMs
  for match in dms[species]: 
    sz1, sz2 = dms[species][match]
    seizepair = tuple(sorted([sz1,sz2]))
    allpairs.add(seizepair)
    if seizepair not in dmpairs[species]:
      dmpairs[species][seizepair] = []
    dmpairs[species][seizepair].append(dm_LR)
    LRs[species].append(dm_LR)
    if seizepair not in ncompares[species]:
      ncompares[species][seizepair] = 0
    ncompares[species][seizepair] += 1
    allseizures.add(sz1)
    allseizures.add(sz2)

# place observations into bins
allseizures = list(allseizures)
observed = {}
weights = {}
outfile = open(outdir + "fammatch_weights_bins","w")
for species in splist:
  outfile.write(species+"\n")
  numbins = len(fpbins[species])
  observed[species] = [0.0 for x in fpbins[species]]
  weights[species] = [0.0 for x in fpbins[species]]
  for bestLL in LRs[species]:   # this includes DMs:  I think that's OK
    mybin = whichbin(bestLL, fpbins[species])
    if mybin is not None:
      observed[species][mybin] += 1
    # DEBUG
      #if species == "forest":
      #  print(math.log(bestLL,10.0))
  # obtain weights for each bin 
  numcompares = len(LRs[species])
  print(species)
  for binno, obs, rate in zip(range(0,numbins),observed[species],fprates[species]):
    expected = rate * numcompares
    print(binno,math.log(fpbins[species][binno],10),obs,expected)
    if obs <= expected:
      print("Observed greater than expected:  species",species,"binno",binno)
      print("bounds",fpbins[species][binno],fpbins[species][binno+1])
      print("obs",obs,"expected",expected)
      #assert False
    if obs > 0:
      wt = float(obs-expected)/obs
    else:
      print("second branch:  Observed greater than expected:  species",species,"binno",binno)
      print("bounds",fpbins[species][binno],fpbins[species][binno+1])
      print("obs",obs,"expected",expected)
      #assert False
    weights[species][binno] = wt
    outline = [math.log(fpbins[species][binno],10),obs,expected,weights[species][binno]]
    outline = [str(x) for x in outline]
    outline = "\t".join(outline) + "\n"
    outfile.write(outline)
outfile.close()

# calculate seizure-pair matches for all pairs that have any
similarity = {}
allpairs = list(allpairs)
allpairs.sort()
matchpairs = set()
for seizepair in allpairs:
  compval = 0.0
  for species in splist:
    if seizepair in relpairs[species]:
      for item in relpairs[species][seizepair]:
        mybin = whichbin(item,fpbins[species])
        if mybin is not None:
          compval += weights[species][mybin]
          matchpairs.add(seizepair)
    if seizepair in dmpairs[species]:
      for item in dmpairs[species][seizepair]:
        mybin = whichbin(item,fpbins[species])
        if mybin is not None:
          compval += dm_multiplier * weights[species][mybin]
          matchpairs.add(seizepair)
  similarity[seizepair] = compval

# write nodes and edges files for network analysis
# values are similarities, not distances

# node file
nodefile = open(outdir + "seizure_nodes.csv","w")
nline= "Seizure\n"
nodefile.write(nline)
for sz in allseizures:
  nline = sz + "\n"
  nodefile.write(nline)
nodefile.close()

# edge file
edgefile = open(outdir + "seizure_edges.csv","w")
eline = "Seizure1,Seizure2,Similarity\n"
edgefile.write(eline)
for sz1, sz2 in matchpairs:
  if sz1 == sz2:  
    continue
  eline = [sz1,sz2,str(similarity[(sz1,sz2)])]
  eline = ",".join(eline) + "\n"
  edgefile.write(eline)
edgefile.close()
