# take a seizure from raw file to being ready to run SCAT
# does not actually do scat runs
# This should be run in the parent directory of all seizures

# prefer canned reference rather than the one computed in this cycle:
# this provides coherence over multiple seizures.  Only make reference
# if you don't have a canned one, and then can it!

import sys
import os
import subprocess
from subprocess import Popen, PIPE


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
    print("FAILURE: " + errormsg)
    exit(-1)


############################################################################
## main program

if len(sys.argv) != 5:
  print("USAGE:  python3 phase1.py PREFIX laptop/cluster new/canned pathsfile.tsv")
  print("new/canned refers to whether species-specific reference files")
  print("need to be made (new) or already exist (canned)")
  exit(-1)

prefix = sys.argv[1]
runtype = sys.argv[2]
if runtype != "laptop" and runtype != "cluster":
  print("Illegal run type ",runtype," (must be laptop or cluster)")
  exit(-1)
input_canned = sys.argv[3]
if input_canned != "new" and input_canned != "canned":
  print("Reference flag must be new or canned")
  exit(-1)
if input_canned == "new":  canned = False
else:  canned = True
pathsfile = os.path.abspath(sys.argv[4])


# make the seizure directory if it doesn't already exist
if os.path.isdir(prefix):
  print("FAILURE:  The seizure directory ",prefix,"already exists")
  print("Check whether this seizure name is a duplicate")
  print("If you want to replace all previous results, delete or move away")
  print("the previous seizure directory before proceeding.")
  exit(-1)
else:
  command = "mkdir " + prefix
  os.system(command)
seizuredir = prefix + "/"

# read ivory_paths.tsv file
# set up needed variables
pathdir = readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_dir, scat_exec = pathdir["scat_executable"]
reference_path, reference_prefix = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
seizure_data_dir = pathdir["seizure_data_dir"][0]

specieslist = ["forest","savannah"]


# copy raw data into 
rawdata = seizure_data_dir + prefix + "_raw.tsv"
command = ["cp", rawdata, seizuredir]
run_and_report(command,"Could not locate raw data file " + rawdata)

# log_seizure.py
# this program creates a logfile recording run parameters
command = ["python3", ivory_dir+"src/log_seizure.py",prefix,pathsfile]
run_and_report(command,"Failed to log the run")

# cd to newly created directory
os.chdir(prefix)

# run verifymsat
command = ["python3",ivory_dir + "src/verifymsat.py", "16"] 
command.append(reference_path + reference_prefix+"_raw.csv")
command.append(prefix + "_raw.tsv")
run_and_report(command,"Microsat validation failed")

# run detect_duplicates
command = ["python3",ivory_dir + "src/detect_duplicates.py",prefix+"_raw.tsv"]
run_and_report(command,"Duplicate samples detected")

# run prep_scat_data
command = ["python3",ivory_dir + "src/prep_scat_data.py",prefix]
run_and_report(command,"Failure in prep_scat_data.py")
print("Data validated and prepared")

# marshall files for ebhybrids
command = ["cp",ivory_dir + "aux/ebscript_template.R","."]
run_and_report(command,"Failure to find ebscript template")

command = ["cp",ivory_dir + "src/inferencefunctions.R","."]
run_and_report(command,"Failure to find EBhybrids source code")

command = ["cp",ivory_dir + "src/calcfreqs.R","."]
run_and_report(command,"Failure to find EBhybrids source code")

command = ["cp",ivory_dir + "src/likelihoodfunctionsandem.R","."]
run_and_report(command,"Failure to find EBhybrids source code")

# run make_eb_input
command = ["python3",ivory_dir + "src/make_eb_input.py"]
command.append(reference_path + reference_prefix + "_known_structure.txt_f")
command.append(reference_path + reference_prefix + "_known.txt")
command.append(prefix)
command.append(ivory_dir + "aux/dropoutrates_savannahfirst.txt")
run_and_report(command,"Failure to make EBhybrids input files")

# run ebhybrids 
command = ["Rscript","ebscript.R"]
run_and_report(command,"Failure in EBhybrids")
print("EBhybrids run completed")

# generate report on hybrids
hybrid_reportfile = prefix + "_hybout.txt"
ebhyrbid_output = prefix + "_hybt.txt"
hybrid_cutoff = 0.50
command = ["rm","-rf",hybrid_reportfile]
run_and_report(command,"Could not delete previous hybrid report")
command = ["python3",ivory_dir + "src/makehybridreport.py",
  prefix,str(hybrid_cutoff)]
print(command)
run_and_report(command,"Could not generate hybrid report")

# prep files for filter_hybrids
for species in specieslist:
  mapfile = map_path + map_prefix + "_" + species + ".txt"
  command = ["cp",mapfile,"."]
  run_and_report(command,"Could not copy in map file" + mapfile)

  zonesfile = zones_path + zones_prefix + "_" + species + ".txt" 
  command = ["cp",zonesfile,"."]
  run_and_report(command,"Could not copy in zones file" + zonesfile)

command = ["cp",ivory_dir + "aux/master_scat_runfile.sh","."]
run_and_report(command,"Could not copy in master scat runfile")

# run filter_hybrids

command = ["python3",ivory_dir + "src/filter_hybrids.py"]
command.append(prefix)
command.append(pathsfile)
if runtype == "laptop":
  command.append("F")
else:
  command.append("T")
if canned:
  command.append("T")
else:
  command.append("F")
run_and_report(command,"Could not filter hybrids")

# as needed:
species_done = []
for species in specieslist:
  if os.path.isfile("runfile_" + species + ".sh"):
    # set up species specific directory
    dirname = "n" + species
    if not os.path.isdir(dirname):
      command = ["mkdir",dirname]
      run_and_report(command,"Could not create " + dirname)
    else:
      print("FAILURE: ",dirname," directory already exists")
      exit(-1)

    datafile = prefix+"_"+species+".txt"
    command = ["cp",datafile,dirname]
    run_and_report(command,"Could not access " + datafile)

    runfile = "runfile_"+species+".sh"
    command = ["cp",runfile,dirname]
    run_and_report(command,"Could not access " + runfile)

    scat_path = scat_dir + scat_exec
    command = ["cp",scat_path,dirname]
    run_and_report(command,"Could not access scat executable " + scat_path)

    # run setupscatruns.py (or cluster variant)
    if runtype == "laptop":
      progname = ivory_dir + "/src/setupscatruns.py"
      command = ["python3",progname,dirname,runfile,"1001"]
      run_and_report(command,"Failure in setupscatruns")
    else:
      progname = ivory_dir + "/src/cluster_setupscatruns.py"
      command = ["python3",progname,prefix,dirname,runfile,"1001"]
      run_and_report(command,"Failure in cluster_setupscatruns")
    print(dirname,"created")
    species_done.append(species)

# print confirmation message and exit
print("SCAT is now ready to run")
