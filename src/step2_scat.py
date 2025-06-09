# step2_scat.py
# This program sets up the needed files and directories to run SCAT
# for location (not SCAT for sectors) on a seizure.  It requires 
# step1_fammatch.py to have been run previously, as that program
# determines species and culls hybrids.

# It does not actually run SCAT as you may wish to port the files to the
# cluster, or run them in windows where you can watch them.

# Run this in the root directory of all seizures

import sys, os
import ivory_lib as iv

###########################################################################
# main program

if len(sys.argv) != 4:
  print("USAGE:  python3 step2_scat.py PREFIX laptop/cluster pathsfile.tsv")
  print("Note that this program is meant to be run on your laptop:")
  print("setting 'cluster' makes SCAT files that can be ported to the cluster")
  print("and run there")
  exit(-1)

prefix = sys.argv[1]
runtype = sys.argv[2]
if runtype != "laptop" and runtype != "cluster":
  print("Illegal run type ",runtype," (must be laptop or cluster)")
  exit(-1)
pathsfile = os.path.abspath(sys.argv[3])
specieslist = ["forest","savannah"]

# read ivory_paths.tsv file
# set up needed variables
pathdir = iv.readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
scat_dir, scat_exec = pathdir["scat_executable"]
reference_path, reference_prefix = pathdir["reference_prefix"]
zones_path, zones_prefix = pathdir["zones_prefix"]
map_path, map_prefix = pathdir["map_prefix"]
seizure_data_dir = pathdir["seizure_data_dir"][0]

# test if seizure directory exists 
seizure_dir = prefix + "/"
if not os.path.isdir(seizure_dir):
  print("Seizure directory",seizure_dir,"does not exist")
  print("Do you need to run step1_fammatch.py first?")
  exit(-1)
os.chdir(seizure_dir)

# test if some species directory(ies) exist
foundspecies = False
for spec in specieslist:
  if os.path.isdir("n" + spec):
    foundspecies = True
    break
if not foundspecies:
  print("FAILURE: No species specific directories within",seizure_dir,"exist.")
  print("Looked for species:",end="")
  for spec in specieslist:
    print(" " + spec,end="")
  print("\n")
  exit(-1)
 
# we assume that data have been obtained, validated, filtered, and
# assigned to species by upstream code step1_fammatch.py

# Set up the scat runs for each species present in data
for species in specieslist:
  dirname = "n" + species 
  if not os.path.isdir(dirname):  continue  # species not present

  datafile = prefix+"_"+species+".txt"
  command = ["cp",datafile,dirname]
  iv.run_and_report(command,"Could not access " + datafile)

  runfile = "runfile_"+species+".sh"
  if runtype == "cluster":
    runfile = "cluster_" + runfile
  command = ["cp",runfile,dirname]
  iv.run_and_report(command,"Could not access " + runfile)

  scat_path = scat_dir + scat_exec
  command = ["cp",scat_path,dirname]
  iv.run_and_report(command,"Could not access scat executable " + scat_path)

  # set up the prefix_mapinfo files in the species directory
  mapinfofile = dirname + "/" + prefix + "_mapinfo"
  mapfile = map_path + map_prefix + "_" + species + ".txt"
  iv.write_mapinfo_from_map(mapfile, mapinfofile)

  # run setupscatruns.py (or cluster variant)
  if runtype == "laptop":
    progname = ivory_dir + "/src/setupscatruns.py"
    command = ["python3",progname,dirname,runfile,"1001"]
    iv.run_and_report(command,"Failure in setupscatruns")
  else:
    progname = ivory_dir + "/src/cluster_setupscatruns.py"
    command = ["python3",progname,prefix,dirname,runfile,"1001"]
    iv.run_and_report(command,"Failure in cluster_setupscatruns")
  print(dirname,"created")

# print confirmation message and exit
print("SCAT is now ready to run")
