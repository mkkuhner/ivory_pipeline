# diagnose if need to run savannah, forest
# for each species
#   collect scat data
#   collect voronoi data if available
#   plot heatmaps of individuals
#   store data to plot summaries
# write summary table
# plot summary images

import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import math
import statistics
import subprocess
from subprocess import Popen, PIPE
import pickle


###################################################
# functions

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def run_and_report(command,errormsg):
  process = Popen(command)
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

def latlong_to_grid(mylat,mylong,mapdata):
  minlat,minlong,maxlat,maxlong,dim = mapdata
  assert minlat <= mylat <= maxlat
  assert minlong <= mylong <= maxlong
  gridlat = int(math.floor(mylat) - minlat)
  gridlong = int(math.floor(mylong) - minlong)
  return gridlat,gridlong

# this routine collects SCAT results for one sample
# from the 9 SCAT output directories of a typical run
# it does both a grid and a non-grid storage form

def read_scat(scatdirs,mapdata):
  scatfiles = []
  for dir in scatdirs:
    scatfiles.append(dir + "/" + sid)
  data = []
  gridsize = mapdata[4] 
  gridcounts = [[0 for x in range(0,gridsize)] for x in range(0,gridsize)]

  for file in scatfiles:
    lines = open(file,"r").readlines()
    for line in lines[99:-1]:   # skip burnin and last line
      line = line.rstrip().split()
      latlong = [float(x) for x in line[0:2]]   # omitting the likelihood
      data.append(latlong)
      gridlat,gridlong = latlong_to_grid(latlong[0],latlong[1],mapdata)
      gridcounts[gridlat][gridlong] += 1
  return data, gridcounts

# this routine collects VORONOI results for *all* samples
def read_voronoi(printprobs,mapdata):
  minlat,minlong,maxlat,maxlong,dim = mapdata
  vordict = {}
  for line in open(printprobs,"r"):
    line = line.rstrip().split()
    if line[0].startswith("#"):  #header line of an elephant
      sid = line[0][1:]
      assert sid not in vordict
      vordict[sid] = [[0.0 for x in range(0,dim)] for x in range(0,dim)]
    else:
      mylat = float(line[0])
      mylong = float(line[1])
      myprob = float(line[2])
      # convert to grid coordinates
      gridlat, gridlong = latlong_to_grid(mylat,mylong,mapdata)
      vordict[sid][gridlat][gridlong] = myprob
  return vordict

# read the PREFIX_mapinfo file
def read_mapinfo(mapfile):
  mapinfolines = open(mapfile,"r").readlines()
  if len(mapinfolines) != 4:
    print("Error: file",prefix+"_mapinfo","was",len(mapinfolines),"lines long",)
    print("should have been 4.")
    exit(-1)
  ll = mapinfolines[0].rstrip().split(",")
  lllat = int(ll[0].split()[-1])
  lllong = int(ll[1])
  ur = mapinfolines[1].rstrip().split(",")
  urlat = int(ur[0].split()[-1])
  urlong = int(ur[1])
  nsdim = int(mapinfolines[2].rstrip().split(":")[1].split()[0])
  ewdim = int(mapinfolines[3].rstrip().split(":")[1].split()[0])
  if (nsdim != ewdim):
    print("FAILURE: grid not square,",sys.argv[0],"assumes a square grid")
    exit(-1)
  dim = nsdim
  return [lllat,lllong,urlat,urlong,dim]


# read a map file (use if mapinfo not available)
def mapinfo_from_map(mapfilename):
  lats = []
  longs = []
  for line in open(mapfilename,"r"):
    line = line.rstrip().split()
    lats.append(float(line[0]))
    longs.append(float(line[1]))
  lllat = min(lats)
  lllong = min(longs)
  # +1 in next two lines because if the upper right square is X,Y then the
  # address of the actual corner is X+1,Y+1.
  urlat = max(lats) + 1
  urlong = max(longs) + 1
  nsdim = urlat - lllat
  ewdim = urlong - lllong
  if (nsdim != ewdim):
    print("FAILURE: grid not square")
    exit(-1)
  return [lllat,lllong,urlat,urlong,nsdim]

# find biggest entry in a 2D grid
def latlong_of_maximum(vgrid,minlat,minlong):
  bestx = -99
  besty = -99
  bestval = -99.0
  for x in range(0,len(vgrid)):
    for y in range(0,len(vgrid[0])):
      if vgrid[x][y] > bestval:
        bestval = vgrid[x][y]
        bestx = x
        besty = y
  assert bestx != -99
  return [bestx+minlat,besty+minlong]

# use this map for plotting point estimates
def makemap_for_summaries(proj,mapdata,backgroundcolor):
  minlat,minlong,maxlat,maxlong,dim = mapdata
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
  gl.top_labels = None
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="black")
  m.add_feature(cfeature.LAND, color=backgroundcolor)
  return m

# use this map for heatmaps
def makemap_for_heatmaps(proj,mapdata,landcolor):
  minlat,minlong,maxlat,maxlong,dim = mapdata
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="white")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True, linestyle="--")
  gl.top_labels = None
  gl.xlines = False
  gl.ylines = False
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="white")
  m.add_feature(cfeature.LAND, color=landcolor)
  return m
def str_latlong(latlong):
  outstring = str(latlong[0]) + ", " + str(latlong[1])
  return outstring

###################################################
# main

import sys, os
if len(sys.argv) != 3:
  print("USAGE:  replot.py prefix picklefile.pkl")
  exit(-1)

prefix = sys.argv[1]
picklefile = prefix + "/" + sys.argv[2]

figno = 0

picklefile = open(picklefile,"rb")
prefix = pickle.load(picklefile)
maxima = pickle.load(picklefile)
mapdata = pickle.load(picklefile)
crs_lonlat = pickle.load(picklefile)
reportdir = pickle.load(picklefile)
reportdir = prefix + "/" + reportdir

# scat median
statistic = "scatmed"
progname = "SCAT"

alpha = 1.0
#mygold = [0.8, 0.4, 0.0, alpha]
mygold = [1.0, 1.0, 1.0, alpha]
mygreen = [0.0, 1.0, 0.0, alpha]
backgroundcolor = "beige"

markeredgewidth = 0.6
markeredgecolor = "k"
markersize = 9

plt.figure(figno)
figno += 1
if "med" in statistic:
  statname = "median"
else:
  statname = "best"
m = makemap_for_summaries(crs_lonlat,mapdata,backgroundcolor)
for species,color in zip(["savannah","forest"],[mygold,mygreen]):
  if species not in maxima:  continue
  data = maxima[species]
  lats = []
  longs = []
  for sid in data:
    lats.append(data[sid][statistic][0])
    longs.append(data[sid][statistic][1])
  first = True
  for x,y in zip(lats,longs):
    if first:
      m.plot(y,x,"r.",transform=crs_lonlat,markeredgecolor=markeredgecolor,markersize=markersize,markerfacecolor=color,label=species)
      first = False
    else:
      m.plot(y,x,"r.",transform=crs_lonlat,markeredgecolor=markeredgecolor,markersize=markersize,markerfacecolor=color)

plt.legend(loc='lower left')

plt.title(prefix + " " + statname)
plt.savefig(reportdir + prefix + "_" + progname + "_" + statname + ".png")
