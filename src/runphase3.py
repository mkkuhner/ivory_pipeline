import sys
import subprocess
from subprocess import Popen, PIPE

if len(sys.argv) != 3:
  print("Usage: python runphase3.py seizurelist pathsfile.tsv")
  print("  seizurelist contains seizures to be run, one per line")
  exit(-1)

seizurelines = open(sys.argv[1],"r").readlines()
pathsfiles = sys.argv[2]

for line in seizurelines:
  seizure = line.rstrip()
  command = "python3 phase3.py " + seizure + " " + pathsfile
  process = Popen(command)
  stdout, stderr = process.communicate()
  exit_code = process.wait()
  if exit_code != 0:
    print("    FAILED to run seizure " + seizure + "\nTERMINATING")
    exit(-1)
