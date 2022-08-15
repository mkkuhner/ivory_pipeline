# library of useful functions for ivory_pipeline

from haversine import haversine, Unit
from subprocess import Popen
import math
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

############################################################################
# file reading

## read the ivory_paths file into a structure
def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

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

#########################################################################
# system interaction

## execute a system command and terminate with error message on failure
def run_and_report(command,errormsg):
  process = Popen(command)
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

#########################################################################
# latitude/longitude and grid management

## convert latitude/longitude to grid coordinates
def latlong_to_grid(mylat,mylong,mapdata):
  minlat,minlong,maxlat,maxlong,dim = mapdata
  assert minlat <= mylat <= maxlat
  assert minlong <= mylong <= maxlong
  gridlat = int(math.floor(mylat) - minlat)
  gridlong = int(math.floor(mylong) - minlong)
  return gridlat,gridlong

## distance between two lat/long pairs
def dist_between(loc1,loc2):
  return haversine(loc1,loc2,Unit.KILOMETERS)


##########################################################################
# maps

## map for plotting point estimates (tan land, white seas)
def makemap_for_summaries(proj,mapdata):
  crs_lonlat = ccrs.PlateCarree()
  minlat,minlong,maxlat,maxlong,dim = mapdata
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
  gl.top_labels = None
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="black")
  m.add_feature(cfeature.LAND, color="tan")
  return m

## map for heatmaps 
def makemap_for_heatmaps(proj,mapdata):
  crs_lonlat = ccrs.PlateCarree()
  minlat,minlong,maxlat,maxlong,dim = mapdata
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.5, color="white")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True, linestyle="--")
  gl.top_labels = None
  gl.xlines = False
  gl.ylines = False
  m.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle="solid", color="white")
  #m.add_feature(cfeature.LAND, color="tan")
  return m

