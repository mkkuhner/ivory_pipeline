import sys
import ivory_lib as iv
import os

forbidden_suffixes = [".pdf",".docx",".xlsx",".odt",".pkl",".png"]

#####
# functions

def rename_within_file(oldfile,origname,newname):
  # if you somehow got passed a directory, don't touch it
  if os.path.isdir(oldfile):  return

  # do not touch files which are not text-like
  for suffix in forbidden_suffixes:
    if oldfile.endswith(suffix):  return

  # do not touch files which are executable
  # NB:  you have to, because of .sh executable run commands
  # if os.access(oldfile, os.X_OK): return

  # we will update in place by first reading and closing
  # the file, then opening it for writing.
  try:
    lines = open(oldfile,"r").readlines()
  except:
    print("was not able to open file",oldfile,"for reading")
    print("skipping it")
    # DEBUG
    exit(-1)

  outfile = open(oldfile,"w")
  for line in lines:
    line = line.replace(origname,newname)
    outfile.write(line)
  outfile.close()

def rename_dir_contents(dir,origname,newname):
# call this from the directory containing origname
# it is recursive down that directory
  os.chdir(dir)
  curdir = os.getcwd() + "/"
  for item in os.listdir(curdir):
    if os.path.isdir(item):
      # recursively rename directory contents
      rename_dir_contents(item,origname,newname)
    else:
      # rename within this file
      rename_within_file(item,origname,newname)

    # in either case, rename the item itself if needed
    if origname in item:
      newitem = item.replace(origname, newname)
      os.rename(item, newitem)
  os.chdir("..")

#####
# main

if len(sys.argv) != 4:
  print("USAGE: python rename_seizure.py origname newname ivory_paths.tsv")
  print("  assumes that we are in the directory directly containing 'origname'")
  exit(-1)

origname = sys.argv[1]
newname = sys.argv[2]
pathsfile = sys.argv[3]
pathdir = iv.readivorypath(pathsfile)
# get elephant archive out of it
arch_dir = pathdir["fammatch_archive_dir"]
arch_root = arch_dir[0] + "/" + arch_dir[1] + "/"
ivory_dir = pathdir["ivory_pipeline_dir"][0] + "src/"


if not os.path.isdir(arch_root):
  print("Archive base directory",arch_dir,"does not exist")
  print("Did you forget to mount the hard drive?")
  print("  no changes made")
  exit(-1)

cwd = os.getcwd() + "/"

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

# take care of the seizure directory, recursively
# and including renaming it
rename_dir_contents(newroot,origname,newname)
os.rename(newroot, newname)

# regenerate the .png reports, which contain the
# seizure name and can't be edited
progname = ivory_dir + "plot_results.py"
cmd = ["python3",progname,newname,pathsfile]
iv.run_and_report(cmd,"Unable to re-run graphics")

# take care of the fammatch_overall directory
famroot = cwd + "fammatch_overall"
rename_dir_contents(famroot,origname,newname)

# take care of the fammatch archive
rename_dir_contents(arch_root,origname,newname)
