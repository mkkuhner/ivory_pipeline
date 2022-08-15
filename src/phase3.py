# Perform incremental familial matching on a new seizure
# This is meant to be run in the parent directory of all seizures.
# It does the fammatch runs one at a time, which is inefficient 
# but safe.

# Post-processing is done by phase4.py, once for all current seizures.

# If this program fails it is supposed to restore from backup, leaving
# the state of the database unchanged.

import sys
import os
import subprocess
from subprocess import Popen, PIPE

###################################################################
# functions

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
    print("exit code was",exit_code)
    raise RuntimeError(errormsg)

# "cp" onto an existing file may fail, even if "-f" is used, 
# depending on user enviroment.  So we remove the
# target file before attempting copy.

def copy_if_src_present(src,tgt):
  # do nothing if src not present
  if not os.path.isfile(src):  return

  # if tgt exists, delete it
  if os.path.isfile(tgt):
    command = ["rm","-rf",tgt]
    run_and_report(command,"File " + tgt + " cannot be removed")

  # copy
  command = ["cp",src,tgt]
  run_and_report(command, "Unable to copy file " + src + " to " + tgt)

def check_seizure_present(sfile,seizurename):
  oldseizures = open(sfile,"r").readlines()
  for line in oldseizures:
    line = line.rstrip().split()
    if line[0] == seizurename:
      return (True, oldseizures)
  return (False, oldseizures)

def backup_archive(arch_dir):
  backupdir = arch_dir + "../archive_backups/"
  # delete previous backup directory
  if os.path.isdir(backupdir):
    command = ["rm","-rf",backupdir]
    run_and_report(command,"Unable to delete old backup directory" + backupdir)
  # copy archive to backup directory
  command = ["cp","-r",arch_dir,backupdir]
  run_and_report(command,"Unable to back up archive")

def restore_archive(arch_dir):
  backupdir = arch_dir + "../archive_backups/"

  # make copy of current state of archive directory, for debugging
  forensicdir = arch_dir + "../forensics/"
  if os.path.isdir(arch_dir):
    command = ["cp","-r",arch_dir,forensicdir]
    run_and_report(command,"Unable to snapshot archive for debugging")

  # delete archive directory
  if os.path.isdir(arch_dir):
    command = ["rm","-rf",arch_dir]
    run_and_report(command,"Unable to restore from backup " + backupdir)

  # copy backup directory into archive directory
  command = ["cp","-r",backupdir,arch_dir]
  run_and_report(command,"Unable to restore archive from backups")

###################################################################
# main program

if len(sys.argv) != 3:
  print("USAGE:  python phase3.py PREFIX pathsfile.tsv")
  print("This should be run in the parent directory of all seizures")
  print("and the pathsfile must be the same as used in phase1.py and phase2.py")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]

# NB:  We do NOT check seizure_modifications in this program.
# This means we will not omit or merge/rename any seizures.
# This allows us to have fammatch results for them in case they are
# of interest, and also allows us to change our minds about merge or
# reject without having to rerun everything.

# The seizure_modifications are implemented in phase4.py instead, to keep
# unwanted seizures out of the final networks.

# save what directory we were run in (should be root directory of all seizures)
startdir = os.getcwd() + "/"

# read paths file
pathdir = readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
zones_path, zones_prefix = pathdir["zones_prefix"]
scat_dir, scat_exe = pathdir["scat_executable"]
scat_exe = scat_dir + scat_exe
arch_dir = pathdir["fammatch_archive_dir"][0]
meta_path, meta_prefix = pathdir["metadata_prefix"]
mod_path, mod_prefix = pathdir["seizure_modifications_prefix"]
ref_path, ref_prefix = pathdir["reference_prefix"]

# check if the archive actually exists; if not, create it
if not os.path.isdir(arch_dir):
  command = ["mkdir",arch_dir]
  run_and_report(command, "Unable to create archive")

# check if this seizure has already been run.  We will not run it again
# unless the user first cleans it out.

seizurelist = arch_dir + "seizurelist.tsv"
oldseizures = []
if os.path.isfile(seizurelist):
  is_present, oldseizures = check_seizure_present(seizurelist, prefix)
  if is_present:
    print("Seizure",prefix,"is already present in the archive")
    print("If you need to rerun it, call remove_seizure_from_fammatch.py first")
    exit(-1)

# Back up the entire archive.  This will be used to recover if something
# goes wrong at any point in this program.

try:
  backup_archive(arch_dir)
except RuntimeError as e:
  print("FAILURE:  Unable to back up archive:  terminating.")
  print("FAILURE REASON: ",e)
  exit(-1)

# create fammatch subdirectory in seizure directory
# if this directory currently exists it will be DELETED; this avoids
# the risk of getting a mix of stale and current files in here.
# if this fails, we just terminate; nothing harmful has been done yet
# as a side effect, deletes failfile from previous cycle

try:
  os.chdir(prefix)
  if os.path.isdir("fammatch"):
    command = ["rm","-rf","fammatch"]
    run_and_report(command,"Unable to delete fammatch directory")
  command = ["mkdir","fammatch"]
  run_and_report(command,"Unable to make fammatch directory")
except RuntimeError as e:
  print(e)
  exit(-1)

# the remainder of the program is in a try loop:  if it
# catches we will restore from backup

try:
  # update seizure metadata 
  # note:  update_metadata.py will create this file if it does not exist
  seizure_metafile = meta_path + meta_prefix + ".tsv"
  print("metafile is",seizure_metafile)
  prog = ivory_dir + "src/update_metadata.py"
  command = ["python3",prog,seizure_metafile,prefix]
  run_and_report(command,"Unable to update seizure metadata")
  
  # for each species present:
  outprefix = "outdir"
  species_present = []
  os.chdir("fammatch")
  for species in ["forest","savannah"]:
    speciesdir = "n" + species
    if not os.path.isdir("../" + speciesdir):  continue   # this species is not present
    species_present.append(species)
    # create species subdirectory
    outdirname = outprefix + "_" + species
    if not os.path.isdir(outdirname):
      command = "mkdir " + outdirname
      os.system(command)
  
    # create SCAT sector run command and run SCAT
    datafile = "../" + prefix + "_" + species + ".txt"
    zonefile = zones_path + zones_prefix + "_" + species + ".txt"
    command = [scat_exe,"-Z","-H2",datafile,zonefile,outdirname,"16"]
    run_and_report(command,"Unable to run SCAT to determine sectors")
  
  # run prep_fammatch.py
  os.chdir(startdir)     # return to root directory of all seizures
  progname = ivory_dir + "src/prep_fammatch.py"
  command = ["python3",progname]
  command += [prefix, pathsfile]
  run_and_report(command,"Failure in program " + progname)
  
  # run run_fammatch.py
  # this calls rout2db.py to tidy up the fammatch output
  progname = ivory_dir + "src/run_fammatch.py"
  command = ["python3",progname]
  command += [prefix,pathsfile]
  run_and_report(command,"Unable to run " + progname)
  print("Fammatch runs completed and archived")
  
  # everything seems to have succeeded, so we will add this seizure to the
  # list of processed seizures
  
  oldseizures.append(prefix + "\n")
  outfile = open(seizurelist,"w")
  for entry in oldseizures:
    outfile.write(entry)
  outfile.close()

except RuntimeError as e:
  # write failfile
  failname = startdir + prefix + "/fammatch/FAILURE_REPORT"
  failfile = open(failname,"w")
  failfile.write(str(e) + "\n")
  failfile.close()
  print("FAILED:  Restoring from backups")
  print("FAILURE REASON:  ",e)
  restore_archive(arch_dir)
  exit(-1)
