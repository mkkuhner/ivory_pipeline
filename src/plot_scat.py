import sys
from mpl_toolkits.basemap import Basemap as bmap
import numpy as np
import matplotlib.pyplot as plt
import os
import math
import statistics

# constants

########################################################################
# functions
def pull_voronoi(vfile,gridsize):
  rawgrid = []
  for line in open(vfile,"r"):
    line = line.rstrip().split()
    rawrow = [float(x) for x in line]
    assert len(rawrow) == gridsize
    rawgrid.append(rawrow)
  assert len(rawgrid) == gridsize
  return rawgrid

def pull_scat(sfiles,gridsize,latmin,latmax,longmin,longmax):
  gridcounts = [[0 for x in xrange(gridsize)] for x in xrange(gridsize)]
  lats = []
  longs = []
  for file in sfiles:
    lines = open(file,"r").readlines()
    for line in lines[99:-1]:  # skip burning!
      line = line.rstrip().split()
      mylat = float(line[0])
      mylong = float(line[1])
      assert latmin <= mylat <= latmax
      assert longmin <= mylong <= longmax
      gridlat = int(math.floor(mylat) - latmin)
      gridlong = int(math.floor(mylong) - longmin)
      gridcounts[gridlat][gridlong] += 1
      lats.append(mylat)
      longs.append(mylong)
  medlat = statistics.median(lats)
  medlong = statistics.median(longs)
  return gridcounts,medlat,medlong

def get_maximum(vgrid):
  bestx = -99
  besty = -99
  bestval = -99.0
  for x in xrange(len(vgrid)):
    for y in xrange(len(vgrid[0])):
      if vgrid[x][y] > bestval:
        bestval = vgrid[x][y]
        bestx = x
        besty = y
  assert bestx != -99
  return [bestx,besty]

def makemap_for_summaries(latmin,latmax,longmin,longmax):
  m = bmap(projection='merc',epsg='4326',llcrnrlat=latmin,llcrnrlon=longmin,urcrnrlat=latmax,urcrnrlon=longmax)
  m.drawcoastlines(linewidth=0.4,color="black")
  m.drawmeridians(np.arange(-50.0,70.0,20.0),labels=[False,False,False,True],dashes=[2,2])
  #m.drawmapboundary(fill_color="lightblue")
  m.drawcountries(linewidth=0.4, linestyle="solid", color="blue")
  m.drawparallels(np.arange(-50.0,70.0,20.0),labels=[True,False,False,False],dashes=[2,2])
  return m

def makemap_for_heatmaps(latmin,latmax,longmin,longmax):
  m = bmap(projection='merc',epsg='4326',llcrnrlat=latmin,llcrnrlon=longmin,urcrnrlat=latmax,urcrnrlon=longmax)
  m.drawcoastlines(linewidth=0.4,color="white")
  m.drawmeridians(np.arange(-50.0,70.0,20.0),labels=[False,False,False,True],dashes=[2,2])
  #m.drawmapboundary(fill_color="lightblue")
  m.drawcountries(linewidth=0.4, linestyle="solid", color="lightblue")
  m.drawparallels(np.arange(-50.0,70.0,20.0),labels=[True,False,False,False],dashes=[2,2])
  return m

########################################################################
# main program
if len(sys.argv) != 2 and len(sys.argv) != 3:
  print("USAGE: python2 plot_voronoi_Africa.py prefix sid")
  print("Assumes that Voronoi individual elephant results are in prefix_reports/")
  print("and scat results are here, along with needed samplemaps")
  print("If no sid is given, plots everything in that directory")
  print("Note that this program uses 'basemap' and only runs in Python2")
  exit(-1)

# read Voronoi data

prefix = sys.argv[1]
reportdir = prefix + "_reports"

v_infiles = []
sids = []
if len(sys.argv) == 2:
  for root, dirs, files in os.walk(reportdir):
    for file in files:
      if file.endswith("_voronoi.txt"):
        v_infiles.append(reportdir + "/" + file)
        sid = file[0:-12]
        sids.append(sid)
else:
  sid = sys.argv[2]
  print("Analysis for sid",sid,"only")
  infilename = reportdir + "/" + sid + "_voronoi.txt"
  v_infiles.append(infilename)
  sids.append(sid)

