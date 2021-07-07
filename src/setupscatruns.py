import sys
if len(sys.argv) != 4:
  print("USAGE:  python setupscatruns.py rootdir masterscript randseed")
  exit()

numruns = 9
rootdir = sys.argv[1]
masterfile = sys.argv[2]
randseed = int(sys.argv[3])

# set up the directories
import os
#command = "mkdir " + rootdir
#os.system(command)
for i in range(1,numruns+1):
  mydir = str(i)
  command = "mkdir " + rootdir + "/" + mydir
  os.system(command)
  command = "mkdir " + rootdir + "/" + mydir + "/outputs" 
  os.system(command)
  myrunfile = "run" + str(i) + ".sh"
  command = "cp " + masterfile + " " + rootdir + "/" + mydir + "/" + myrunfile
  os.system(command)
  runfilepath = rootdir + "/" + mydir + "/" + myrunfile
  command = 'perl -p -i -e "s/SEED/' + str(randseed) + '/;" ' + runfilepath
  os.system(command)
  randseed += 1
print("Finished creating directories")
