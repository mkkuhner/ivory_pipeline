import sys
#from mpl_toolkits.basemap import Basemap as bmap
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
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
  gridcounts = [[0 for x in range(0,gridsize)] for x in range(0,gridsize)]
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
  for x in range(0,len(vgrid)):
    for y in range(0,len(vgrid[0])):
      if vgrid[x][y] > bestval:
        bestval = vgrid[x][y]
        bestx = x
        besty = y
  assert bestx != -99
  return [bestx,besty]

def makemap_for_summaries(proj,latmin,latmax,longmin,longmax):
  m = plt.axes(projection=proj)
  m.set_extent([longmin,longmax,latmin,latmax], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="black")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,20),ylocs=np.arange(-50,70,20),draw_labels=True)
  gl.top_labels = None 
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="blue")
  m.add_feature(cfeature.LAND, color="tan")
  return m

def makemap_for_heatmaps(proj,latmin,latmax,longmin,longmax):
  m = plt.axes(projection=proj)
  m.set_extent([longmin,longmax,latmin,latmax], crs=proj)
  m.coastlines(resolution="50m", linewidth=0.4, color="white")
  gl = m.gridlines(crs=crs_lonlat,xlocs=np.arange(-50,70,20),ylocs=np.arange(-50,70,20),draw_labels=True, linestyle="--")
  gl.top_labels = None 
  gl.xlines = False
  gl.ylines = False
  m.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle="solid", color="white")
  m.add_feature(cfeature.LAND, color="tan")
  return m

#def makemap_for_heatmaps(latmin,latmax,longmin,longmax):
#  m = bmap(projection='merc',epsg='4326',llcrnrlat=latmin,llcrnrlon=longmin,urcrnrlat=latmax,urcrnrlon=longmax)
#  m.drawcoastlines(linewidth=0.4,color="white")
#  m.drawmeridians(np.arange(-50.0,70.0,20.0),labels=[False,False,False,True],dashes=[2,2])
#  #m.drawmapboundary(fill_color="lightblue")
#  m.drawcountries(linewidth=0.4, linestyle="solid", color="lightblue")
#  m.drawparallels(np.arange(-50.0,70.0,20.0),labels=[True,False,False,False],dashes=[2,2])
  return m

########################################################################
# main program
if len(sys.argv) != 2 and len(sys.argv) != 3:
  print("USAGE:  python2 plot_voronoi_Africa.py prefix sid")
  print("Assumes that Voronoi individual elephant results are in prefix_reports/")
  print("and scat results are here, along with needed samplemaps")
  print("If no sid is given, plots everything in that directory")
  print("Note that this program uses 'basemap' and only runs in python2")
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

pointfile = open(reportdir + "/" + prefix + "_point_estimates.tsv","w")
hdr = "SID\tVoronoi\tSCAT_median\tSCAT_bestsquare\n"
pointfile.write(hdr)

crs_lonlat = ccrs.PlateCarree()

for vfile, sfiles, sid in zip(v_infiles,s_infiles,sids):
  pointline = sid
  # voronoi data
  plt.figure(figno)
  figno += 1
  vgrid = pull_voronoi(vfile,gridsize)

  # get best point for summary graph
  vorx,vory = get_maximum(vgrid)
  best_vorx.append(vorx+latmin+0.5)
  best_vory.append(vory+longmin+0.5)
  pointline += "\t" + str(vorx+latmin+0.5) + "," + str(vory+longmin+0.5) 

  m = makemap_for_heatmaps(crs_lonlat,latmin,latmax,longmin,longmax)
#  x,y = m(*np.meshgrid(longs,lats))
  x,y = np.meshgrid(longs,lats)
  m.pcolormesh(x,y,vgrid,shading="flat",cmap=plt.cm.hot)
  sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
  sm._A = []
  cb = plt.colorbar(sm)
  cb.set_ticks([])

  plt.title("Voronoi " + sid);
  plt.savefig(reportdir + "/" + sid + "_voronoi.png")
  #plt.show()
  plt.close()

  # scat data
  plt.figure(figno) 
  figno += 1
  sgrid,medlat,medlong = pull_scat(sfiles,gridsize,latmin,latmax,longmin,longmax)
  m = makemap_for_heatmaps(crs_lonlat,latmin,latmax,longmin,longmax)

  # get best point for summary graph
  scatx,scaty = get_maximum(sgrid)
  best_scatx.append(scatx+latmin+0.5)
  best_scaty.append(scaty+longmin+0.5)
  med_scatx.append(medlat)
  med_scaty.append(medlong)
  pointline += "\t" + str(medlat) + "," + str(medlong) 
  pointline += "\t" + str(scatx+latmin+0.5) + "," + str(scaty+longmin+0.5) 
  pointline += "\n"
  pointfile.write(pointline)

#  x,y = m(*np.meshgrid(longs,lats))
  x,y = np.meshgrid(longs,lats)
#  m.pcolormesh(longs,lats,sgrid,latlon=True,shading="flat",cmap=plt.cm.hot)
  m.pcolormesh(longs,lats,sgrid,shading="flat",cmap=plt.cm.hot)
  sm = plt.cm.ScalarMappable(cmap=plt.cm.hot)
  sm._A = []
  cb = plt.colorbar(sm)
  cb.set_ticks([])

  plt.title("Scat " + sid)
  plt.savefig(reportdir + "/" + sid + "_scat.png")
  #plt.show()
  plt.close()

pointfile.close()

# summary figures

# voronoi summary
figno += 1
plt.figure(figno)
m = makemap_for_summaries(crs_lonlat,latmin,latmax,longmin,longmax)
#m.fillcontinents(color='tan')
#for vx,vy in zip(best_vorx,best_vory):
#  x,y = m(vx,vy)
for x,y in zip(best_vorx,best_vory):
  m.plot(y,x,"r+",transform=crs_lonlat)
plt.title("Voronoi summary")
plt.savefig(reportdir+"/voronoi_summary.png")

# scat summary by squares
figno += 1
plt.figure(figno)
m = makemap_for_summaries(crs_lonlat,latmin,latmax,longmin,longmax)
#m.fillcontinents(color='tan')
#for sx,sy in zip(best_scatx,best_scaty):
#  x,y = m(sx,sy)
for x,y in zip(best_scatx,best_scaty):
  m.plot(y,x,"r+",transform=crs_lonlat)
plt.title("Scat summary:  most occupied grid square")
plt.savefig(reportdir+"/scat_summary_squares.png")

# scat summary by medians
figno += 1
plt.figure(figno)
m = makemap_for_summaries(crs_lonlat,latmin,latmax,longmin,longmax)
#m.fillcontinents(color='tan')
#for sx,sy in zip(med_scatx,med_scaty):
#  x,y = m(sx,sy)
for x,y in zip(med_scatx,med_scaty):
  m.plot(y,x,"r+",transform=crs_lonlat)
plt.title("Scat summary:  median lat/long")
plt.savefig(reportdir+"/scat_summary_medians.png")

