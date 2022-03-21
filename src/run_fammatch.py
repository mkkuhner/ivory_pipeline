# run_fammatch.py

# Marshall input files, run fammatch R scripts, archive results

# inputs:
# sector specific genotype files of new elephants
# sector specific genotype files of old elephants
# sector specific reference files

# archive directory structure (N is sector number):
#   old_inputs/oldN.txt where N is sector number
#   reference/refN_fammatch.csv 
#   elephant_msat_database.tsv

# also uses but does not modify:
#   sector_metadata.tsv
# uses and modifies:
#   seizure_metadata

import os, sys, shutil

##########################################################################
# functions

import subprocess
from subprocess import Popen

def file_exists(filename):
  return os.path.isfile(filename)

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def run_and_report(command,errormsg):
  process = Popen(command)
  stdout, stderr = process.communicate()
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

def safecopy(fromfile,tofile):
  if not file_exists(tofile):
    command = ["cp",fromfile,tofile]
    run_and_report(command, "Unable to copy file " + fromfile)

# assumes that the file consists of 2 tab delimited columns, no header,
# first column = string, sector id
# second column = string, species name
def read_sector_metadata(metafilename):
  sector2species = {}
  for line in open(metafilename,"r"):
    pline = line.rstrip().split("\t")
    sector2species[pline[0]] = pline[1]
  return sector2species

def make_dir_if_needed(pathname):
  if not os.path.isdir(pathname):
    os.mkdir(pathname)
  return pathname

##########################################################################
# main program

from datetime import datetime

if len(sys.argv) != 3:
  print("USAGE:  run_fammatch.py prefix ivory_paths")
  exit(-1)

# set up directory names to be used throughout
# all end in "/"

