# Transform a SCAT input file where only one allele at a locus might be
# missing while the other was not, into a SCAT input file where if one is
# missing, the other is as well.  Also, put in -1 for region, and do
# a little error checking

# input:  SCAT style data from the spreadsheets
# output:  SCAT input that will actually work in EBhybrids and SCAT2

# functions

def correct_missing(msats):
  for i in range(0,len(msats)):
    if not msats[i].isnumeric():
      msats1[i] = "-999"

import sys
if len(sys.argv) != 2:
  print("USAGE:  prep_scat_data.py PREFIX")
  print("This will read PREFIX_raw.tsv and write PREFIX_unknowns.txt")
  exit(-1)

prefix = sys.argv[1]
infilename = prefix+"_raw.tsv"
outfilename = prefix+"_unknowns.txt"
outfile = open(outfilename,"w")

headerline = True
firstline = True
for line in open(infilename,"r"):
  line = line.rstrip().split("\t")
  if headerline:
    headerline = False
    continue
  if len(line) != 17:
    print("Expected 17 entries per line but found",len(line))
    exit(-1)
  if firstline:
    name1 = line[0]
    msats1 = line[1:]
    correct_missing(msats1)
    firstline = False
  else:
    name2 = line[0]
    msats2 = line[1:]
    correct_missing(msats2)
    firstline = True
    
    # make the output line
    if name1 != name2: 
      print("Names",name1,"and",name2,"for same individual")
      exit(-1)
    outline1 = name1 + " -1"
    outline2 = name2 + " -1"
    bad_msats = 0
    for m1, m2 in zip(msats1,msats2):
      if m1 == "-999" or m2 == "-999":
        bad_msats += 1
        outline1 += " -999"
        outline2 += " -999"
      else:
        outline1 += " " + m1
        outline2 += " " + m2
    outline1 += "\n"
    outline2 += "\n"
    if bad_msats < 7:  # we require 10/16 msats to be good
      outfile.write(outline1)
      outfile.write(outline2)

outfile.close()

