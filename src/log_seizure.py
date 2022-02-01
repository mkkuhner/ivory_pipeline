# This program gathers information about which program versions, data files, etc.
# were used in running a particular seizure, and makes a log file accordingly.
# It is meant to be run in the root directory of all seizures.
# It will overwrite previous log files for the same seizure name.

import subprocess, os

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

### main program
import sys
if len(sys.argv) != 7:
  print("USAGE:  log_seizure.py prefix ivorydir datadir scatdir vordir pathsfile.tsv")
  exit(-1)

prefix = sys.argv[1]
seizuredir = os.path.abspath(prefix)
ivorydir = os.path.abspath(sys.argv[2])
datadir = os.path.abspath(sys.argv[3])
scatdir = os.path.abspath(sys.argv[4])
scatdir = stripfilename(scatdir)
vordir = os.path.abspath(sys.argv[5])
vordir = stripfilename(vordir)
pathsfile = sys.argv[6]

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
code = get_github_code(ivorydir)
outline = "Ivory Pipeline GitHub version: " + code + "\n"
outfile.write(outline)
outline = "Ivory pipeline directory: " + ivorydir + "\n\n"
outfile.write(outline)

code = get_github_code(scatdir)
outline = "SCAT GitHub version: " + code + "\n"
outfile.write(outline)
outline = "SCAT directory: " + scatdir + "\n\n"
outfile.write(outline)

code = get_github_code(vordir)
outline = "VORONOI GitHub version: " + code + "\n"
outfile.write(outline)
outline = "VORONOI directory: " + vordir + "\n\n"
outfile.write(outline)

# working directories
outline = "Reference data: " + datadir + "\n"
outfile.write(outline)

outline = "Pathsfile used: " + pathsfile + "\n"
outfile.write(outline)

outfile.close()
