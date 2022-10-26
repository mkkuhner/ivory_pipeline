# This version uses the new-style VORONOI output (VORONOI should
# be run with -k or -N)

import sys
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.pyplot as plt
import os
import math
import statistics

margin = 7

########################################################################
# functions

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def latlong_to_grid(mylat,mylong,minlat,maxlat,minlong,maxlong):
  assert minlat <= mylat <= maxlat
  assert minlong <= mylong <= maxlong
  gridlat = int(math.floor(mylat) - minlat)
  gridlong = int(math.floor(mylong) - minlong)
  return gridlat,gridlong

# this routine collects VORONOI results for *all* samples
def read_voronoi(printprobs,minlat,maxlat,minlong,maxlong):
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
      gridlat, gridlong = latlong_to_grid(mylat,mylong,minlat,maxlat,minlong,maxlong)
      vordict[sid][gridlat][gridlong] = myprob
  return vordict

# this routine collects SCAT results for *one* sample 
def read_scat(sfiles,gridsize,minlat,maxlat,minlong,maxlong):
  # this code accumulates over all 9 SCAT files for one sample
  gridcounts = [[0 for x in range(0,gridsize)] for x in range(0,gridsize)]
  lats = []
  longs = []
  for file in sfiles:
    lines = open(file,"r").readlines()
    for line in lines[99:-1]:  # skip burning!
      line = line.rstrip().split()
      mylat = float(line[0])
      mylong = float(line[1])
      gridlat, gridlong = latlong_to_grid(mylat,mylong,minlat,maxlat,minlong,maxlong)
      gridcounts[gridlat][gridlong] += 1
      lats.append(mylat)
      longs.append(mylong)
  medlat = statistics.median(lats)
  medlong = statistics.median(longs)
  return lats,longs,gridcounts,medlat,medlong

# find biggest entry in a 2D grid
def get_maximum(vgrid):
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
  return [bestx,besty]

# use this map for plotting point estimates
def makemap_for_summaries(proj,minlat,maxlat,minlong,maxlong):
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
  gl.top_labels = None 
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="blue")
  m.add_feature(cfeature.LAND, color="tan")
  return m

# use this map for heatmaps
def makemap_for_heatmaps(proj,minlat,maxlat,minlong,maxlong):
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="white")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True, linestyle="--")
  gl.top_labels = None 
  gl.xlines = False
  gl.ylines = False
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="white")
  m.add_feature(cfeature.LAND, color="tan")
  return m

# read the PREFIX_mapinfo file
def read_mapinfo(mapfile):
  # read prefix_mapinfo for grid dimensions
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

# read a map file
# this code has to be in synch with readboundary.cpp's version
def mapinfo_from_map(mapfilename):
  lats = []
  longs = []
  for line in open(mapfilename,"r"):
    line = line.rstrip().split()
    lats.append(float(line[0]))
    longs.append(float(line[1]))

  minlat = math.floor(min(lats)) - margin
  minlong = math.floor(min(longs)) - margin
  # +1 in next two lines because if the upper right square is X,Y then the
  # address of the actual corner is X+1,Y+1.
  maxlat = math.floor(max(lats)) + margin + 1
  maxlong = math.floor(max(longs)) + margin + 1

  size_lat = int(maxlat - minlat)
  size_long = int(maxlong - minlong)
  if size_lat != size_long:
    maxgrid = max(size_lat,size_long)
    mingrid = min(size_lat,size_long)
    diff = maxgrid - mingrid
    leftadd = math.floor(diff/2)    # deliberate truncation
    rightadd = diff - leftadd
    print("diff",diff,"leftadd",leftadd,"rightadd",rightadd)
    if maxgrid == maxlat:   # lat is bigger
      minlong -= leftadd
      maxlong += rightadd
      size_long = maxlong - minlong
      assert size_long == size_lat
    else:     # long is bigger
      minlat -= leftadd
      maxlat += rightadd
      size_lat = maxlat - minlat
      assert size_long == size_lat
  print(minlat,minlong,maxlat,maxlong,size_lat)
  return [minlat,minlong,maxlat,maxlong,size_lat]
  


########################################################################
# main program

if len(sys.argv) != 3 and len(sys.argv) != 4:
  print("USAGE:  python plot_scat_vor.py ivory_paths.tsv prefix sid")
  print("If no sid is given, plots everything")
  exit(-1)

pathsfile = sys.argv[1]
prefix = sys.argv[2]
reportdir = prefix + "_reports/"
if len(sys.argv) == 4:
  wanted_sid = sys.argv[3]
else:
  wanted_sid = None

