# take a set of EBhybrids results and the infile that produced
# them, and make 1 or 2 species specific files for SCAT.

import sys
import os

cutoff = 0.5

def make_fam_match_files(prefix,biome,datalines,refprefix):
  reffile = open(refprefix+"_"+biome+"_long.csv","w")
  sampfile = open(prefix+"_genotypes_"+biome+"_wide.csv","w")
  samplehdr = "Match ID,FH67,FH67,FH71,FH71,FH19,FH19,FH129,FH129,FH60,FH60,FH127,FH127,FH126,FH126,FH153,FH153,FH94,FH94,FH48,FH48,FH40,FH40,FH39,FH39,FH103,FH103,FH102,FH102,S03,S03,S04,S04\n"
  sampfile.write(samplehdr)
  refhdr = "FH67,FH71,FH19,FH129,FH60,FH127,FH126,FH153,FH94,FH48,FH40,FH39,FH103,FH102,S03,S04\n"
  reffile.write(refhdr)
  idseen = {}
  for line in datalines:
    nline = line.split()
    id = nline[0]
    region = nline[1]
    msats = nline[2:]

    # if the region is "unknown" then the line goes into the sample file
    if region == "-1":
      if id not in idseen:
        idseen[id] = msats
        continue
      sampline = id
      for msat1,msat2 in zip(msats,idseen[id]):
        sampline += "," + msat1 + "," + msat2
      sampline += "\n"
      sampfile.write(sampline)
    #else the line goes into the reference file
    else:
      refline = ",".join(msats)
      refline += "\n"
      reffile.write(refline)

  reffile.close()
  sampfile.close()

#-----------------------------------------------
  
print("NOTE:  this program assumes that Species 1 is savannah")
print("and is using a hybrid cutoff of >", cutoff)

if len(sys.argv) != 5:
  print("USAGE:  make_species_files.py prefix mapprefix regionfile refprefix")
  print("  datafile should contain both unknown and all known refs")
  print("  and must be the file the EBhybrid results came from!")
  print("  refprefix is which reference file the ref data came from")
  print("  frex. REFELE_21 for data that came from REFELE_21_known.txt")
  exit()

prefix = sys.argv[1]
datafile = os.path.abspath(prefix+"_plus_ref.txt")
ebfile = prefix+"_hybt.txt"
mapprefix = sys.argv[2]
savannahmap = os.path.abspath(mapprefix+"_savannah.txt")
forestmap = os.path.abspath(mapprefix+"_forest.txt")
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
  runlines = open("master_scat_runfile.sh","r").readlines()
  assert len(runlines) == 1
  runline = runlines[0]
  runline = runline.replace("NUMIND",str(numunknown))
  # we do NOT replace SEED; that will be done downstream, as each
  # separate Scat run needs its own seed.
  runline = runline.replace("MAPFILE",savannahmap)
  runline = runline.replace("DATAFILE","../"+outfilename)
  runline = runline.replace("REGIONFILE",regionfile)
  runfile = open("runfile_savannah.sh","w")
  runfile.write(runline)
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
  # make elephant familial matching ref and samples files
  make_fam_match_files(prefix,"savannah",savannahlines,sys.argv[4])

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
  runlines = open("master_scat_runfile.sh","r").readlines()
  assert len(runlines) == 1
  runline = runlines[0]
  runline = runline.replace("NUMIND",str(numunknown))
  # we do NOT replace SEED; that will be done downstream, as each
  # separate Scat run needs its own seed.
  runline = runline.replace("MAPFILE",forestmap)
  runline = runline.replace("DATAFILE","../"+outfilename)
  runline = runline.replace("REGIONFILE",regionfile)
  runfile = open("runfile_forest.sh","w")
  runfile.write(runline)
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
  # make elephant familial matching ref and samples files
  make_fam_match_files(prefix,"forest",forestlines,sys.argv[4])