# read corresponding Scat data
taglist = ["r","s","t","u","v","w","x","y","z"]
smap = {}
for line in open("samplemap.r","r"):
  if line.startswith("Accept"):  continue
  fileno,mysid = line.rstrip().split()
  if mysid in sids:
    smap[mysid] = fileno
  
s_infiles = []
for sid in sids:
  fileno = smap[sid]
  specfiles = []
  for tag in taglist:
    specfiles.append(fileno + tag)
  s_infiles.append(specfiles)
 
# read map info to align grid correctly
maplines = open(prefix+"_mapinfo","r").readlines()
nsgrid = int(maplines[2].rstrip().split()[-2])
ewgrid = int(maplines[3].rstrip().split()[-2])
assert nsgrid == ewgrid   # map must currently be square
gridsize = nsgrid
latmin, longmin = maplines[0].rstrip().split()[-2:]
latmin = int(latmin[:-1])  # remove comma
longmin = int(longmin)
latmax, longmax = maplines[1].rstrip().split()[-2:]
latmax = int(latmax[:-1])  # remove comma
longmax = int(longmax)
print("gridsize",gridsize)
print("latmin",latmin,"latmax",latmax)
print("longmin",longmin,"longmax",longmax)

figno = 1
longs = [x for x in range(longmin,longmax+1)]
lats = [x for x in range(latmin,latmax+1)]

best_vorx = []
best_vory = []
best_scatx = []
best_scaty = []
med_scatx = []
med_scaty = []

for sfiles, sid in zip(s_infiles,sids):
#  # voronoi data
#  plt.figure(figno)
#  figno += 1
#  vgrid = pull_voronoi(vfile,gridsize)
#
#  # get best point for summary graph
#  vorx,vory = get_maximum(vgrid)
#  best_vorx.append(vorx+latmin+0.5)
#  best_vory.append(vory+longmin+0.5)
#
#  m = makemap(latmin,latmax,longmin,longmax)
#  x,y = m(*np.meshgrid(longs,lats))
#  m.pcolormesh(x,y,vgrid,shading="flat",cmap=plt.cm.hot)
#  m.colorbar(location="right")
#
#  plt.title("Voronoi " + sid);
#  plt.savefig(reportdir + "/" + sid + "_voronoi.jpg")
#  #plt.show()
#  plt.close()

  # scat data
  plt.figure(figno) 
  figno += 1
  sgrid,medlat,medlong = pull_scat(sfiles,gridsize,latmin,latmax,longmin,longmax)
  m = makemap_for_heatmaps(latmin,latmax,longmin,longmax)

  # get best point for summary graph
  scatx,scaty = get_maximum(sgrid)
  best_scatx.append(scatx+latmin+0.5)
  best_scaty.append(scaty+longmin+0.5)
  med_scatx.append(medlat)
  med_scaty.append(medlong)

  x,y = m(*np.meshgrid(longs,lats))
  m.pcolormesh(longs,lats,sgrid,latlon=True,shading="flat",cmap=plt.cm.hot)
  m.colorbar(location="right")

  plt.title("Scat " + sid)
  plt.savefig(reportdir + "/" + sid + "_scat.jpg")
  #plt.show()
  plt.close()


# summary figures

# voronoi summary
#figno += 1
#plt.figure(figno)
#m = makemap_for_summaries(latmin,latmax,longmin,longmax)
#m.fillcontinents(color='tan')
#for vx,vy in zip(best_vorx,best_vory):
#  x,y = m(vx,vy)
#  m.plot(y,x,"r+")
#plt.title("Voronoi summary")
#plt.savefig(reportdir+"/voronoi_summary.jpg")

# scat summary by squares
figno += 1
plt.figure(figno)
m = makemap_for_summaries(latmin,latmax,longmin,longmax)
m.fillcontinents(color='tan')
for sx,sy in zip(best_scatx,best_scaty):
  x,y = m(sx,sy)
  m.plot(y,x,"r+")
plt.title("Scat summary:  most occupied grid square")
plt.savefig(reportdir+"/scat_summary_squares.jpg")

# scat summary by medians
figno += 1
plt.figure(figno)
m = makemap_for_summaries(latmin,latmax,longmin,longmax)
m.fillcontinents(color='tan')
for sx,sy in zip(med_scatx,med_scaty):
  x,y = m(sx,sy)
  m.plot(y,x,"r+")
plt.title("Scat summary:  median lat/long")
plt.savefig(reportdir+"/scat_summary_medians.jpg")