prefix = sys.argv[1]
pathfile = sys.argv[2]
seizuredir = prefix + "/fammatch/"
pathdir = readivorypath(pathfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
archivedir, fam_db = pathdir["fammatch_archive_dir"]
metadir, metafile = pathdir["metadata_prefix"]
metafile = metadir + metafile + ".tsv"

if not os.path.isdir(archivedir):
  print("Cannot find fammatch archive:  did you forget to hook up the external HD?")
  print("Location tried was",archivedir)
  exit(-1)

old_inputs_dir = archivedir + "old_inputs/"
old_input_backup_dir = archivedir + "old_input_backups/"
make_dir_if_needed(old_inputs_dir)
old_ref_dir = archivedir + "reference/"
make_dir_if_needed(old_ref_dir)

# associate sectors with species
sectorfile = ivory_dir + "aux/sector_metadata.tsv"
sector2species = read_sector_metadata(sectorfile)
nsec = len(sector2species)

## BACKUPS
# back up "old" and "new" data files before modification
# we will restore from backups if things go badly
for sector in range(0,nsec):
  secname = str(sector)
  # old files back up to archive subdirectory
  olddataname = old_inputs_dir + "old" + secname + ".csv"
  if os.path.isfile(olddataname):
    oldbackupname = old_input_backup_dir + "old" + secname + ".csv_bak"
    shutil.copyfile(olddataname,oldbackupname)
  # new files back up to seizure fammatch directory
  newdataname = seizuredir + "new" + secname + ".csv"
  if os.path.isfile(newdataname):
    newbackupname = newdataname + "_bak"
    shutil.copyfile(newdataname,newbackupname)

# for each sector, assemble fammatch inputs and run fammatch if necessary
for sector in range(0,nsec):
  secname = str(sector)
  species = sector2species[secname]

  # determine if we need to run this sector (i.e. there are new data)
  newdataname = seizuredir + "new" + secname + ".csv"
  if not file_exists(newdataname):
    continue

  print("Running fammatch for sector",secname)

  ## REFERENCE

  # obtain reference data:  for safety we check that the reference
  # generated de novo is IDENTICAL to the archived one.  This protects
  # against merging data from different references.

  newrefname = seizuredir + "ref_" + secname + "_fammatch.csv"
  oldrefname = old_ref_dir + "ref_" + secname + "_fammatch.csv"

  # if old reference exists, compare with new; otherwise archive new
  if file_exists(oldrefname):
    command = ["diff",newrefname,oldrefname]
    run_and_report(command,"Discrepant reference data detected for sector " + secname)
  else:
    command = ["cp",newrefname,oldrefname]
    run_and_report(command,"Cannot copy reference file for sector " + secname)

  ## OLD AND NEW DATA

  # if there are no "old" data, borrow one from "new"
  olddataname = old_inputs_dir + "old" + secname + ".csv"
    
  if not file_exists(olddataname):   
    # read new data and check if more than 1 sample
    newdata = open(newdataname,"r").readlines()
    numsamples = len(newdata) - 1   # header

    # make old file and put 1 sample into it
    oldfile = open(olddataname,"w")
    for line in newdata[0:2]:
      oldfile.write(line)  # header and first sample
    oldfile.close()

    # rewrite new file in place with one less sample
    newfile = open(newdataname,"w")
    newfile.write(newdata[0])    # header
    for line in newdata[2:]:     # skip first sample
      newfile.write(line)
    newfile.close()

    # if there aren't any new samples left, we cannot run fammatch; bail out
    # new data is already saved in this case (by creating olddatafile)
    if numsamples == 1:
      indicatorfile = open(seizuredir + "ONLY_ONE_SAMPLE_" + secname,"w")
      indicatorfile.write("Insuffcient samples:  No matching run for sector" + secname + "\n")
      indicatorfile.close()
      continue

  ## FAMMATCH RUNS

  # make directory for runs
  rundir = seizuredir + "sub" + secname + "/"
  make_dir_if_needed(rundir)
  safecopy(ivory_dir + "src/calculate_LRs.R", rundir + "calculate_LRs.R")
  safecopy(ivory_dir + "src/LR_functions.R", rundir + "LR_functions.R")

  # get absolute paths to give to R scripts (safest)
  r_oldrefname = os.path.abspath(oldrefname)
  r_olddataname = os.path.abspath(olddataname)
  r_newdataname = os.path.abspath(newdataname)

  # run fammatch; restore backups on failure
  try:
    olddir = os.getcwd()
    os.chdir(rundir)  # the Rscripts have to be run from within their resident directory
    command = ["Rscript","calculate_LRs.R",species,r_oldrefname,r_olddataname,r_newdataname]
    print("Calculating familial matches for sector ",sector)
    print(" ".join(command))
    run_and_report(command,"Unable to execute calculate_LRs.R")

    # translate results to database format
    progfile = ivory_dir + "src/rout2db.py"
    # we are in rundir, so use local filename only
    rfile = "obsLRs." + species + ".txt"
    command = ["python3",progfile,rfile,metafile,secname]
    run_and_report(command,"Unable to execute rout2db.py")
    # result will be in file with "_full" before its extension
    os.chdir(olddir)

    # archive results in database
    print("Archiving results for ",secname)
    progfile = ivory_dir + "src/fammatch_database.py" 
    infile = rundir + "obsLRs." + species + "_full.tsv"
    dbfile = archivedir + fam_db
    if not file_exists(dbfile):
      # create new archive file
      print("Creating new archive file",dbfile)
      command = ["python3",progfile,dbfile,"create",infile]
    else:
      # add to existing archive file
      print("Adding to existing archive file",dbfile)
      command = ["python3",progfile,dbfile,"add",infile]
    run_and_report(command,"Could not add new results to fammatch database" + dbfile)
  
    os.chdir(olddir)

    # archive input files
    # at this point olddata file and newdata file will both exist
    # we open both and append everything but header in newdata onto end of olddata
    append_old = open(olddataname,"a")
    newdata = open(newdataname,"r").readlines()
    for line in newdata[1:]:
      append_old.write(line)
    append_old.close()
  except:
    # restore from backups, something has gone wrong
    for sector in range(0,nsec):
      secname = str(sector)
      # old data files
      olddataname = old_inputs_dir + "old" + secname + ".csv"
      oldbackupname = old_input_backup_dir + "old" + secname + ".csv_bak"
      if os.path.isfile(oldbackupname):
        shutil.copyfile(oldbackupname,olddataname)
      # new data files
      newdataname = seizuredir + "new" + secname + ".csv"
      newbackupname = newdataname + "_bak"
      if os.path.isfile(newbackupname):
        shutil.copyfile(newbackupname,newdataname)
    exit(-1)
