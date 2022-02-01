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
  sz1 = sid2seiz[pline[0]]
  sz2 = sid2seiz[pline[1]]
  outline += sz1 + "\t" + sz2 + "\t" + line
  outlines.append(outline)

outfilename = sys.argv[1][:-4]
outfilename += "_full.tsv"
outfile = open(outfilename,"w")
for line in outlines:
  outfile.write(line)
outfile.close()
