# take a set of EBhybrids results and the infile that produced
# them, and make 1 or 2 species specific files for SCAT, as well as
# a conjoint hybrid-free file for familial matching.

# also creates run files (cluster or laptop style) for SCAT.

# program formerly known as make_species_files.py

### functions

def make_species_scatfile(species, prefix, seizelines, reflines):
  outfilename = prefix + "_" + species + ".txt"
  print("Writing", species, "SCAT input file",outfilename)
  print("Contains:")
  numseize = len(seizelines) / 2
  numref = len(reflines) / 2
  print("\t",numseize,"location unknown")
  print("\t",numref,"reference")
  outfile = open(outfilename,"w")
  for line in seizelines:
    outfile.write(line)
  for line in reflines:
    outfile.write(line)
  outfile.close()

def truncate_path(mypath,prefix):
  mypath = mypath.split("/")
  mypath = prefix + "/" + mypath[-1]
  return mypath

def make_runfiles(clusterrun,species,prefix,seizelines,mapfile,regionfile):
  # make Scat run file
  datafile = prefix + "_" + species + ".txt"
  if clusterrun:
    cluster_path = "/gscratch/wasser/mkkuhner/seizureruns/" 
    runlines = open("../cluster_master_scat.sh","r").readlines()
    runline = runlines[-1]
    mapfile = cluster_path + truncate_path(mapfile,prefix)
    regionfile = cluster_path + truncate_path(regionfile,prefix)
    datafile = cluster_path + truncate_path(datafile,prefix)
  else:
    runlines = open("master_scat_runfile.sh","r").readlines()
    assert len(runlines) == 1
    runline = runlines[0]
  numind = len(seizelines) / 2
  runline = runline.replace("NUMIND",str(numind))
  # we do NOT replace SEED; that will be done downstream, as each
  # separate Scat run needs its own seed.
  runline = runline.replace("MAPFILE",mapfile)
  runline = runline.replace("DATAFILE",datafile)
  runline = runline.replace("REGIONFILE",regionfile)
  runfile = open("runfile_" + species + ".sh","w")
  if clusterrun:
    runfile.writelines(runlines[0:-1])
  runfile.write(runline)
  runfile.close()
  # make Voronoi run file
  runlines = open("master_voronoi_runfile.sh","r").readlines()
  assert len(runlines) == 1
  runline = runlines[0]
  runline = runline.replace("MAPFILE",mapfile)
  runline = runline.replace("PREFIX",prefix)
  runfile = open("voronoi_runfile_" + species + ".sh","w")
  runfile.write(runline)
  runfile.close()


###############################################################################
### main

import sys
import os

cutoff = 0.5
  
print("NOTE:  this program assumes that Species 1 is savannah")
print("and is using a hybrid cutoff of >", cutoff)

if len(sys.argv) != 6:
  print("USAGE:  filter_hybrids.py prefix mapprefix regionfile refprefix clusterrun")
  print("  datafile should contain both unknown and all known refs")
  print("  and must be the file the EBhybrid results came from!")
  print("  refprefix is which reference file the ref data came from")
  print("  frex. REFELE_21 for data that came from REFELE_21_known.txt")
  print("  if clusterrun == T then this will be assumed to be a run on the biology")
  print("     computing cluster, otherwise not")
  exit()

prefix = sys.argv[1]
datafile = os.path.abspath(prefix+"_plus_ref.txt")
ebfile = prefix+"_hybt.txt"
mapprefix = sys.argv[2]
savannahmap = os.path.abspath(mapprefix+"_savannah.txt")
forestmap = os.path.abspath(mapprefix+"_forest.txt")
regionfile = os.path.abspath(sys.argv[3])

clusterrun = False
if sys.argv[5] == "T":
  clusterrun = True

savcount = 0
forcount = 0
hybcount = 0

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

# read scat-style input containing both seizure and ref
sav_seizure = []
sav_ref = []
for_seizure = []
for_ref = []
for line in open(datafile,"r"):
  nline = line.rstrip().split()
  id = nline[0]
  region = nline[1]
  msats = nline[2:]
  # hybrids
  if speciesdict[id] == "H":
    continue    # discarding hybrids
  # savannah
  if speciesdict[id] == "S":
    if region == "-1":
      sav_seizure.append(line)
    else:
      sav_ref.append(line)
  # forest
  else:
    assert speciesdict[id] == "F"
    if region == "-1":
      for_seizure.append(line)
    else:
      for_ref.append(line)

# write conjoint file for familial matching
outfile = open(prefix + "_conjoint_nohybrids.txt","w")
unknowns = []
knowns = []
for line in sav_seizure:
  outfile.write(line)
for line in for_seizure:
  outfile.write(line)
for line in sav_ref:
  outfile.write(line)
for line in for_ref:
  outfile.write(line)
outfile.close()

# write species-specific files for SCAT/VORONOI pipeline

if len(sav_seizure) > 0:
  make_species_scatfile("savannah",prefix,sav_seizure,sav_ref)
  make_runfiles(clusterrun,"savannah",prefix,sav_seizure,savannahmap,regionfile)

if len(for_seizure) > 0:
  make_species_scatfile("forest",prefix,for_seizure,for_ref)
  make_runfiles(clusterrun,"forest",prefix,for_seizure,forestmap,regionfile)
