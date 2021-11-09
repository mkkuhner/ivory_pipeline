# For each species present in a seizure:
# Take the results of a scat2 -H2 run and the corresponding scat file 
# create:
#  list of new elephants by match id and sector
#  fammatch reference files for needed sectors
#  "new" fammatch input files (will be edited downstream)
#  does NOT create old fammatch input files

# ivory samples are assigned to sector by scat.  Reference samples
# are assigned to sector based on their park and species--NOT by scat.

# run from parent directory of all seizures
# writes to PREFIX/fammatch directory, creating if needed

import sys
import os

if len(sys.argv) != 4:
  print("USAGE:  prep_fammatch.py PREFIX zonefileprefix dirwithzonefiles")
  exit(-1)

nsec = 6
prefix = sys.argv[1]
zoneprefix = sys.argv[2]
dirwithzonefiles = sys.argv[3]
if not dirwithzonefiles.endswith("/"):
  dirwithzonefiles += "/"
famdir = prefix + "/fammatch/"

# determine which species are wanted
specieslist = []
if os.path.isdir(prefix + "/nsavannah"):
  specieslist.append("savannah")
if os.path.isdir(prefix + "/nforest"):
  specieslist.append("forest")

# data structures for all sectors (both species)
seizure = [[] for x in range(0,nsec)]
reference = [[] for x in range(0,nsec)]
names = [[] for x in range(0,nsec)]

for species in specieslist:
  # identify wanted sectors based on species
  if species == "forest":
    sectors_wanted = [0,1]
  else:
    sectors_wanted = [2,3,4,5]
    # how far over do they start?
    displacement = 2

  # set up input files based on species
  zonefile = dirwithzonefiles + zoneprefix + "_" + species + ".txt"
  hybfile = prefix + "/fammatch/outdir_" + species + "/Output_hybrid"
  genofile = prefix + "/" + prefix + "_" + species + ".txt"

  # read sector assignments from scat
  id_sector = {}
  for line in open(hybfile,"r"):
    line = line.rstrip().split()
    if line[0] == "Hybridcheck": 
      assert line[1] == "=2"
      continue
    if line[0] == "Individual":
      continue
    id = line[0]
    probs = [float(x) for x in line[1:nsec+1]]
    bestprob = max(probs[sectors_wanted[0]:sectors_wanted[1]+1])
    sector = probs.index(bestprob) + displacement
    if sector not in sectors_wanted:
      print("found unexpected sector",sector)
      print("not in sectors_wanted:",sectors_wanted)
      print(id,probs)
      exit(-1)
    id_sector[id] = sector
  
  # read sector assignments from zonefile
  reg_sector = {}
  for line in open(zonefile,"r"):
    line = line.rstrip().split()
    reg = line[1]
    sector = int(line[2])
    if sector not in sectors_wanted:
      print("found unexpected ref sector",sector)
      print("not in sectors_wanted:",sectors_wanted)
      exit(-1)
    assert sector in sectors_wanted
    reg_sector[reg] = sector
  
  # read and classify genotypes
  for line in open(genofile,"r"):
    line = line.rstrip().split()
    id = line[0]
    reg = line[1]
    if reg == "-1":      # ivory sample
      sector = id_sector[id]
      sector = int(sector)
      seizure[sector].append(line)
      names[sector].append(id)
    else:                # reference sample
      sector = reg_sector[reg]
      sector = int(sector)
      reference[sector].append(line)

# write reference files
# "long" format -- 2 lines per sample, no ID, with headers
  
header = "FH67,FH71,FH19,FH129,FH60,FH127,FH126,FH153,FH94,FH48,FH40,FH39,FH103,FH102,S03,S04\n"
  
for sector in range(0,nsec):
  if len(seizure[sector]) == 0:  continue
  outfile = open(famdir + "ref_"+str(sector)+"_fammatch.csv","w")
  outfile.write(header)
  for line in reference[sector]:
    data = line[2:]
    outline = ",".join(data) + "\n"
    outfile.write(outline)
  outfile.close()
  
# deduce official seizure name (with commas instead of underscores)
seizurename = prefix.split("_")
seizurename = ", ".join(seizurename)

# write elephant lists
for sector in range(0,nsec):
  if len(names[sector]) == 0:  continue
  outfile = open(famdir + "names_"+str(sector)+".tsv","w")
  for id in names[sector][0::2]:   
    outline = id + "\t" + seizurename + "\n"
    outfile.write(outline)
  outfile.close()
  
# write ivory files
# "wide" format -- 1 line per sample, doubled header with Match ID

header = "Match ID,FH67,FH67,FH71,FH71,FH19,FH19,FH129,FH129,FH60,FH60,FH127,FH127,FH126,FH126,FH153,FH153,FH94,FH94,FH48,FH48,FH40,FH40,FH39,FH39,FH103,FH103,FH102,FH102,S03,S03,S04,S04\n"

for sector in range(0,nsec):
  if len(seizure[sector]) == 0:  continue
  outfile_new = open(famdir + "prep"+str(sector)+".csv","w")
  outfile_new.write(header)
  for line1, line2 in zip(seizure[sector][0::2],seizure[sector][1::2]):
    data1 = line1[2:]
    data2 = line2[2:]
    id = line1[0]
    if not line2[0] == id:
      print ("Mismatched ids:",line1[0],line2[0])
      exit(-1)
    outline = id 
    for d1,d2 in zip(data1,data2):
      outline += "," + d1
      outline += "," + d2
    outline += "\n"
    outfile_new.write(outline)
  outfile_new.close()
