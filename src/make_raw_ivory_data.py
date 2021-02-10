# NOTE:  python3 program!

# This program reads the master elephant database (ivory stats tab) and
# writes a single SCAT-style file.  It does not retain seizure information,
# so that may need to be added back in later.

import sys
import csv

if len(sys.argv) != 3:
  print("USAGE:  python3 make_raw_ivory_data.py ivoryfile.csv outfile")
  exit(-1)

ivoryfile = sys.argv[1]
outfilename = sys.argv[2]

# read the ivory master file 
rdat = {}
with open(ivoryfile,newline="") as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    if line[0].startswith("Seizure"):  
      header = line
      matchindex = header.index("Match ID")
      firstmsat = header.index("FH67")
      lastmsat = firstmsat+32
      continue
    sid = line[matchindex]
    if sid == "":  continue  # I don't know what these are but they're useless
    msatdata = line[firstmsat:lastmsat]
    assert len(msatdata) == 32
    badcount = 0
    for i in range(0,32,2):
      badmsat = 0
      for j in [i,i+1]:
        if msatdata[j] == "" or msatdata[j] == "NA" or msatdata[j].isspace():
          badmsat += 1
          msatdata[j] = ""
      if badmsat == 2:
        badcount += 1
    if badcount > 6:
      continue     # not enough valid msats     
    rdat[sid] = msatdata

outfile = open(outfilename,"w")
outline = "Sample\t"
msatnames = header[firstmsat:lastmsat:2] 
outline += "\t".join(msatnames)
outline += "\n"
outfile.write(outline)
sortsids = sorted(list(rdat.keys()))
for sid in sortsids:
  region = rdat[sid][0]
  outline1 = sid 
  outline2 = sid 
  odd = True
  for m in rdat[sid]:
    if m == "":  m = "-999"
    if m == "NA":  m = "-999"
    if odd:
      outline1 += "\t" + m
    else:
      outline2 += "\t" + m
    odd = not odd
  outline1 += "\n"
  outline2 += "\n"
  outfile.write(outline1)
  outfile.write(outline2)

outfile.close()
