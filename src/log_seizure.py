# This program gathers information about which program versions, data files, etc.
# were used in running a particular seizure, and makes a log file accordingly.
# It is meant to be run in the root directory of all seizures.
# It will overwrite previous log files for the same seizure name.

# Modified by Mary 4/20/22 to actually use the ivory_paths file!

import subprocess, os

#######################################################################################3
### functions
def get_github_code(mydir):
  currentdir = os.getcwd()
  os.chdir(mydir)
  results = subprocess.check_output(["git", "log", "--oneline"])
  # results is a BYTE STRING, convert to regular string
  results = results.decode("utf-8")
  results = results.split()
  return(results[0])
  os.chdir(currentdir)

def stripfilename(mypath):
  parts = mypath.split("/")
  newpath = "/".join(parts[:-1])
  return newpath

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths


#######################################################################################3
### main program
import sys
if len(sys.argv) != 3:
  print("USAGE:  log_seizure.py prefix pathsfile.tsv")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]
seizuredir = os.path.abspath(prefix)

pathinfo = readivorypath(pathsfile)
ivory_dir = pathinfo["ivory_pipeline_dir"]
scat_dir, scat_exe = pathdir["scat_executable"]
vor_dir, vor_exe = pathdir["voronoi_executable"]
reference_path, reference_prefix = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
seizure_data_dir = pathdir["seizure_data_dir"][0]

outfile = open(seizuredir + "/" + prefix + "_logfile.txt","w")

# date of run
import datetime
current_time = datetime.datetime.now()
outline = "Run date: " + str(current_time.month) + "/" + str(current_time.day) + "/" + str(current_time.year) 
minutes = str(current_time.minute)
if len(minutes) == 1:  minutes = "0" + minutes
outline += " " + str(current_time.hour) + ":" + minutes + "\n\n"
outfile.write(outline)

# versions
code = get_github_code(ivory_dir)
outline = "Ivory Pipeline GitHub version: " + code + "\n"
outfile.write(outline)
outline = "Ivory pipeline directory: " + ivory_dir + "\n\n"
outfile.write(outline)

code = get_github_code(scat_dir)
outline = "SCAT GitHub version: " + code + "\n"
outfile.write(outline)
outline = "SCAT executable: " + scat_dir + scat_exe + "\n\n"
outfile.write(outline)

code = get_github_code(vor_dir)
outline = "VORONOI GitHub version: " + code + "\n"
outfile.write(outline)
outline = "VORONOI executable: " + vor_dir + vor_exe "\n\n"
outfile.write(outline)

# working directories
outline = "Reference data: " + reference_path + reference_prefix + "\n"
outfile.write(outline)

outline = "Pathsfile used: " + pathsfile + "\n"
outfile.write(outline)

outfile.close()
