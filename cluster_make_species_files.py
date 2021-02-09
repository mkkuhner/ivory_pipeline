# take a set of EBhybrids results and the infile that produced
# them, and make 1 or 2 species specific files for SCAT.

import sys
import os

cutoff = 0.5

print("NOTE:  this program assumes that Species 1 is savannah")
print("and is using a hybrid cutoff of >", cutoff)

if len(sys.argv) != 4:
  print("USAGE:  make_species_files.py prefix maptype regionfile")
  print("  datafile should contain both unknown and all known refs")
  print("  and must be the file the EBhybrid results came from!")
  print("  maptype must be either new or iucn")
  exit()

prefix = sys.argv[1]
datafile = os.path.abspath(prefix+"_plus_ref.txt")
ebfile = prefix+"_hybt.txt"
maptype = sys.argv[2]
if maptype == "new":
  savannahmap = os.path.abspath("mapfile_new_savannah.txt")
  forestmap = os.path.abspath("mapfile_new_forest.txt")
elif maptype == "iucn":
  savannahmap = os.path.abspath("iucn_savannah.txt")
  forestmap = os.path.abspath("iucn_forest.txt")
else:
  print("Unknown map type",maptype)
  exit(-1)
regionfile = os.path.abspath(sys.argv[3])

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

# read scat
savannahlines = []
forestlines = []
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
    if region == "-1":   # found a region-unknown savannah individual
      unknown_savannah += 1
    savannahlines.append(line)
  else:
    if region == "-1":   # found a region-unknown forest individual
      unknown_forest += 1
    forestlines.append(line)

if unknown_savannah > 0:
  outfilename = prefix + "_savannah.txt"
  print("Writing savannah SCAT input file",outfilename)
  print("Contains:")
  numunknown = unknown_savannah/2
  numref = (len(savannahlines) - unknown_savannah)/2
  print("\t",numunknown,"location unknown")
  print("\t",numref,"reference")
  outfile = open(outfilename,"w")
  for line in savannahlines:
    outfile.write(line)
  outfile.close()
  # make Scat run file
  runlines = open("cluster_master_scat.sh","r").readlines()
  runline = runlines[-1]
  runline = runline.replace("NUMIND",str(numunknown))
  # we do NOT replace SEED; that will be done downstream, as each
  # separate Scat run needs its own seed.
  runline = runline.replace("MAPFILE",savannahmap)
  runline = runline.replace("DATAFILE","../"+outfilename)
  runline = runline.replace("REGIONFILE",regionfile)
  runlines[-1] = runline
  runfile = open("runfile_savannah.sh","w")
  runfile.writelines(runlines)
  runfile.close()

  # make Voronoi run file
  runlines = open("master_voronoi_runfile.sh","r").readlines()
  assert len(runlines) == 1
  runline = runlines[0]
  runline = runline.replace("MAPFILE",savannahmap)
  runline = runline.replace("PREFIX",prefix)
  runfile = open("voronoi_runfile_savannah.sh","w")
  runfile.write(runline)
  runfile.close()
  

if unknown_forest > 0:
  outfilename = prefix + "_forest.txt"
  print("Writing forest SCAT input file",outfilename)
  print("Contains:")
  numunknown = unknown_forest/2
  numref = (len(forestlines) - unknown_forest)/2
  print("\t",numunknown,"location unknown")
  print("\t",numref,"reference")
  outfile = open(outfilename,"w")
  for line in forestlines:
    outfile.write(line)
  outfile.close()
  # make master run file
  runlines = open("cluster_master_scat.sh","r").readlines()
  runline = runlines[-1]
  runline = runline.replace("NUMIND",str(numunknown))
  # we do NOT replace SEED; that will be done downstream, as each
  # separate Scat run needs its own seed.
  runline = runline.replace("MAPFILE",forestmap)
  runline = runline.replace("DATAFILE","../"+outfilename)
  runline = runline.replace("REGIONFILE",regionfile)
  runlines[-1] = runline
  runfile = open("runfile_forest.sh","w")
  runfile.writelines(runlines)
  runfile.close()
  # make Voronoi run file
  runlines = open("master_voronoi_runfile.sh","r").readlines()
  assert len(runlines) == 1
  runline = runlines[0]
  runline = runline.replace("MAPFILE",forestmap)
  runline = runline.replace("PREFIX",prefix)
  runfile = open("voronoi_runfile_forest.sh","w")
  runfile.write(runline)
  runfile.close()
