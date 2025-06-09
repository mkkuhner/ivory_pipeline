# make_new_archive.py sets up for a NEW set of runs, for example if
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
  print("USAGE:  python3 make_new_archive.py pathsfile.tsv new_archive")
  exit(-1)

pathsfile = os.path.abspath(sys.argv[1])
new_archname = sys.argv[2]
if not new_archname.endswith("/"):
  new_archname += "/"

# read ivory_paths.tsv file
pathdir = iv.readivorypath(pathsfile)
arch_dir = pathdir["fammatch_archive_dir"][0]

# base directory must exist
if not os.path.isdir(arch_dir):
  print("Archive base directory",arch_dir,"does not exist")
  print("Did you forget to mount the hard drive?")
  exit(-1)

# the new archive must not exist
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
