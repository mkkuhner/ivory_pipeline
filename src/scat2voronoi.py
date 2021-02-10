def filldigits(ndigits,val):
  outstr = str(val)
  while len(outstr) < ndigits:
    outstr = "0" + outstr
  return outstr

import sys

if len(sys.argv) != 2:
  print("USAGE: python scat2voronoi.py masterinfile")
  print("  each line of masterinfile is a path to a scat output dir")
  exit(-1)

inpaths = open(sys.argv[1],"r").readlines()
inpaths = [x.rstrip() for x in inpaths]

if len(inpaths) != 9:
  print("the master infile must contain exactly 9 paths, each on a separate line")
  print("it currently has",len(inpaths),"lines in it.")
  exit(-1)

scatids = ["r","s","t","u","v","w","x","y","z"]
import os
import shutil

# make a DETERMINISTIC, REPEATABLE mapping of elephant name to
# ID number, based on the first Scat directory
# if you instead use the stochastic mapping of os.walk you will
# sooner or later regret it 

# determine all elephant names
# we assume all elephants are present in the first SCAT directory
allfiles = []
for root,dirs,files in os.walk(inpaths[0]):
  for fn in files:
    if fn.startswith("Output_"):
      continue
    allfiles.append(fn)

# sort and identify them
namedict = {}
allfiles.sort()
count = 1
for fn in allfiles:
  label = filldigits(3,count)
  namedict[fn] = label
  count += 1

# copy them over, making a samplemap in the process
for path,scatid in zip(inpaths,scatids):
  outfile = open("samplemap."+scatid,"w")
  for root,dirs,files in os.walk(path):
    for fn in files:
      if fn.startswith("Output_"):
        continue
      count = namedict[fn]
      outfile.write(count+"\t"+fn+"\n")
      if not path.endswith("/"):
        path += "/"
      shutil.copyfile(path+fn,"./"+count+scatid)
  outfile.close()

outfile = open("voronoiin.txt","w+")
numelephants = len(namedict)
outline = str(numelephants)
for x in range(1,numelephants+1):
  outline += " " + str(x)
outline += "\n"
outfile.write(outline)
outfile.close()