pathdir = readivorypath(pathsfile)
map_path, map_prefix = pathdir["map_prefix"]
vor_mapinfo = prefix + "_mapinfo"
namesfile = prefix + "_names.txt"
regionfilename = prefix + "_regions"

# NOTE:  If the mapinfo file exists, we will read it and will assume that
# VORONOI was run.  If it does not exist, we will go back to the original
# map, and will assume VORONOI was NOT run (so will only handle SCAT results).
# To figure out which map to use, we look at the name of the directory we
# are currently in; "nsavannah" uses savannah map, "nforest" uses forest map,
# anything else ends with an error message.

if os.path.isfile(vor_mapinfo):   # VORONOI ran
  use_voronoi = True
  print("Plotting both SCAT and VORONOI results")
  minlat,minlong,maxlat,maxlong,dim = read_mapinfo(prefix + "_mapinfo")
else:                             # VORONOI did not run
  use_voronoi = False
  print("Plotting SCAT results; no VORONOI detected")
  mydirname = os.getcwd().split("/")[-1]
  if mydirname == "nforest":
    species = "forest"
  elif mydirname == "nsavannah":
    species = "savannah"
  else:
    print("Unable to deduce which map was used for SCAT; this program")
    print("needs to be run in either 'nsavannah' or 'nforest'")
    exit(-1)
  mapfile = map_path + map_prefix + "_" + species + ".txt"
  minlat,minlong,maxlat,maxlong,dim = mapinfo_from_map(mapfile)

# if not doing a single SID, read list of SIDs (this was written by
# setupvoronoi.py and exists even if voronoi didn't run) 
wantednames = []
if wanted_sid is None:
  namesfile = prefix + "_names.txt"
  for line in open(namesfile,"r"):
    wantednames.append(line.rstrip())
else:
  wantednames.append(wanted_sid)

# read SCAT data
dirnames = [str(x) + "/outputs" for x in range(1,10)]
scatgrids = {}
scatraw = {}
scatmedians = {}
for sid in wantednames:
  scatfiles = []
  for dir in dirnames:
    scatfiles.append(dir + "/" + sid)
  scatlats,scatlongs,gridcounts,medlat,medlong = read_scat(scatfiles,dim,minlat,maxlat,minlong,maxlong)
  scatgrids[sid] = gridcounts
  scatmedians[sid] = [medlat,medlong]
  scatraw[sid] = [scatlats,scatlongs]
  
if use_voronoi:
  # read Voronoi printprobs data
  printprobs = prefix + "_printprobs"
  vordict = read_voronoi(printprobs,minlat,maxlat,minlong,maxlong)

  # read Voronoi regions data, for median estimation
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

# if we only want one SID, eliminate the others
if wanted_sid is not None:
  newvordict = {}
  newvordict[wanted_sid] = vordict[wanted_sid]
  vordict = newvordict

# prepare reports and graphs
lats = [x for x in range(minlat,maxlat+1)]
longs = [x for x in range(minlong,maxlong+1)]

best_vorx = []
best_vory = []
med_vorx = []
med_vory = []
best_scatx = []
best_scaty = []
med_scatx = []
med_scaty = []

# set up file for point estimate reporting
pointfile = open(reportdir + prefix + "_point_estimates.tsv","w")
if use_voronoi:
  hdr = "SID\tVoronoi_bestsquare\tVoronoi_median\tSCAT_bestsquare\tSCAT_median\n"
else:
  hdr = "SID\tSCAT_bestsquare\tSCAT_median\n"

pointfile.write(hdr)


# plot heatmaps

figno = 1
crs_lonlat = ccrs.PlateCarree()

# make overall image of Voronoi regions 
if use_voronoi:
  plt.figure(figno)
  m = makemap_for_heatmaps(crs_lonlat,minlat,maxlat,minlong,maxlong)
  x,y = np.meshgrid(longs,lats)
  m.pcolormesh(x,y,regions,shading="flat",cmap=plt.cm.hot,transform=crs_lonlat)
  sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
  sm._A = []
  cb = plt.colorbar(sm)
  cb.set_ticks([])
  plt.title("Voronoi region");
  plt.savefig(reportdir + "voronoi_region.png")
  plt.close()
  figno += 1


