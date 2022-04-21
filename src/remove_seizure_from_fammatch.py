# remove arbitrary seizure from fammatch database:
#   elephant_msat_database.tsv
#   old_inputs
#   seizurelist.tsv
#   seizure_metadata.tsv
# goal is to be able to run this seizure again as if it had never been run

########################################################################
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
    print("Unix exit code ",exit_code)
    raise RuntimeError(errormsg)

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

def backup_archive(arch_dir):
  backupdir = arch_dir + "../archive_backups/"
  if not os.path.isdir(arch_dir):
    raise RuntimeError("Archive " + arch_dir + " does not exist")
  # delete previous backup directory
  if os.path.isdir(backupdir):
    command = ["rm","-rf",backupdir]
    print(command)
    run_and_report(command,"Unable to delete old backup directory" + backupdir)
  # copy archive to backup directory
  command = ["cp","-r",arch_dir,backupdir]
  print(command)
  run_and_report(command,"Unable to back up archive")

def restore_archive(arch_dir):
  # make copy of current state of archive directory, for debugging
  forensicdir = arch_dir + "../forensics/"
  if os.path.isdir(arch_dir):
    command = ["cp","-r",arch_dir,forensicdir]
    run_and_report(command,"Unable to snapshot archive for debugging")
  backupdir = arch_dir + "../archive_backups/"
  # delete archive directory
  if os.path.isdir(arch_dir):
    command = ["rm","-rf",arch_dir]
    run_and_report(command,"Unable to delete " + arch_dir)
  # copy backup directory
  command = ["cp","-r",backupdir,arch_dir]
  run_and_report(command,"Unable to restore archive from backup directory " + backupdir)

def rewrite_or_delete(filename,newcontents):
  if len(newcontents) > 0:  # rewrite the file
    outfile = open(filename,"w")
    outfile.writelines(newcontents)
    outfile.close()
  else:  # nothing is left, delete the file
    command = ["rm", "-f", filename]
    run_and_report(command,"Unable to delete " + filename)

########################################################################
# main

import sys, os
import subprocess
from subprocess import Popen, PIPE

if len(sys.argv) != 3:
  print("USAGE:  python3 remove_seizure_from_fammatch.py PREFIX pathfile")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]
numsecs = 6

pathdir = readivorypath(pathsfile)
arch_dir = pathdir["fammatch_archive_dir"][0]
ivory_dir = pathdir["ivory_pipeline_dir"][0]
meta_path, meta_prefix = pathdir["metadata_prefix"]

# back up archive in case something goes wrong
try:
  backup_archive(arch_dir)
except RuntimeError as e:
  print("FAILURE:  could not back up archive, terminating")
  print("FAILURE REASON:  ",e)
  exit(-1)
except Exception as e:
  print("FAILURE:  could not back up archive, terminating")
  print(e)
  exit(-1)

# do all the removals within a try, so that we can restore from
# backups if something goes wrong
try:

  # remove seizure from elephant_msat_database.tsv
  progname = ivory_dir + "src/fammatch_database.py"
  database_name = arch_dir + "elephant_msat_database.tsv"
  command = ["python3",progname,database_name,"remove",prefix]
  run_and_report(command,progname + " failed on " + database_name)

  # remove seizure from seizure_metadata.tsv, at the same time building
  # up a list of elephant names to remove elsewhere
  unwanted_samples = set()     # for speed
  new_meta = []
  metafile = meta_path + meta_prefix + ".tsv"
  for line in open(metafile,"r"):
    seizure, sid = line.rstrip().split("\t")
    if seizure != prefix:
      new_meta.append(line)
    else:
      unwanted_samples.add(sid)
  rewrite_or_delete(metafile,new_meta)

  # remove seizure from old_inputs
  for sector in range(0,numsecs):
    secname = str(sector)
    oldfilename = arch_dir + "old_inputs/old" + secname + ".csv"
    if not os.path.isfile(oldfilename):  continue  # skip to next sector
    newcontents = []
    for line in open(oldfilename,"r"):
      sid = line.rstrip().split(",")[0]
      if sid == "Match ID": # header
        header = line
        continue
      if sid not in unwanted_samples:
        newcontents.append(line)
      if len(newcontents) > 0:    # if we had no entries, don't put in the header
        newcontents = [header] + newcontents
    rewrite_or_delete(oldfilename,newcontents)
          
  # finally remove seizure from seizurelist.tsv
  seizurelist = arch_dir + "seizurelist.tsv"
  newcontents = []
  for line in open(seizurelist,"r"):
    seizure = line.rstrip()
    if seizure != prefix:
      newcontents.append(line)
  rewrite_or_delete(seizurelist,newcontents)

except RuntimeError as e:
  print("FAILURE:  could not remove seizure from archive")
  print("FAILURE REASON:  ",e)
  restore_archive(arch_dir)
  exit(-1)

except:
  print("FAILURE due to unexpected error in remove_seizure_from_fammatch.py")
  restore_archive(arch_dir)
  exit(-1)
