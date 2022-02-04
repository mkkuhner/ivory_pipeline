import sys

if len(sys.argv) != 4:
  print("USAGE: python rout2db.py r_output.tsv seizure_metadata.tsv sector")
  exit(-1)

rinlines = open(sys.argv[1],"r").readlines()
metalines = open(sys.argv[2],"r").readlines()
secno = sys.argv[3]

sid2seiz = {}
for line in metalines:
  pline = line.rstrip().split("\t")
  seiz = pline[0]
  sid = pline[1]
  sid2seiz[sid] = seiz

outline = "secno\tsz1\tsz2\t" + rinlines[0]
outlines = [outline,]
for line in rinlines[1:]:
  outline = secno + "\t"
  pline = line.rstrip().split("\t")
  sid1 = pline[0]
  sid2 = pline[1]
  if sid1 > sid2:
    # using python swap pecularity
    sid2, sid1 = sid1, sid2
  sz1 = sid2seiz[sid1]
  sz2 = sid2seiz[sid2]
  parselen = len(sid1) + len(sid2) + 2  # +2 for the tabs
  outline += sz1 + "\t" + sz2 + "\t" + sid1 + "\t" + sid2 + "\t" + line[parselen:]
  outlines.append(outline)

outfilename = sys.argv[1][:-4]
outfilename += "_full.tsv"
outfile = open(outfilename,"w")
for line in outlines:
  outfile.write(line)
outfile.close()
