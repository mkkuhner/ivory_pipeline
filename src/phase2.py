# takes a seizure which has been run through SCAT, runs
# VORONOI, and prepares reports and images
# meant to be run in the parent directory of all seizures

import sys
import os
import subprocess
from subprocess import Popen, PIPE


############################################################################
## functions

# assumes a file "ivory_paths.tsv" exists in the same directory as the 
# calling function

def readivorypath():
  ivorypaths = {}
  inlines = open("ivory_paths.tsv","r").readlines()
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

if len(sys.argv) != 2:
  print("USAGE:  python3 phase2.py PREFIX")
  exit(-1)

prefix = sys.argv[1]
seizuredir = prefix + "/"

# read ivory_paths.tsv file
# set up needed variables
pathdir = readivorypath()
ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_exec = pathdir["scat_executable"][0]
reference_path, reference_prefix = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
seizure_data_dir = pathdir["seizure_data_dir"][0]
voronoi_exec = pathdir["voronoi_executable"][0]

os.chdir(seizuredir)
specieslist = ["forest","savannah"]

# if nforest/nsavannah exists:
#   run voronoi
#   run prep_reports
#   run plot_scat_vor

for species in specieslist:
  dirname = "n" + species
  if os.path.isdir(dirname):
    os.chdir(dirname)
    setuppath = ivory_dir + "src/setupvoronoi.py"
    command = ["python3",setuppath,prefix,species]
    run_and_report(command,"Failure in setupvoronoi.py")

    print("About to run VORONOI:  be patient with this step")
    command = ["/bin/bash","voronoi_runfile_" + species + ".sh"]
    run_and_report(command,"Could not run VORONOI")

    reportdir = prefix + "_reports"
    if not os.path.isdir(reportdir):
      command = ["mkdir",reportdir]
      run_and_report(command,"Could not create directory" + reportdir)

    plotname = ivory_dir + "src/plot_scat_vor.py"
    command = ["python3",plotname,prefix]
    run_and_report(command,"Failure in" + plotname)
    
    print("Completed",species,"run")
    os.chdir("..")

# print confirmation message and exit
print("VORONOI runs and reports complete for seizure",prefix)
