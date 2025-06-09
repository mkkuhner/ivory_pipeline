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
  latdim = urlat - lllat
  longdim = urlong - lllong
  if latdim > longdim:
    diff = latdim - longdim
    lllong -= diff/2
    urlong += diff - diff/2
  elif longdim > latdim:
    diff = longdim - latdim
    lllat -= diff/2
    urlat += diff - diff/2
  latdim = urlat - lllat
  longdim = urlong - lllong
  if (latdim != longdim):
    print("FAILURE: grid not square")
    exit(-1)
  returnvals = [int(x) for x in [lllat,lllong,urlat,urlong,latdim]]
  return returnvals

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
def makemap_for_summaries(proj,mapdata):
  minlat,minlong,maxlat,maxlong,dim = mapdata
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
  gl.top_labels = None
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="black")
  m.add_feature(cfeature.LAND, color="tan")
  return m

# use this map for heatmaps
def makemap_for_heatmaps(proj,mapdata):
  minlat,minlong,maxlat,maxlong,dim = mapdata
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

def plot_summary(prefix,maxima,progname,statistic,figno,mapdata,crs_lonlat,reportdir,whichspecies):
  alpha = 1.0
  mygold = [1.0, 0.9, 0.0, alpha]
  mygreen = [0.0, 1.0, 0.0, alpha]
  backgroundcolor = "tan"
  markeredgewidth=0.6
  markeredgecolor="k"
  markersize = 9
  plt.figure(figno)
  figno += 1
  if "med" in statistic:
    statname = "median"
  else:
    print("Unknown statistic",statistic,"encountered:  terminating")
    exit(-1)
  m = makemap_for_summaries(crs_lonlat,mapdata)
  for species,color in zip(["savannah","forest"],[mygold,mygreen]):
    if species not in whichspecies:  continue
    if species not in maxima:  continue
    data = maxima[species]
    lats = []
    longs = []
    for sid in data:
      lats.append(data[sid][statistic][0])
      longs.append(data[sid][statistic][1])
    firstone = True
    for x,y in zip(lats,longs):
      if firstone:
        firstone = False
        m.plot(y,x,"r.",transform=crs_lonlat,markeredgecolor=markeredgecolor,markersize=markersize,markerfacecolor=color,markeredgewidth=markeredgewidth,label=species)
      else: 
        m.plot(y,x,"r.",transform=crs_lonlat,markeredgecolor=markeredgecolor,markersize=markersize,markerfacecolor=color,markeredgewidth=markeredgewidth)
  plt.legend(loc="lower left")
  plt.title(prefix + " " + statname)
  plt.savefig(reportdir + prefix + "_" + progname + "_" + statname + ".png")
  return(figno)

def str_latlong(latlong):
  outstring = str(latlong[0]) + ", " + str(latlong[1])
  return outstring

###################################################
# main

import sys, os
if len(sys.argv) != 3:
  print("USAGE:  plot_results.py prefix ivory_paths.tsv")
  exit(-1)

prefix = sys.argv[1]
pathfile = sys.argv[2]

pathdir = readivorypath(pathfile)
# fill in which variables we need here
map_path,map_prefix = pathdir["map_prefix"]

# switch to main seizure directory
os.chdir(prefix)

# make reports directory if it does not already exist
reportdir = "reports/"
if not os.path.isdir(reportdir):
  command = ["mkdir",reportdir]
  run_and_report(command,"Unable to create reports directory")

# diagnose which results are available
use_vor = {}
use_vor["savannah"] = False
use_vor["forest"] = False

dirs_to_do = []

if os.path.isdir("nsavannah"):
  dirs_to_do.append("nsavannah/")
  if os.path.isfile("nsavannah/" + prefix + "_regions"):
    use_vor["savannah"] = True
if os.path.isdir("nforest"):
  dirs_to_do.append("nforest/")
  if os.path.isfile("nforest/" + prefix + "_regions"):
    use_vor["forest"] = True

if len(dirs_to_do) == 0:
  print("WARNING:  No species directories found for seizure ",prefix)
  exit(-1)


boundaries = {}
maxima = {}    # species, then individual
allspecies = [x[1:-1] for x in dirs_to_do]
for species in allspecies:
  maxima[species] = {}
scatdirs = [str(x) + "/outputs" for x in range(1,10)]

# set up plotting
crs_lonlat = ccrs.PlateCarree()
figno = 0

