# Takes an all-seizures genotype file and a this-seizure genotype file and
# creates the all-but-this-one file needed for familial matching.  Assumes the
# current seizures IS in the all-seizures file and will error out if not.  All
# files are species specific.

# Q:  Why does this program insist that the current seizure is in all-seizures,
# and then take it out?
# A:  To make sure that this seizure gets into all-seizures, where it will
# need to be before we run the next one!
# Q:  How am I supposed to get it into all-seizures?
# A:  There is a dedicated maintainer; ask them!  (Currently Mary.)

import sys
import csv

if len(sys.argv) != 4:
  print("USAGE:  python partition_genotypes.py species this_seizure.csv all_seizures.csv")
  exit(-1)

species = sys.argv[1]

if not (species == "forest" or species == "savannah"):
  print("Unknown species",species,"--legal options are forest and savannah")
  exit(-1)

myseizure = sys.argv[2]
if not myseizure.endswith(".csv"):
  print("Expected current seizure file to be a .csv")
  exit(-1)

allseizures = sys.argv[3]
if not allseizures.endswith(".csv"):
  print("Expected all seizure file to be a .csv")
  exit(-1)

outfilename = "other_genotypes_" + species + "_wide.csv"

# algorithm:  Remove everything in this_seizure.csv from all_seizures.csv to make
# output file.  Complain if match ids in this_seizure are not in all_seizures.

mydat = []
with open(myseizure,newline="") as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    mydat.append(line[0])

outputstuff = []
foundmatches = []

with open(allseizures,newline="") as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    oldID = line[0]
    if oldID not in mydat:
      outputstuff.append(line)
    else:
      foundmatches.append(oldID)

if len(foundmatches) == 0:
  print("Did not find current seizure in all seizures file!")
  print("Please update the all seizures file.")
  print("No files written.")
  exit(-1)

foundmatches.sort()
mydat.sort()
if foundmatches != mydat:
  print("Not all Match IDs in new data were present in all seizures file.")
  print("Please update the all seizures file.")
  print("No files written.")
  exit(-1)

outfile = open(outfilename,"w")
for line in outputstuff:
  outfile.write(line)
outfile.close()
