# verifymsat.py checks for previously unknown alleles of a given msat locus since they
# may be indicative of a column swap error in the seizure data

import sys

if len(sys.argv) != 4:
  print("USAGE: verifymsat.py nmarkers REFELE_[dbno]_raw.csv [seizure_name]_raw.tsv")
  exit()

nmarkers = int(sys.argv[1])

import csv
# we can't use DictReader because the column headers are not unique

pos2name = {}
refalleles = {}
readhdr = True
with open(sys.argv[2], newline="") as csvfile:
  reader = csv.reader(csvfile, delimiter=",")
  for row in reader:

    if readhdr:
      if row[0] != "Match ID":
        print("ERROR. Expected a header starting with 'Match ID', found:",row[0],"in",sys.argv[2])
        exit()
      # figure out where the msats are; the number of columns cannot be relied
      # on between database releases
      firstmarker = row.index("FH67")
      lastmarker = row.index("S04") + 1
      for pos in range(firstmarker,lastmarker+1,2):
        if row[pos] != row[pos+1]:
          print("ERROR. marker",row[pos],"does not match",row[pos+1],"in",sys.argv[2] )
          exit(-1)
        pos2name[pos] = row[pos]
        pos2name[pos+1] = row[pos]
        refalleles[row[pos]] = ["-999",]
      readhdr = False
      continue

    for pos in range(firstmarker,lastmarker+1):
      refalleles[pos2name[pos]].append(row[pos])

# now read in the seizure data 
abberant = {}
seizlines = open(sys.argv[3],"r").readlines()

pline = seizlines[0].rstrip().split("\t")
if pline[0] != "MatchID":
  print("ERROR. Expected a header starting with 'MatchID', found:",pline[0],"in",sys.argv[3])
  exit(-1)

spos2name = {}
for spos in range(1,nmarkers+1):
  name = pline[spos]
  if name not in refalleles.keys():
    print("ERROR, could not find marker",name,"in reference alleles")
    exit(-1)
  spos2name[spos] = name 

for line in seizlines[1:]:
  pline = line.rstrip().split("\t")
  sid = pline[0]

  for spos in range(1,nmarkers+1):
    msat = spos2name[spos]
    if pline[spos] not in refalleles[msat]:
      if sid not in abberant:
        abberant[sid] = []
      stuff = [msat,pline[spos]]
      abberant[sid].append(stuff)

retval = 0
if len(abberant) > 0:
  print("The following samples had alleles not found in the reference data")
  print("MatchID\tLocus\tAllele")
  for sid in abberant:
    outline = sid 
    for entry in abberant[sid]:
      outline += "\t" + entry[0] + "\t" + entry[1]
    print(outline)
    if len(abberant[sid]) > 2:
      retval = 1

exit(retval)
