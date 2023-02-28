# step0_newarchive.py sets up for a NEW set of runs, for example if
# you have changed the reference data, maps, or zones files.  It
# does not run any analyses itself, but it creates the archive and
# edits the ivory_paths file to point at it.  It must be given an 
# archive name that, when combined with the archive root found in
# ivory_paths.tsv, does NOT point to any existing archive.

# Run this in the parent directory of all seizures

import sys
import os
import subprocess
from subprocess import Popen, PIPE
import ivory_lib as iv

############################################################################
## main program

if len(sys.argv) != 3:
  print("USAGE:  python3 step0_newarchive.py pathsfile.tsv new_archive")
  exit(-1)

pathsfile = os.path.abspath(sys.argv[1])
new_archname = sys.argv[2]
if not new_archname.endswith("/"):
  new_archname += "/"

# read ivory_paths.tsv file
pathdir = iv.readivorypath(pathsfile)
arch_dir, old_archname = pathdir["fammatch_archive_dir"]

# the new archive must not already exist
if os.path.isdir(arch_dir + new_archname):
  print("Cannot create new archive",new_archname,"as it already exists")
  exit(-1)

# create new archive and subdirectories within it
command = ["mkdir",arch_dir + new_archname]
iv.run_and_report(command, "Unable to create archive")
try:
  command = ["mkdir",arch_dir + new_archname + "old_inputs"]
  iv.run_and_report(command, "Unable to create subdirectory 'old_inputs'")
  command = ["mkdir",arch_dir + new_archname + "reference"]
  iv.run_and_report(command, "Unable to create subdirectory 'reference'")
except:
  print("Archive could not be completely created; deleting it")
  command = ["rm -rf",arch_dir + new_archname]
  iv.run_and_report(command,"Could not delete failed archive")
  exit(-1)

print("New archive created as",arch_dir + new_archname)

# Edit ivory_paths to point at new archive
found_archive = False
found_meta = False
pathdata = open(pathsfile,"r").readlines()
newpathdata = []
for line in pathdata:
  if line.startswith("fammatch_archive_dir"):
    newline = ["fammatch_archive_dir",arch_dir,new_archname]
    newline = "\t".join(newline) + "\n"
    newpathdata.append(newline)
    found_archive = True
  elif line.startswith("metadata_prefix"):
    parts = line.split("\t")
    newline = [parts[0],arch_dir + new_archname,parts[2]]
    newline = "\t".join(newline) + "\n"
    newpathdata.append(newline)
    found_meta = True
  else:
    newpathdata.append(line)

if not found_archive:
  print("Could not find fammatch_archive_dir entry in",pathsfile)
  print("Hand-edit this file to add the new archive before proceeding")
elif not found_meta:
  print("Could not find metadata_prefix entry in",pathsfile)
  print("Hand-edit this file to add the new archive before proceeding")
else:
  pathout = open(pathsfile,"w")
  for line in newpathdata:
    pathout.write(line)
  pathout.close()
  print("Updated paths file",pathsfile)