for sid in wantednames:
  pointline = sid  
  shortsid = sid
  if len(shortsid) > 15:
    shortsid = shortsid[:15] + "..."

  # voronoi data
  if use_voronoi:
    plt.figure(figno)
    figno += 1
    vgrid = vordict[sid]

    # get best point for summary graph
    vorx,vory = get_maximum(vgrid)
    best_vorx.append(vorx+minlat+0.5)
    best_vory.append(vory+minlong+0.5)
    pointline += "\t" + str(vorx+minlat+0.5) + "," + str(vory+minlong+0.5) 

    # make individual sample heatmaps
    m = makemap_for_heatmaps(crs_lonlat,minlat,maxlat,minlong,maxlong)
    x,y = np.meshgrid(longs,lats)
    m.pcolormesh(x,y,vgrid,shading="flat",cmap=plt.cm.hot,transform=crs_lonlat)
    sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
    sm._A = []
    cb = plt.colorbar(sm)
    cb.set_ticks([])

    plt.title("Voronoi " + shortsid);
    plt.savefig(reportdir + sid + "_voronoi.png")
    plt.close()

    # following code makes median-style VORONOI point estimates by masking out
    # everything outside the VORONOI region, then taking median lat/long of the
    # survivors.  Code from median_voronoi.py.

    # how this works:  regions[][] contains a count of the number
    # of times each grid square was in R.  For each SCAT observation,
    # we add it to the list a number of times equal to regions[][],
    # which is equivalent to weighting it by how often it's in R
    # --done this way so we can take a median.
    masked_scatdata = []
    for vlat,vlong in zip(scatraw[sid][0],scatraw[sid][1]):
      gridlat,gridlong = latlong_to_grid(vlat,vlong,minlat,maxlat,minlong,maxlong)
      for i in range(0,regions[gridlat][gridlong]):
        masked_scatdata.append([vlat,vlong])

    # take median lat/long
    vlats = [x[0] for x in masked_scatdata]
    vlongs = [x[1] for x in masked_scatdata]
    medvlat = statistics.median(vlats)
    medvlong = statistics.median(vlongs)
    med_vorx.append(medvlat)
    med_vory.append(medvlong)
    pointline += "\t" + str(medlat) + "," + str(medlong)

  # scat data
  plt.figure(figno) 
  figno += 1
  sgrid = scatgrids[sid]
  medlat,medlong = scatmedians[sid]
  m = makemap_for_heatmaps(crs_lonlat,minlat,maxlat,minlong,maxlong)

  # get best point for summary graph
  scatx,scaty = get_maximum(sgrid)
  best_scatx.append(scatx+minlat+0.5)
  best_scaty.append(scaty+minlong+0.5)
  med_scatx.append(medlat)
  med_scaty.append(medlong)
  pointline += "\t" + str(scatx+minlat+0.5) + "," + str(scaty+minlong+0.5) 
  pointline += "\t" + str(medlat) + "," + str(medlong) 
  pointline += "\n"
  pointfile.write(pointline)

  x,y = np.meshgrid(longs,lats)
  m.pcolormesh(longs,lats,sgrid,shading="flat",cmap=plt.cm.hot,transform=crs_lonlat)
  sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
  sm._A = []
  cb = plt.colorbar(sm)
  cb.set_ticks([])

  plt.title("Scat " + shortsid)
  plt.savefig(reportdir + sid + "_scat.png")
  plt.close()

pointfile.close()

# summary figures

if use_voronoi:
  # voronoi summary by squares
  figno += 1
  plt.figure(figno)
  m = makemap_for_summaries(crs_lonlat,minlat,maxlat,minlong,maxlong)
  for x,y in zip(best_vorx,best_vory):
    m.plot(y,x,"r+",transform=crs_lonlat)
  plt.title("Voronoi summary: most occupied grid square")
  plt.savefig(reportdir+"voronoi_summary_squares.png")

  # voronoi summary by medians
  figno += 1
  plt.figure(figno)
  m = makemap_for_summaries(crs_lonlat,minlat,maxlat,minlong,maxlong)
  for x,y in zip(med_vorx,med_vory):
    m.plot(y,x,"r+",transform=crs_lonlat)
  plt.title("Voronoi summary: median lat/long")
  plt.savefig(reportdir+"voronoi_summary_medians.png")

# scat summary by squares
figno += 1
plt.figure(figno)
m = makemap_for_summaries(crs_lonlat,minlat,maxlat,minlong,maxlong)
for x,y in zip(best_scatx,best_scaty):
  m.plot(y,x,"r+",transform=crs_lonlat)
plt.title("Scat summary:  most occupied grid square")
plt.savefig(reportdir+"scat_summary_squares.png")

# scat summary by medians
figno += 1
plt.figure(figno)
m = makemap_for_summaries(crs_lonlat,minlat,maxlat,minlong,maxlong)
for x,y in zip(med_scatx,med_scaty):
  m.plot(y,x,"r+",transform=crs_lonlat)
plt.title("Scat summary:  median lat/long")
plt.savefig(reportdir+"scat_summary_medians.png")

