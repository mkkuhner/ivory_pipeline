import sys
if len(sys.argv) != 4:
  print("USAGE:  python setupscatruns.py rootdir masterscript randseed")
  exit()

numruns = 9
rootdir = sys.argv[1]
masterfile = sys.argv[2]
randseed = int(sys.argv[3])

import os
for i in range(1,numruns+1):
  # set up the directories
  mydir = str(i)
  command = "mkdir " + rootdir + "/" + mydir
  os.system(command)
  command = "mkdir " + rootdir + "/" + mydir + "/outputs" 
  os.system(command)

  # make run files
  myrunfile = "run" + str(i)
  command = "cp " + masterfile + " " + rootdir + "/" + mydir + "/" + myrunfile
  os.system(command)

  # edit run files for cluster run
  runfilepath = rootdir + "/" + mydir + "/" + myrunfile

  # random number seed
  command = 'perl -p -i -e "s/SEED/' + str(randseed) + '/;" ' + runfilepath
  os.system(command)

  # unique job name:  root directory plus run number
  jobname = rootdir + "_" + mydir
  command = 'perl -p -i -e "s#UNAME#' + jobname + '#;" ' + runfilepath
  os.system(command)

  # local path
  localpath = "/gscratch/wasser/mkkuhner/seizureruns/" + rootdir + "/" + mydir
  command = 'perl -p -i -e "s#LOCALPATH#' + localpath  + '#;" ' + runfilepath
  os.system(command)

  # 
  randseed += 1
print("Finished creating directories")
