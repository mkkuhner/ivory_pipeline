# This program takes a Structure result file and two zonefiles (forest and savannah)
# and places the locations on the map of Africa color-coded by majority population.
# It is meant to work with K values from 2 to 6.  The input K value is used to label
# the output file and also to parse the Structure result file.

# For comparison purposes the program also makes a picture of the populations
# color coded by current forest/savannah divisions, and another coded by sector.

import sys
if len(sys.argv) != 5:
  print("USAGE:  python3 plot_structure.py K structfile zone1 zone2")
  exit(-1)

k = int(sys.argv[1])
if not (1 < k < 7):
  print("K must be between 2 and 6 but is",k)
  exit(-1)

structfile = sys.argv[2]
zonefiles = [sys.argv[3],sys.argv[4]]

# make dictionary of zone number to lat/long
zones = {}
fzones = {}
szones = {}
for zonefile in zonefiles:
  if "forest" in zonefile:  species = "forest"
  else:  species = "savannah"
  for line in open(zonefile,"r"):
    line = line.rstrip().split()
    zonenum = line[1]
    latlong = [float(line[3]),float(line[4])]
    zones[zonenum] = latlong
    if species == "forest":
      fzones[zonenum] = latlong
    else:
      szones[zonenum] = latlong

data = {}
foundit = False
for line in open(structfile,"r"):
  line = line.strip().split()
  if len(line) == 0:  continue   # blank lines
  # at beginning?
  if line[0] == "0:":
    foundit = True
  # at end?
  if foundit and "-" in line[0]:
    break
  if foundit:
    assert len(line) == k+2  # k populations, plus pop id, plus number individuals
    popid = line[0][:-1]
    numind = line[-1]
    props = [float(line[x]) for x in range(1,k+1)]
    data[popid] = props

import ivory_lib as iv
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

crs_lonlat = ccrs.PlateCarree()

# get min and max lat and long
lats = [myzone[0] for myzone in zones.values()]
longs = [myzone[1] for myzone in zones.values()]
minlat = min(lats) - 5
maxlat = max(lats) + 5
minlong = min(longs) - 5
maxlong = max(longs) + 5
dim = -99
mapdata = [minlat,minlong,maxlat,maxlong,dim]

colors = ["r","g","b","y","c"]
ambigcolor = "k"

m = iv.makemap_for_summaries(crs_lonlat,mapdata)

lats = []
longs = []
for pop, probs in data.items():
  maxprob = max(probs)
  if maxprob > 0.66:
    bestpop = probs.index(maxprob)
    mycolor = colors[bestpop]
  else:
    mycolor = ambigcolor
  latlong = zones[pop]
  lat = latlong[0]
  long = latlong[1]
  plt.plot(long,lat,transform=crs_lonlat,marker="o",markerfacecolor=mycolor,markersize=10,markeredgecolor=mycolor)

plt.savefig("plot" + str(k) + ".pdf")
plt.show()

  
