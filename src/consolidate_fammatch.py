# look into every directory with a /fammatch in it
# look into all sub* directories off that

# how os.walk works:
# it returns triples in which the first one ("root") is the current
# working directory, the second ("dirs") is a list of all its subdirectories,
# and the third ("files") is a list of all its files
# it recurses from where it starts down all possible subdirectories, so the
# first triple returned is where you started, the second is into a subdirectory, etc.

import os
nsubs = 6
outfiles = {}
header = "s1\ts2\tDM_LR\tPO_LR\tFS_LR\tHS_LR\tnloci\n"

# create global fammatch directory if it does not already exist
if not os.path.isdir("fammatch"):
  os.mkdir("fammatch")

for n in range(0,nsubs):
  outfilename = "fammatch/obsLRs." + str(n) + ".txt"
  outfile = open(outfilename,"w")
  outfile.write(header)
  outfiles[n] = outfile

for root,dirs,files in os.walk("."):
  # skip unless this is an appropriate directory
  if root[-13:-1] != "fammatch/sub":  continue

  sub = int(root[-1])
  if sub not in range(0,nsubs):
    print("impossible subregion",sub,"found in",root)
    exit(-1)

  for file in files:
    if file == "obsLRs.forest.txt" or file == "obsLRs.savannah.txt":
      print("Found LR file",file)
      for line in open(root+"/"+file,"r"):
        if line.startswith("s1"):  continue   # skip header
        outfiles[sub].write(line)

for sub in range(0,nsubs):
  outfiles[sub].close()