# loop over species making individual plots and collecting summary data
for specdir in dirs_to_do:
  os.chdir(specdir)
  species = specdir[1:-1]

  # read map info to establish the grid
  mapfile = prefix + "_mapinfo"
  if os.path.isfile(mapfile):  # found a mapinfo file
    mapdata = read_mapinfo(mapfile)
  else:   # no mapinfo file, go back to original map
    mapfile = map_path + map_prefix + "_" + species + ".txt"
    mapdata = mapinfo_from_map(mapfile)
  minlat,minlong,maxlat,maxlong,dim = mapdata
  boundaries[species] = mapdata
  meshlats = [x for x in range(minlat,maxlat+1)]
  meshlongs = [x for x in range(minlong,maxlong+1)]
  meshx,meshy = np.meshgrid(meshlongs,meshlats)

  # if VORONOI ran, process the regions file
  if use_vor[species]:
    regionfilename = prefix + "_regions"
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

    # and read the bulk VORONOI results
    vordict = read_voronoi(prefix + "_printprobs",mapdata)

  # get list of wanted names
  # this comes from namefile, which is written by setupvoronoi.py even if
  # VORONOI did not run
  namesfile = prefix + "_names.txt"
  wantednames = []
  for line in open(namesfile,"r"):
    wantednames.append(line.rstrip())

  # process individuals
  for sid in wantednames:
    print("Processing",sid)
    maxima[species][sid] = {}
    shortsid = sid.split("-")
    shortsid = "-".join(shortsid[0:3])

    ## SCAT analyses
    scatnums, scatgrid = read_scat(scatdirs,mapdata)

    # scat median lat/long  "scatmed"
    scatlats = [x[0] for x in scatnums]
    scatlongs = [x[1] for x in scatnums]
    medlat = statistics.median(scatlats)
    medlong = statistics.median(scatlongs)
    maxima[species][sid]["scatmed"] = [medlat,medlong]

    # scat heatmap
    plt.figure(figno)
    figno += 1
    m = makemap_for_heatmaps(crs_lonlat,mapdata)
    m.pcolormesh(meshx,meshy,scatgrid,shading="flat",cmap=plt.cm.hot,transform=crs_lonlat)
    sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
    sm._A = []
    cb = plt.colorbar(sm)
    cb.set_ticks([])
    plt.title("SCAT " + shortsid);
    plt.savefig("../" + reportdir + sid + "_scat.png")
    plt.close()

    # VORONOI analyses
    if use_vor[species]:
      # how this works:  regions[][] contains a count of the number
      # of times each grid square was in R.  For each SCAT observation,
      # we add it to the list a number of times equal to regions[][],
      # which is equivalent to weighting it by how often it's in R
      # --done this way so we can take a median.
      masked_scatnums = []
      for lat, long in scatnums:
        gridlat,gridlong = latlong_to_grid(lat,long,mapdata)
        for i in range(0,regions[gridlat][gridlong]):
          masked_scatnums.append([lat,long])

      # median lat/long "vormed"
      vals = [x[0] for x in masked_scatnums]
      medlat = statistics.median(vals)
      vals = [x[1] for x in masked_scatnums]
      medlong = statistics.median(vals)
      maxima[species][sid]["vormed"] = [medlat,medlong]
      masked_scatnums = []   # get rid of it, it's huge!

      # heatmap for VORONOI
      plt.figure(figno)
      figno += 1
      vorgrid = vordict[sid]
      m = makemap_for_heatmaps(crs_lonlat,mapdata)
      m.pcolormesh(meshx,meshy,vorgrid,shading="flat",cmap=plt.cm.hot,transform=crs_lonlat)
      sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
      sm._A = []
      cb = plt.colorbar(sm)
      cb.set_ticks([])

      plt.title("VORONOI " + shortsid);
      plt.savefig("../" + reportdir + sid + "_voronoi.png")
      plt.close()
  # go back to main seizure directory before doing next species
  os.chdir("..")
    
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

picklefile = open("new_report_pickle.pkl","wb")
pickle.dump(prefix,picklefile)
pickle.dump(maxima,picklefile)
pickle.dump(mapdata,picklefile)
pickle.dump(crs_lonlat,picklefile)
pickle.dump(reportdir,picklefile)

whichspecies_scat = [x[1:-1] for x in dirs_to_do]
whichspecies_vor = []
if use_vor["savannah"]:  whichspecies_vor.append("savannah")
if use_vor["forest"]:  whichspecies_vor.append("forest")

# scat median
figno = plot_summary(prefix,maxima,"SCAT","scatmed",figno,mapdata,crs_lonlat,reportdir,whichspecies_scat)

if use_vor["savannah"] or use_vor["forest"]:
  # voronoi median
  figno = plot_summary(prefix,maxima,"VORONOI","vormed",figno,mapdata,crs_lonlat,reportdir,whichspecies_vor)

# summary table
outfile = reportdir + prefix + "_point_estimates.tsv"
outfile = open(outfile,"w")
outline = "SID\tspecies\tSCAT_median\tVORONOI_median\n"
outfile.write(outline)
for species in allspecies:
  for sid in maxima[species]:
    outline = [sid,species]
    outline.append(str_latlong(maxima[species][sid]["scatmed"]))
    if use_vor[species]:
      outline.append(str_latlong(maxima[species][sid]["vormed"]))
    outline = "\t".join(outline) + "\n"
    outfile.write(outline)
outfile.close()
