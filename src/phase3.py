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

archivefiles = ["elephant_msat_database.tsv","seizurelist.tsv","seizure_metadata.tsv"]
archivedirs = ["old_inputs","reference"]

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
  #print("command is ",command)
  #print("running in ",os.getcwd())
  #process = Popen(command, stdout=PIPE,stderr=PIPE)
  process = Popen(command)
  stdout, stderr = process.communicate()
  exit_code = process.wait()
  if exit_code != 0:
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

def backup_archive(fam_dir):
  backupdir = fam_dir + "archive_backups/"
  # delete previous backup directory
  if os.path.isdir(backupdir):
    command = ["rm","-rf",backupdir]
    run_and_report(command,"Unable to delete old backup directory" + backupdir)
  # create backup directory and copy in files
  command = ["mkdir",backupdir]
  run_and_report(command,"Unable to create backup directory")
  for filename in archivefiles:
    copy_if_src_present(fam_dir + filename, backupdir + filename)
  # ... and subdirectories
  for dirname in archivedirs:
    command = ["cp","-r",fam_dir + dirname, backupdir + dirname]
    run_and_report(command,"Unable to populate backup directory")

def restore_archive(fam_dir):
  backupdir = fam_dir + "archive_backups/"
  for filename in archivefiles:
    copy_if_src_present(backupdir + filename, fam_dir + filename)
  for dirname in archivedirs:
    command = ["rm","-rf", fam_dir + dirname]
    run_and_report(command,"Unable to delete files in " + fam_dir + dirname)
    command = ["cp", backupdir + dirname + "/*", fam_dir + dirname + "/"]
    run_and_report(command,"Unable to recover from backup: " + fam_dir + dirname)

###################################################################
# main program

if len(sys.argv) != 3:
  print("USAGE:  python phase3.py PREFIX pathsfile.tsv")
  print("This should be run in the parent directory of all seizures")
  print("and the pathsfile must be the same as used in phase1.py and phase2.py")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]
formalseizurename = prefix.replace("_", ", ")
print("Seizure will be called",formalseizurename)

# NB:  We do NOT check seizure_modifications in this program.
# This means we will not omit REJECT seizures nor merge MERGE seizures.
# This allows us to have fammatch results for them in case they are
# of interest, and also allows us to change our minds about MERGE or
# reject without having to rerun everything.

# The seizure_modifications are implemented in phase4.py instead, to keep
# unwanted seizures out of the final networks.

# save what directory we were run in (should be root directory of all seizures)
startdir = os.getcwd()

# read paths file
pathdir = readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]
zones_path, zones_prefix = pathdir["zones_prefix"]
scat_exec = pathdir["scat_executable"][0]
fam_dir = pathdir["fammatch_archive_dir"][0]
meta_path, meta_prefix = pathdir["metadata_prefix"]
mod_path, mod_prefix = pathdir["seizure_modifications_prefix"]
ref_path, ref_prefix = pathdir["reference_prefix"]

# check if this seizure has already been run.  We will not run it again
# unless the user first cleans it out.

seizurelist = fam_dir + "seizurelist.tsv"
oldseizures = []
if os.path.isfile(seizurelist):
  is_present, oldseizures = check_seizure_present(seizurelist, prefix)
  if is_present:
    print("Seizure",prefix,"is already present in the archive")
    print("If you need to rerun it, call remove_seizure_from_fammatch.py first")
    print("NOT IMPLEMENTED YET")
    exit(-1)

# Back up the entire archive.  This will be used to recover if something
# goes wrong at any point in this program.

try:
  backup_archive(fam_dir)
except RuntimeError as e:
  print("Unable to back up archive:  terminating.")
  print(e)
  exit(-1)

# create fammatch subdirectory in seizure directory
# if this directory currently exists it will be DELETED; this avoids
# the risk of getting a mix of stale and current files in here.
# if this fails, we just terminate; nothing harmful has been done yet

try:
  os.chdir(prefix)
  if os.path.isdir("fammatch"):
    print("Deleting previous familial matching directory")
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
  prog = ivory_dir + "src/update_metadata.py"
  command = ["python3",prog,seizure_metafile,prefix,formalseizurename]
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
    command = [scat_exec,"-Z","-H2",datafile,zonefile,outdirname,"16"]
    run_and_report(command,"Unable to run SCAT to determine sectors")
  
  # run prep_fammatch.py
  os.chdir(startdir)     # return to root directory of all seizures
  sector_metafile = fam_dir + "sector_metadata.txt"
  progname = ivory_dir + "src/prep_fammatch.py"
  command = ["python3",progname]
  command += [prefix, zones_prefix, zones_path]
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
  print("Restoring from backups")
  restore_from_backups(fam_dir)
  exit(-1)
