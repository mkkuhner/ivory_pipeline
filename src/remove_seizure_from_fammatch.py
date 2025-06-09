# remove arbitrary seizure from fammatch database:
#   elephant_msat_database.tsv
#   old_inputs
#   seizurelist.tsv
#   seizure_metadata.tsv
# goal is to be able to run this seizure again as if it had never been run

# 4/6/23 revising for new archive directory structure

import ivory_lib as iv
import sys
import os
import subprocess
from subprocess import Popen, PIPE


########################################################################
# functions

def copy_if_src_present(src,tgt):
  # do nothing if src not present
  if not os.path.isfile(src):  return

  # if tgt exists, delete it
  if os.path.isfile(tgt):
    command = ["rm","-rf",tgt]
    iv.run_and_report(command,"File " + tgt + " cannot be removed")

  # copy
  command = ["cp",src,tgt]
  iv.run_and_report(command, "Unable to copy file " + src + " to " + tgt)

def rewrite_or_delete(filename,newcontents):
  if len(newcontents) > 0:  # rewrite the file
    outfile = open(filename,"w")
    outfile.writelines(newcontents)
    outfile.close()
  else:  # nothing is left, delete the file
    command = ["rm", "-f", filename]
    iv.run_and_report(command,"Unable to delete " + filename)

########################################################################
# main

if len(sys.argv) != 3:
  print("USAGE:  python3 remove_seizure_from_fammatch.py PREFIX pathfile")
  exit(-1)

prefix = sys.argv[1]
pathsfile = sys.argv[2]
numsecs = 6

pathdir = iv.readivorypath(pathsfile)
arch_dir = pathdir["fammatch_archive_dir"]
refprefix = pathdir["reference_prefix"][1]
arch_name = "elephant_archive_" + refprefix + "/"
archive = arch_dir + arch_name
database_name = archive + "elephant_msat_database.tsv"
ivory_dir = pathdir["ivory_pipeline_dir"][0]
metafile = archive + "seizure_metadata.tsv"
data_dir = pathdir["seizure_data_dir"][0]

# back up archive in case something goes wrong
iv.backup_archive(arch_dir, arch_name)

# build a list of all elephants in this seizure, *including ones with no
# match entries*, so they can be cleanly removed.  (Using only ones with a 
# match can leave cruft in old_inputs, which under some circumstances will
# have elephants that do not appear in the matchlist).

rawdata = data_dir + prefix + "_raw.tsv"
if not os.path.isfile(rawdata):
  print("ERROR:  unable to find raw data file", rawdata, "so no removal done.")
  exit(-1)
unwanted_samples = []
for line in open(rawdata,"r"):
  line = line.rstrip().split("\t")
  if line[0] == "MatchID":  continue   # skip header
  unwanted_samples.append(line[0])

# do all the removals within a try, so that we can restore from
# backups if something goes wrong
try:
  # remove seizure from elephant_msat_database.tsv
  progname = ivory_dir + "src/fammatch_database.py"
  command = ["python3",progname,database_name,"remove",prefix]
  iv.run_and_report(command,progname + " failed on " + database_name)

  # remove seizure from seizure_metadata.tsv, at the same time building
  # up a list of elephant names to remove elsewhere
  new_meta = []
  for line in open(metafile,"r"):
    seizure, sid = line.rstrip().split("\t")
    if seizure != prefix:
      new_meta.append(line)
  rewrite_or_delete(metafile,new_meta)

  # remove seizure from old_inputs
  for sector in range(0,numsecs):
    secname = str(sector)
    oldfilename = archive + "old_inputs/old" + secname + ".csv"
    if not os.path.isfile(oldfilename):  continue  # skip to next sector
    newcontents = []
    for line in open(oldfilename,"r"):
      sid = line.rstrip().split(",")[0]
      if sid == "Match ID": # header
        header = line
        continue
      if sid not in unwanted_samples:
        newcontents.append(line)

    # now write the revised file out
    if len(newcontents) > 0:    # if we had no entries, don't put in the header
      newcontents = [header] + newcontents
    rewrite_or_delete(oldfilename,newcontents)
          
  # finally remove seizure from seizurelist.tsv
  seizurelist = archive + "seizurelist.tsv"
  newcontents = []
  for line in open(seizurelist,"r"):
    seizure = line.rstrip()
    if seizure != prefix:
      newcontents.append(line)
  rewrite_or_delete(seizurelist,newcontents)

except RuntimeError as e:
  print("FAILURE:  could not remove seizure from archive")
  print("FAILURE REASON:  ",e)
  iv.restore_archive(arch_dir, arch_name)
  exit(-1)

except:
  print("FAILURE due to unexpected error in remove_seizure_from_fammatch.py")
  iv.restore_archive(arch_dir, arch_name)
  exit(-1)
