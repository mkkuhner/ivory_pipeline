# set up for a VORONOI run, given a directory with SCAT runs

# replaces previous functionality of scat2voronoi.py as well
# as parts of filter_hybrids.py.

# relies on the ivory_paths.tsv file being in the root directory
# below the seizures.

# functions

def readivorypath(infile):
  ivorypaths = {}
  inlines = open(infile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

# main program

import sys, os, subprocess

if len(sys.argv) != 4:
  print("USAGE:  setupvoronoi.py PREFIX species ivory_paths.tsv")
  exit(-1)

prefix = sys.argv[1]
species = sys.argv[2]
scatdata = prefix + "_" + species + ".txt"
pathfile = sys.argv[3]

ivorypaths = readivorypath(pathfile)

ivorydir = ivorypaths["ivory_pipeline_dir"][0]
vor_dir, vor_exe = ivorypaths["voronoi_executable"]
vor_exe = vor_dir + vor_exe
map_dir, map_prefix = ivorypaths["map_prefix"]

masterfile = ivorydir + "aux/master_voronoi_runfile.sh"

if not os.path.isfile(scatdata):
  print("FAILURE:  could not find scat data",scatdata)
  exit(-1)

if not os.path.isfile(masterfile):
  print("FAILURE:  could not find master voronoi runfile",masterfile)
  exit(-1)

if not os.path.isfile(vor_exe):
  print("FAILURE:  could not find voronoi executable",vor_exe)
  exit(-1)

# parse SCAT input data and find out what individuals are wanted
sids = []
for line in open(scatdata,"r"):
  line = line.rstrip().split()
  sid = line[0]
  zone = line[1]
  if zone != "-1":  continue   # ignore reference elephants
  if sid not in sids:
    sids.append(sid)
  
# write a file of those individuals
samplefilename = prefix + "_names.txt"
outfile = open(samplefilename,"w")
for sid in sids:
  outfile.write(sid+"\n")
outfile.close()

# write a VORONOI run file (with -k option) -- note that samplefile
# replaces voronoiin.txt.
# also put other useful new options in VORONOI run file!

runline = open(masterfile,"r").readline()
runline = runline.replace("VORONOI",vor_exe)
mapname = map_dir + map_prefix + "_" + species + ".txt"
runline = runline.replace("MAPFILE",mapname)
runline = runline.replace("SAMPLEFILE",samplefilename)
runline = runline.replace("PREFIX",prefix)

outfilename = "voronoi_runfile_" + species + ".sh"
outfile = open(outfilename,"w")
outfile.write(runline)
outfile.close()

# copy map info from SCAT into directory
mapinfofile = prefix + "_mapinfo"
if not os.path.isfile(mapinfofile):
  rawmapinfo = "1/outputs/Output_mapinfo"
