# library of useful functions for ivory_pipeline

from haversine import haversine, Unit
from subprocess import Popen
import math
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import os

############################################################################
# file reading

## read the ivory_paths file into a structure
def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    if not pline[1].endswith("/"):
      print("FAILURE: ivorypaths file line\n\t"+line+"\nmissing terminal '/' on directory name")
      exit(-1)
    if pline[0] == "fammatch_archive_dir" and not pline[2].endswith("/"):
      print("FAILURE: ivorypaths file line\n\t"+line+"\nmissing terminal '/' on directory name")
      exit(-1)
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

def read_seizure_mods(modfile):
  rejected_seizures = []
  merged_seizures = {}
  state = None
  for line in open(modfile,"r"):
    line = line.rstrip().split("\t")
    if line[0] == "REJECT":
      state = "reject"
      continue
    if line[0] == "MERGE":
      state = "merge"
      continue
    if state == "reject":
      assert len(line) == 1
      rejected_seizures.append(line[0])
      continue
    if state == "merge":
      # merge requires a new name and at least two old names
      assert len(line) >= 3
      newname = line[0]
      for entry in line[1:]:
        merged_seizures[entry] = newname
  return rejected_seizures, merged_seizures


##########################################################################
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
# backups for fammatch archive

# In these functions, arch_dir is the root directory of all archives and
# arch_name is the DIRECTORY of the current archive--not the name of the
# current archive as you might expect.

def backup_archive(arch_dir, arch_name):
  if not os.path.isdir(arch_dir + arch_name):
    print("ERROR:  attempt to back up a non-existing directory")
    exit(-1)
  archive = arch_dir + arch_name
  backupdir = archive[:-1] + "_backups/"
  # delete previous backup directory
  if os.path.isdir(backupdir):
    command = ["rm","-rf",backupdir]
    run_and_report(command,"Unable to delete old backup directory" + backupdir)
  # copy archive to backup directory
  command = ["cp","-r",archive,backupdir]
  run_and_report(command,"Unable to back up archive")

def restore_archive(arch_dir, arch_name):
  archive = arch_dir + arch_name
  backupdir = archive[:-1] + "_backups/"
  forensicdir = archive[:-1] + "_forensics/"
  assert os.path.isdir(backupdir)

  # make copy of current state of archive directory, for debugging
  if os.path.isdir(archive):
    command = ["cp","-r",archive,forensicdir]
    run_and_report(command,"Unable to snapshot archive for debugging")

  # delete archive directory
  if os.path.isdir(archive):
    command = ["rm","-rf",archive]
    run_and_report(command,"Unable to delete old archive " + archive)

  # copy backup directory into archive directory
  command = ["cp","-r",backupdir,archive]
  run_and_report(command,"Unable to restore archive from backups")



##########################################################################
# maps

## map for plotting point estimates (tan land, white seas)
def makemap_for_summaries(proj,mapdata):
  # crs_lonlat = ccrs.PlateCarree()
  minlat,minlong,maxlat,maxlong,dim = mapdata
  m = plt.axes(projection=proj)
  m.set_extent([minlong,maxlong,minlat,maxlat], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  # gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
  gl = m.gridlines(crs=proj,xlocs=np.arange(-50,70,10),ylocs=np.arange(-50,70,10),draw_labels=True)
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

