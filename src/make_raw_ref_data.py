# NOTE:  python3 program!

# this program reads the master ref database and writes a SCAT style file
# to be used in Structure.  It should be given the ref data as a .csv
# made from the Ref Stats tab (not the Reference All tab!).  Note that
# this program correctly uses Match ID and not Sample ID.

import sys
import csv

if len(sys.argv) != 3:
  print("USAGE:  python3 make_raw_ref_data.py reffile.csv outfile")
  exit(-1)

reffile = sys.argv[1]
outfilename = sys.argv[2]

# read the ref master file 
rdat = {}
with open(reffile,newline="") as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    if line[0].startswith("Match"):  
      header = line
      regionindex = header.index("Input Zone")
      matchindex = header.index("Match ID")
      firstmsat = header.index("FH67")
      lastmsat = firstmsat+32
      continue
    sid = line[matchindex]
    region = line[regionindex]
    if region == "NA":  continue   # can't use this region-unknown individual
    assert len(line[firstmsat:lastmsat]) == 32
    rdat[sid] = [region,line[firstmsat:lastmsat]]

outfile = open(outfilename,"w")
# no header:  for Structure we will slap one on, and the other programs don't want it
sortsids = sorted(list(rdat.keys()))
for sid in sortsids:
  region = rdat[sid][0]
  outline1 = sid + "\t" + region
  outline2 = sid + "\t" + region
  msats = rdat[sid][1]
  for m1,m2 in zip(msats[0::2],msats[1::2]):
    bad = False
    if m1 == "" or m2 == "":  bad = True
    if m1 == "NA" or m2 == "NA":  bad = True
    if m1 == "-999" or m2 == "-999":  bad = True
    if bad:
      m1 = "-999"
      m2 = "-999"
    outline1 += "\t" + m1
    outline2 += "\t" + m2
  outline1 += "\n"
  outline2 += "\n"
  outfile.write(outline1)
  outfile.write(outline2)

outfile.close()

