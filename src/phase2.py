# takes a seizure which has been run through SCAT, runs
# VORONOI, and prepares reports and images
# meant to be run in the parent directory of all seizures

# If there are fewer than minimum_samples in this seizure/species
# combination, VORONOI will not be run; it is unreliable in such
# cases.

import sys
import os
import subprocess
from subprocess import Popen, PIPE

# minimum number of samples needed to run VORONOI
minimum_samples = 10


############################################################################
## functions

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
    print("\nFAILURE: " + errormsg + "\n")
    exit(-1)


############################################################################
## main program

if len(sys.argv) != 3:
  print("USAGE:  python3 phase2.py PREFIX pathsfile.tsv")
  print("This should be run in the parent directory of all seizures")
  print("and the pathsfile must be the same as used in phase1.py and phase3.py")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]
pathsfile = os.path.abspath(pathsfile)
seizuredir = prefix + "/"

# read ivory_paths.tsv file
# set up needed variables
pathdir = readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]

os.chdir(seizuredir)
specieslist = ["forest","savannah"]

# if nforest/nsavannah exists:
#   run voronoi
#   run prep_reports
#   run plot_results (replaces older plot_scat_vor)

for species in specieslist:
  dirname = "n" + species
  if os.path.isdir(dirname):
    os.chdir(dirname)
    
    setuppath = ivory_dir + "src/setupvoronoi.py"
    command = ["python3",setuppath,prefix,species,pathsfile]
    run_and_report(command,"Failure in setupvoronoi.py")

    # count the samples, bail if fewer than minimum_samples
    namefile = prefix + "_names.txt"
    namelines = open(namefile,"r").readlines()
    if len(namelines) >=minimum_samples:
      print("About to run VORONOI:  be patient with this step")
      command = ["/bin/bash","voronoi_runfile_" + species + ".sh"]
      run_and_report(command,"Could not run VORONOI")
    else:
      print("Only ",len(namelines),"samples available for",species,"so VORONOI not run")

    reportdir = prefix + "_reports"
    if not os.path.isdir(reportdir):
      command = ["mkdir",reportdir]
      run_and_report(command,"Could not create directory" + reportdir)

    print("Completed",species,"run")
    os.chdir("..")

# after both species are run, back up to main directory to run plot_results.py
os.chdir("..")
plotname = ivory_dir + "src/plot_results.py"
command = ["python3",plotname,prefix,pathsfile]
run_and_report(command,"Failure in" + plotname)
    
# print confirmation message and exit
print("VORONOI runs and reports complete for seizure",prefix)
