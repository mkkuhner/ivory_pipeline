# take a set of EBhybrids results and the infile that produced
# them, and make 1 or 2 species specific files for SCAT

# also creates run files (cluster or laptop style) for SCAT.

# program formerly known as make_species_files.py

### functions

def readivorypath(ifile):
  ivorypaths = {}
  inlines = open(ifile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def is_even(number):
  if number % 2 != 0:
    return False
  return True

def make_species_scatfile(species, prefix, seizelines, reflines):
  outfilename = prefix + "_" + species + ".txt"
  print("Writing", species, "SCAT input file",outfilename)
  print("Contains:")
  assert is_even(len(seizelines))
  assert is_even(len(reflines))
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
    datafile = "../../" + datafile
  assert is_even(len(seizelines))
  runline = runline.replace("SCAT",scat_execpath)
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


###############################################################################
### main

import sys
import os

cutoff = 0.5
  
print("NOTE:  this program assumes that Species 1 is savannah")
print("and is using a hybrid cutoff of >", cutoff)

if len(sys.argv) != 5:
  print("USAGE:  filter_hybrids.py prefix ivory_paths.tsv clusterrun use_canned_reference")
  print("What we got:")
  for item in sys.argv:  print(item)
  print("  This program uses PREFIX_plus_ref.txt and the corresponding EBhybrids output,")
  print("    and THOSE MUST MATCH.")
  print("  if clusterrun == T then this will be assumed to be a run on the biology")
  print("     computing cluster, otherwise not")
  print("  if use_canned_reference == T then precomputed references will be used")
  print("     rather than the ones from EBhybrid")
  exit(-1)

prefix = sys.argv[1]
ifile = sys.argv[2]
datafile = os.path.abspath(prefix+"_plus_ref.txt")
ebfile = prefix+"_hybt.txt"

pathdir = readivorypath(ifile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_dir, scat_exec = pathdir["scat_executable"]
scat_execpath = scat_dir + scat_exec
reference_path, reference_prefix = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
zones_savannah = zones_path + zones_prefix + "_savannah.txt"
zones_forest = zones_path + zones_prefix + "_forest.txt"

map_path, map_prefix = pathdir["map_prefix"]
savannahmap = map_path + map_prefix+"_savannah.txt"
forestmap = map_path + map_prefix+"_forest.txt"

seizure_data_dir = pathdir["seizure_data_dir"][0]
voronoi_exec = pathdir["voronoi_executable"][0]

clusterrun = False
if sys.argv[3] == "T":
  clusterrun = True
use_canned_reference = False
if sys.argv[4] == "T":
  use_canned_reference = True

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

# read "canned" reference (we do not use the self-generated one as it varies stochastically
# and we need all runs to use the same exact reference).
if use_canned_reference:
  if len(sav_seizure) > 0:
    # pull savannah reference
    sav_ref = open(reference_path + reference_prefix + "_filtered_savannah.txt","r").readlines()
  if len(for_seizure) > 0:
    # pull forest reference
    for_ref = open(reference_path + reference_prefix + "_filtered_forest.txt","r").readlines()

# write species-specific files for SCAT/VORONOI pipeline

if len(sav_seizure) > 0:
  make_species_scatfile("savannah",prefix,sav_seizure,sav_ref)
  make_runfiles(clusterrun,"savannah",prefix,sav_seizure,savannahmap,zones_savannah)

if len(for_seizure) > 0:
  make_species_scatfile("forest",prefix,for_seizure,for_ref)
  make_runfiles(clusterrun,"forest",prefix,for_seizure,forestmap,zones_forest)
