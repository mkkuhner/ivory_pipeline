import sys
if len(sys.argv) != 5:
  print("USAGE:  python setupscatruns.py prefix rootdir masterscript randseed")
  exit()

numruns = 9
prefix = sys.argv[1]
rootdir = sys.argv[2]
masterfile = sys.argv[3]
randseed = int(sys.argv[4])

import os
for i in range(1,numruns+1):
  # set up the directories
  mydir = str(i)
  command = "mkdir " + rootdir + "/" + mydir
  os.system(command)
  command = "mkdir " + rootdir + "/" + mydir + "/outputs" 
  os.system(command)

  # make run files
  myrunfile = "run" + str(i) + ".sh"
  command = "cp " + masterfile + " " + rootdir + "/" + mydir + "/" + myrunfile
  os.system(command)

  # edit run files for cluster run
  runfilepath = rootdir + "/" + mydir + "/" + myrunfile

  # random number seed
  command = 'perl -p -i -e "s/SEED/' + str(randseed) + '/;" ' + runfilepath
  os.system(command)

  # unique job name:  prefix + root directory + run number
  jobname = prefix + "_" + rootdir + "_" + mydir
  command = 'perl -p -i -e "s#UNAME#' + jobname + '#;" ' + runfilepath
  os.system(command)

  # local path
  localpath = "/gscratch/wasser/mkkuhner/seizureruns/" + prefix + "/" + rootdir + "/" + mydir
  command = 'perl -p -i -e "s#LOCALPATH#' + localpath  + '#;" ' + runfilepath
  os.system(command)

  # 
  randseed += 1
print("Finished creating directories")
