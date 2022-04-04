import sys

if len(sys.argv) != 3:
  print("USAGE: python renameseizuredir.py origname newname")
  print("  assumes that we are in the directory directly containing 'origname'")
  exit(-1)

origname = sys.argv[1]
newname = sys.argv[2]

import os

cwd = os.getcwd()

stuff = os.listdir(cwd)
if newname in stuff:
  print("ERROR: seizure directory",newname,"already exists")
  print("  possible argument switch?")
  print("  no changes made")
  exit(-1)
if origname not in stuff:
  print("ERROR: could not find seizure directory",origname,"to rename to",newname)
  print("  possible argument switch?")
  print("  no changes made")
  exit(-1)

if not cwd.endswith("/"):
  cwd += "/"

newroot = cwd + origname

for root, dirs, files in os.walk(newroot, topdown = True):
  for dir in dirs:
     if origname in dir:
       dir = os.path.join(root,dir)
       newdir = dir.replace(origname,newname)
       os.replace(dir,newdir)
  for file in files:
     if origname in file:
       newfile = file.replace(origname,newname)
       newfile = os.path.join(root,newfile)
       file = os.path.join(root,newfile)
       os.replace(file,newfile)

os.replace(cwd+origname,cwd+newname)
