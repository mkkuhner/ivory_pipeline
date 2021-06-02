# take the results of a scat2 -H2 run, on joint savannah and forest (but
# not hybrid) data, and the scat file from which these were made.
# create all needed files for a fammatch run for each subregion.
# this includes a reference file and new_ sample files.  We assume that
# old_ sample files have been provided; this version of the program
# is meant for incrementally running new seizure(s) against previously
# archived old seizures.  Don't forget to add your new results to the
# archive!

# ivory samples are assigned to subregion by scat.  Reference samples
# are assigned to subregion based on their park--NOT by scat.

# No files are written for subregions with no seizure samples assigned.

# BE SURE TO SET "nsub" APPROPRIATELY (number of subregions)!

nsub = 6

import sys

if len(sys.argv) != 4:
  print("USAGE:  make_fammatch_incremental Output_hybrid scatinput.txt regionfile.txt")
  exit(-1)

hybfile = sys.argv[1]
genofile = sys.argv[2]
regionfile = sys.argv[3]

# read subregion assignments from scat
id_subreg = {}
for line in open(hybfile,"r"):
  line = line.rstrip().split()
  if line[0] == "Hybridcheck": 
    assert line[1] == "=2"
    continue
  if line[0] == "Individual":
    continue
  id = line[0]
  probs = [float(x) for x in line[1:nsub+1]]
  bestprob = max(probs)
  subreg = probs.index(bestprob)
  id_subreg[id] = subreg

# read subregion assignments from regionfile
reg_subreg = {}
for line in open(regionfile,"r"):
  line = line.rstrip().split()
  reg = line[1]
  subreg = line[2]
  reg_subreg[reg] = subreg

seizure = [[] for x in range(0,nsub)]
reference = [[] for x in range(0,nsub)]

# read and classify genotypes
for line in open(genofile,"r"):
  line = line.rstrip().split()
  id = line[0]
  reg = line[1]
  if reg == "-1":      # ivory sample
    subreg = id_subreg[id]
    subreg = int(subreg)
    seizure[subreg].append(line)
  else:                # reference sample
    subreg = reg_subreg[reg]
    subreg = int(subreg)
    reference[subreg].append(line)

# write reference files
# "long" format -- 2 lines per sample, no ID, with headers

header = "FH67,FH71,FH19,FH129,FH60,FH127,FH126,FH153,FH94,FH48,FH40,FH39,FH103,FH102,S03,S04\n"

for subreg in range(0,nsub):
  if len(seizure[subreg]) == 0:  continue  # nothing to be done for this one
  outfile = open("ref"+str(subreg)+"_fammatch.csv","w")
  outfile.write(header)
  for line in reference[subreg]:
    data = line[2:]
    outline = ",".join(data) + "\n"
    outfile.write(outline)
  outfile.close()

# write ivory files
# "wide" format -- 1 line per sample, doubled header with Match ID

header = "Match ID,FH67,FH67,FH71,FH71,FH19,FH19,FH129,FH129,FH60,FH60,FH127,FH127,FH126,FH126,FH153,FH153,FH94,FH94,FH48,FH48,FH40,FH40,FH39,FH39,FH103,FH103,FH102,FH102,S03,S03,S04,S04\n"

for subreg in range(0,nsub):
  if len(seizure[subreg]) == 0:  continue  # nothing to be done for this one
  outfile_new = open("new"+str(subreg)+".txt","w")
  outfile_new.write(header)
  for line1, line2 in zip(seizure[subreg][0::2],seizure[subreg][1::2]):
    data1 = line1[2:]
    data2 = line2[2:]
    id = line1[0]
    if not line2[0] == id:
      print (line1[0],line2[0])
      exit()
    outline = id 
    for d1,d2 in zip(data1,data2):
      outline += "," + d1
      outline += "," + d2
    outline += "\n"
    outfile_new.write(outline)
  outfile_new.close()

