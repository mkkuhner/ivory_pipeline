# version of plot_clust.py adapted for the long sims
# needs user to specify species (it should be savannah)
# only does clust
# no heatmaps
# run in results directory (bottom directory of heirarchy)

# old flowchart
# diagnose if need to run savannah, forest
# for each species
#   collect scat data
#   collect voronoi data if available
#   collect clust data if available
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

def str_latlong(latlong):
  outstring = str(latlong[0]) + ", " + str(latlong[1])
  return outstring

def add_grid(accumulator, source):
  for i in range(0,dim):
    for j in range(0,dim):
      accumulator[i][j] += source[i][j]

def vor_style_analysis(sid,resultsdict,maxima,prog,code,figno):
  # implementing the weighted mean lat and long of the original paper, NOT medians
  if sid not in resultsdict:
    return figno
  vgrid = resultsdict[sid]

  # mean weighted lat/long 
  latweights = [0 for x in range(len(vgrid))]
  longweights = [0 for x in range(len(vgrid))]
  mylats = []
  mylongs = []

  # lazy but easy coding for weighted means
  # latitudes
  for x in range(0,len(vgrid)):
    mylat = x + minlat + 0.5
    mylats.append(mylat)
    for y in range(0,len(vgrid)):
      latweights[x] += vgrid[x][y]

  # longitudes
  for y in range(0,len(vgrid)):
    mylong = y + minlong + 0.5
    mylongs.append(mylong)
    for x in range(0,len(vgrid)):
      longweights[y] += vgrid[x][y]

  medlat = np.average(mylats,weights=latweights)
  medlong = np.average(mylongs,weights=longweights)
  maxima[sid][code] = [medlat,medlong]
  return figno

###################################################
# main

import sys, os
if len(sys.argv) != 4:
  print("USAGE:  plot_sim_clust.py prefix species ivory_paths.tsv")
  exit(-1)

prefix = sys.argv[1]
species = sys.argv[2]
pathfile = sys.argv[3]

pathdir = readivorypath(pathfile)
# fill in which variables we need here
map_path,map_prefix = pathdir["map_prefix"]

# switch to main seizure directory
#os.chdir(prefix)

# make reports directory if it does not already exist
reportdir = "reports/"
if not os.path.isdir(reportdir):
  command = ["mkdir",reportdir]
  run_and_report(command,"Unable to create reports directory")

print("Tabulating clust results for:", species)

boundaries = {}
maxima = {}    # by sid individual

# read map info to establish the grid
mapfile = prefix + "_clust_mapinfo"
if os.path.isfile(mapfile):  # found a mapinfo file
  mapdata = read_mapinfo(mapfile)
else:
  print("Could not find _mapinfo file, terminating")
  exit(-1)
minlat,minlong,maxlat,maxlong,dim = mapdata
boundaries[species] = mapdata
meshlats = [x for x in range(minlat,maxlat+1)]
meshlongs = [x for x in range(minlong,maxlong+1)]
meshx,meshy = np.meshgrid(meshlongs,meshlats)

tot_gridcounts = [[0 for x in range(0,dim)] for x in range(0,dim)]

# if CLUST ran, read the bulk CLUST results (same routine as VORONOI)
clustdict = read_voronoi(prefix + "_clust_printprobs", mapdata)

wantednames = list(clustdict.keys())
outfile = open(prefix + "_clust_names.txt","w")
for name in wantednames:
  outfile.write(name + "\n")
outfile.close()

# process individuals
figno = 0
for sid in wantednames:
  maxima[sid] = {}
  shortsid = sid.split("-")
  shortsid = "-".join(shortsid[0:3])
  figno = vor_style_analysis(sid,clustdict,maxima,"clust","clustmed",figno)
  
# summary plots
# the forest and savannah maps are different sizes (same scale, luckily!)
# so we have to make a bounding box that fits both
minlats = []
minlongs = []
maxlats = []
maxlongs = []
for species in boundaries:
  minlats.append(boundaries[species][0])
  minlongs.append(boundaries[species][1])
  maxlats.append(boundaries[species][2])
  maxlongs.append(boundaries[species][3])
margin = 7
mapdata = []
mapdata.append(min(minlats) + margin)
mapdata.append(min(minlongs) + margin)
mapdata.append(max(maxlats) - margin)
mapdata.append(max(maxlongs) - margin)
mapdata.append(None)

# summary table
outfile = reportdir + prefix + "_point_estimates.tsv"
outfile = open(outfile,"w")
outline = "SID\tspecies\tCLUST"
outline += "\n"
outfile.write(outline)
for sid in maxima:
  outline = [sid,species]
  outline.append(str_latlong(maxima[sid]["clustmed"]))
  outline = "\t".join(outline) + "\n"
  outfile.write(outline)
outfile.close()
