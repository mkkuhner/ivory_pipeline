import math
import statistics
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.pyplot as plt


######################################################
# functions

# read the mapinfo file
def read_mapinfo(mapfile):
  # read prefix_mapinfo for grid dimensions
  mapinfolines = open(mapfile,"r").readlines()
  if len(mapinfolines) != 4:
    print("Error: file",prefix+"_mapinfo","was",len(mapinfolines),"lines long",)
    print("should have been 4.")
    exit(-1)
  ll = mapinfolines[0].rstrip().split(",")
  minlat = int(ll[0].split()[-1])
  minlong = int(ll[1])
  ur = mapinfolines[1].rstrip().split(",")
  maxlat = int(ur[0].split()[-1])
  maxlong = int(ur[1])
  nsdim = int(mapinfolines[2].rstrip().split(":")[1].split()[0])
  ewdim = int(mapinfolines[3].rstrip().split(":")[1].split()[0])
  if (nsdim != ewdim):
    print("FAILURE: grid not square,",sys.argv[0],"assumes a square grid")
    exit(-1)
  dim = nsdim
  return [minlat,minlong,maxlat,maxlong,dim]

def latlong_to_grid(mylat,mylong,minlat,maxlat,minlong,maxlong):
  #assert minlat <= mylat <= maxlat
  #assert minlong <= mylong <= maxlong
  gridlat = int(math.floor(mylat) - minlat)
  gridlong = int(math.floor(mylong) - minlong)
  return gridlat,gridlong

# this routine collects SCAT results for *one* sample
def read_scat(sfiles):
  data = []
  for file in sfiles:
    lines = open(file,"r").readlines()
    for line in lines[99:-1]:   # skip burnin and last line
      line = line.rstrip().split()
      latlong = [float(x) for x in line[0:2]]   # omitting the likelihood
      data.append(latlong)
  return data

# use this map for plotting point estimates
def makemap_for_summaries(proj,minlat,maxlat,minlong,maxlong):
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
  gl.top_labels = None
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="black")
  m.add_feature(cfeature.LAND, color="tan")
  return m


######################################################
# main

import sys

if len(sys.argv) != 2:
  print("USAGE: python median_voronoi.py prefix")
  exit(-1)

prefix = sys.argv[1]
mapinfofilename = prefix + "_mapinfo"
samplenamesfilename = prefix + "_names.txt"
regionfilename = prefix + "_regions"
reportdir = prefix + "_reports/"
estimatesfilename = reportdir + prefix + "_point_estimates.tsv" 

# read mapinfo file to set up the grid
minlat,minlong,maxlat,maxlong,dim = read_mapinfo(mapinfofilename)

# read the name file to find which samples were used
sids = []
for line in open(samplenamesfilename,"r"):
  pline = line.rstrip()
  sids.append(pline)
  
# read the regions file from VORONOI
regions = [[0 for x in range(0,dim)] for x in range(0,dim)]
row = 0
for line in open(regionfilename,"r"):
   line = line.rstrip().split()
   assert len(line) == dim
   for i in range(0,dim):
     if line[i] == "1":
       regions[row][i] += 1
   row += 1
   if row == dim:  row = 0

# read the SCAT data files for those names
scatdirs = [str(x) for x in range(1,10)]
scatpaths = [x + "/outputs/" for x in scatdirs]
point_lats = []
point_longs = []
point_estimates = {}

# read in point_estimates file to modify
estlines = open(estimatesfilename,"r").readlines()
sid2estline = {}
for line in estlines[1:]:
  pline = line.rstrip().split("\t")
  sid = pline[0]
  sid2estline[sid] = "\t".join(pline)

estout = open(estimatesfilename,"w")

for sid in sids:
  print("Processing",sid)
  scatfiles = [x + sid for x in scatpaths]
  scatdata = read_scat(scatfiles)
  
  # how this works:  regions[][] contains a count of the number
  # of times each grid square was in R.  For each SCAT observation,
  # we add it to the list a number of times equal to regions[][],
  # which is equivalent to weighting it by how often it's in R
  # --done this way so we can take a median.
  masked_scatdata = []
  for lat,long in scatdata:
    gridlat,gridlong = latlong_to_grid(lat,long,minlat,maxlat,minlong,maxlong)
    for i in range(0,regions[gridlat][gridlong]):
      masked_scatdata.append([lat,long])

  # take median lat/long
  lats = [x[0] for x in masked_scatdata]
  longs = [x[1] for x in masked_scatdata]
  medlat = statistics.median(lats)
  medlong = statistics.median(longs)
  point_estimates[sid] = [medlat,medlong]
  point_lats.append(medlat)
  point_longs.append(medlong)
  print("Estimate for ",sid,medlat,medlong)
  sid2estline[sid] += "\t"+str(medlat)+","+str(medlong)+"\n"

estout.write(estlines[0].rstrip() + "\tVoronoi_median\n")
for sid in sids:
  estout.write(sid2estline[sid])

# plot
crs_lonlat = ccrs.PlateCarree()
plt.figure(0)
myred = [255,0,0,0.5]
# DEBUG this should be communicated somehow, not hardcoded
border = 7
m = makemap_for_summaries(crs_lonlat,minlat+border,maxlat-border,minlong+border,maxlong-border)
for x,y in zip(point_lats,point_longs):
  m.plot(y,x,"r.",transform=crs_lonlat,markeredgecolor="k",markersize=10, markerfacecolor=myred)

plt.title(prefix + ": Voronoi median lat/long")
plt.savefig(prefix + "_voronoi_summary_median.png")

