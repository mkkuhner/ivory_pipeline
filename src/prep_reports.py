import math

###################################################################

#filenames

import sys
import os
if len(sys.argv) != 3:
  print("USAGE: python2 prep_reports.py prefix voronoiin")
  print("uses prefix_indprobs, prefix_mapinfo, and samplemap.r files")
  exit()

prefix = sys.argv[1]
indprobs_file = prefix + "_indprobs"
outdir = prefix + "_reports/"
vorin_file = sys.argv[2]

if not os.path.isdir(outdir):
  os.mkdir(outdir)
else:
  print("Warning:  overwriting material in ",outdir)
  

#associate SCAT2 output name with normal name
naming = {}
for line in open("samplemap.r","r"):
  line = line.rstrip().split()
  fileno = int(line[0])
  name = line[1]
  naming[fileno] = name

import matplotlib.pyplot as plt

# process voronoi data 

# first read prefix_mapinfo for grid dimensions
mapinfolines = open(prefix+"_mapinfo","r").readlines()
if len(mapinfolines) != 4:
  print("Error: file",prefix+"_mapinfo","was",len(mapinfolines),"lines long",)
  print("should have been 4.")
  exit(-1)
# we assume a properly formatted mapinfo file
ll = mapinfolines[0].rstrip().split(",")
lllat = int(ll[0].split()[-1])
lllong = int(ll[1])
ur = mapinfolines[1].rstrip().split(",")
urlat = int(ur[0].split()[-1])
urlong = int(ur[1])
nsdim = int(mapinfolines[2].rstrip().split(":")[1].split()[0])
ewdim = int(mapinfolines[3].rstrip().split(":")[1].split()[0])
# debug DEBUG warning WARNING
if (nsdim != ewdim):
  print("WARNING: grid not square, currently",sys.argv[0],"assumes a square grid")
  exit(-1)
#dim = 67
dim = nsdim
print("Grid dimensions are",dim,"by",dim)

# read Voronoi data from _indprobs file
eldata = []
count = 0
rawdata = []
for line in open(indprobs_file,"r"):
  rawdata.append(line)
  count += 1
  if count == dim:
    eldata.append(rawdata)
    rawdata = []
    count = 0

print("Number of elephants found:",len(eldata))

# read voronoiin file to establish which elephants were used
vorinlines = open(vorin_file,"r").readlines()
assert len(vorinlines) == 1
vordata = vorinlines[0].rstrip().split()
numdat = int(vordata[0])
vordata = vordata[1:]
assert len(vordata) == numdat
vordata = [int(x) for x in vordata]
index_to_name = {}
name_to_index = {}
for index,entry in zip(range(0,numdat),vordata):
  index_to_name[index] = naming[entry]
  name_to_index[naming[entry]] = index
  

index = 0
for elephant in eldata:
  animalname = index_to_name[index]
  outfilename = outdir + animalname + "_voronoi.txt"
  outfile = open(outfilename,"w")
  for line in elephant:
    outfile.write(line)
  outfile.close()
  index += 1
