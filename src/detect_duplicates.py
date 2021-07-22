# examine file PREFIX_raw.tsv and find any samples that are perfect
# matches when unknown data is taken into account.  If any are found,
# return a list and an error code (to stop scripts) so that they can
# be consolidated; it is an error to go forward with duplicates as
# it messes up VORONOI, familial matching, and individual names.

import sys
if len(sys.argv) != 2:
  print("USAGE:  detect_duplicates PREFIX_raw.tsv")
  exit(-1)

infilename = sys.argv[1]

data = {}

# read in input data
for line in open(infilename,"r"):
  if line.startswith("MatchID"):  continue   # skip header
  line = line.rstrip().split("\t")
  id = line[0]
  msats = line[1:]
  assert len(msats) == 16
  if id not in data:
    data[id] = []
  data[id].append(msats)

# check for too many lines for one sample (suggesting duplicate IDs)
for id in data:
  if len(data[id]) < 2:
    print("Too few data lines found for",id)
    exit(-1)
  if len(data[id]) > 2:
    print("Too many data lines found for",id,"suggesting duplicate IDs")
    exit(-1)

# organize genotypes
parsedata = []
for id in data:
  msats = data[id]
  parsemsats = []
  for m1, m2 in zip(msats[0],msats[1]):
    geno = [int(m1),int(m2)]
    geno.sort()
    parsemsats.append(geno)
  parsedata.append([id,parsemsats])

# check for matches
allmissing = [-999,-999]
missing = -999
numids = len(parsedata)
for i in range(0,numids - 1):
  for j in range(i+1,numids):  
    assert parsedata[i][0] != parsedata[j][0]  # comparing it to itself?!
    match = True
    for m1, m2 in zip(parsedata[i][1],parsedata[j][1]):
      # no missing data
      if missing not in m1 and missing not in m2:
        if m1 != m2:
          match = False
          break

      # all missing data for at least one
      if m1 == allmissing or m2 == allmissing:  continue

      # some missing data
      # problem case is [-999,271], [271, 277]
      for a in m1:
        if a != missing and a not in m2:  
          match = False
          break
      for a in m2:
        if a != missing and a not in m1:
          match = False
          break

    if match:  
      print("Samples",parsedata[i][0],parsedata[j][0],"are exact matches")
      exit(-1)

    
