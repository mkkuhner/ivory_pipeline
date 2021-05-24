# take a set of EBhybrids results and the infile that produced
# them, and make 1 or 2 species specific files for SCAT, as well as
# a conjoint hybrid-free file for familial matching.

# program formerly known as make_species_files.py

### functions

def make_species_scatfile(species,prefix,unknowns,specieslines):
  outfilename = prefix + "_" + species + ".txt"
  print("Writing", species, "SCAT input file",outfilename)
  print("Contains:")
  numunknown = unknowns/2
  numref = (len(specieslines) - unknown_savannah)/2
  print("\t",numunknown,"location unknown")
  print("\t",numref,"reference")
  outfile = open(outfilename,"w")
  for line in specieslines:
    outfile.write(line)
  outfile.close()

def make_runfiles(clusterrun,species,prefix,numunknown,mapfile,regionfile):
  # make Scat run file
  if clusterrun:
    runlines = open("cluster_master_scat.sh","r").readlines()
    runline = runlines[-1]
  else:
    runlines = open("master_scat_runfile.sh","r").readlines()
    assert len(runlines) == 1
    runline = runlines[0]
  runline = runline.replace("NUMIND",str(numunknown))
  # we do NOT replace SEED; that will be done downstream, as each
  # separate Scat run needs its own seed.
  runline = runline.replace("MAPFILE",mapfile)
  outfilename = prefix + "_" + species + ".txt"
  runline = runline.replace("DATAFILE","../"+outfilename)
  runline = runline.replace("REGIONFILE",regionfile)
  runfile = open("runfile_" + species + ".sh","w")
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
savannahlines = []
forestlines = []
unknownlines = []
knownlines = []
unknown_savannah = 0
unknown_forest = 0
for line in open(datafile,"r"):
  nline = line.rstrip().split()
  id = nline[0]
  region = nline[1]
  msats = nline[2:]
  if speciesdict[id] == "H":
    continue    # discarding hybrids
  if speciesdict[id] == "S":
    savannahlines.append(line)
    if region == "-1":   # found a region-unknown savannah individual
      unknown_savannah += 1
      unknownlines.append(line)
    else:
      knownlines.append(line)
  else:
    forestlines.append(line)
    if region == "-1":   # found a region-unknown forest individual
      unknown_forest += 1
      unknownlines.append(line)
    else:
      knownlines.append(line)

# write conjoint file for familial matching
outfile = open(prefix + "_conjoint_nohybrids.txt","w")
unknowns = []
knowns = []
for line in unknownlines:
  outfile.write(line)
for line in knownlines:
  outfile.write(line)
outfile.close()

# write species-specific files for SCAT/VORONOI pipeline

if unknown_savannah > 0:
  make_species_scatfile("savannah",prefix,unknown_savannah,savannahlines)
  make_runfiles(clusterrun,"savannah",prefix,unknown_savannah,savannahmap,regionfile)

if unknown_forest > 0:
  make_species_scatfile("forest",prefix,unknown_forest,forestlines)
  make_runfiles(clusterrun,"forest",prefix,unknown_forest,forestmap,regionfile)
