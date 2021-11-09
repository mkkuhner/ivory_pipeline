# given a list of names of new elephants, and a genotype file for
# them, as well as an archive of old elephants (reference, genotypes,
# names and results):

# 1.  figure out what fammatches to run
# 2.  construct needed input files
# 3.  run the fammatches (one at a time?  all at once?)
# 4.  update the archive to include the new elephants

# archive structure:
# root directory
# subdirectories old_names, old_inputs, old_results, old_reference
# within those, sectors (sec0, sec1 etc.)
# within those, seizures (old_inputs, and old_results)

# ISSUES:  do we do anything with the reference files?

##########################################################################
# functions

import subprocess
from subprocess import Popen

def run_and_report(command,errormsg):
  process = Popen(command)
  stdout, stderr = process.communicate()
  exit_code = process.wait()
  if exit_code != 0:
    print("FAILURE: " + errormsg)
    exit(-1)

def safecopy(fromfile,tofile):
  if not os.path.isfile(tofile):
    command = ["cp",fromfile,tofile]
    run_and_report(command, "Unable to copy file " + fromfile)

# assumes that the file consists of 2 tab delimited columns, no header,
# first column = string, sector id
# second column = string, species name
def read_sector_metadata(metafilename):
  sector2species = {}
  for line in open(metafilename,"r"):
    pline = line.rstrip().split("\t")
    sector2species[pline[0]] = pline[1]
  return sector2species

##########################################################################
# main program

import os, sys
#from datetime import date
from datetime import datetime

if len(sys.argv) != 4:
  print("USAGE:  run_fammatch.py prefix fammatch_archive pipeline_dir")
  exit(-1)

nsec = 6

header = "Match ID,FH67,FH67,FH71,FH71,FH19,FH19,FH129,FH129,FH60,FH60,FH127,FH127,FH126,FH126,FH153,FH153,FH94,FH94,FH48,FH48,FH40,FH40,FH39,FH39,FH103,FH103,FH102,FH102,S03,S03,S04,S04"

# set up directory names to be used throughout
# NO DIRECTORY NAMES END IN /

prefix = sys.argv[1]
seizuredir = prefix + "/fammatch"
archivedir = sys.argv[2]
ivorydir = sys.argv[3]

names_archive = archivedir + "/old_names"
inputs_archive = archivedir + "/old_inputs"
# results_archive needs an absolute path because we change directories
# to run Rscripts before saving our fammatch results
results_archive = os.path.abspath(archivedir + "/old_results")
ref_archive = archivedir + "/reference"
#today = str(date.today())
today = str(datetime.today()).replace(" ","_")
backupdir = archivedir + "/backups/" + today 


# before starting, back up previous results
if not os.path.isdir(backupdir):
  os.mkdir(backupdir)
else:
  print("Backups for ",today," already exist.  Remove before running.")
  exit(-1)

command = ["cp","-r",names_archive,backupdir]
run_and_report(command,"Cannot back up "+names_archive)
command = ["cp","-r",inputs_archive,backupdir]
run_and_report(command,"Cannot back up "+inputs_archive)
command = ["cp","-r",results_archive,backupdir]
run_and_report(command,"Cannot back up "+results_archive)
command = ["cp","-r",ref_archive,backupdir]
run_and_report(command,"Cannot back up "+ref_archive)


# create fammatch inputs and run program
old_names = [[] for x in range(0,nsec)]
old_namelines = [[] for x in range(0,nsec)]
new_names = [[] for x in range(0,nsec)]
new_namelines = [[] for x in range(0,nsec)]

# read sector metadata from ivory pipeline
sectorfile = ivorydir + "/aux/sector_metadata.tsv"
sector2species = read_sector_metadata(sectorfile)

for sector in range(0,nsec):
  secname = str(sector)
  species = sector2species[secname]

  # if reference file is present it MUST be identical to the archived one
  # (we cannot merge results from difference references!)
  newreffile = seizuredir + "/ref_" + secname + "_fammatch.csv"
  if os.path.isfile(newreffile):
    oldreffile = ref_archive + "/ref_" + secname + "_fammatch.csv"
    # if the old ref file doesn't exist we don't need to check against it
    if os.path.isfile(oldreffile):
      command = ["diff",newreffile,oldreffile]
      run_and_report(command,"Discrepant reference data detected for sector " + secname)
    else:
      command = ["cp",newreffile,oldreffile]
      run_and_report(command,"Unable to copy reference file for sector " + secname)

  # establish what samples we're dealing with, respecting that the sector might not
  # have any previously existing samples

  oldnamefile = names_archive + "/old_names_" + secname + ".tsv"
  newnamefile = seizuredir + "/names_" + secname + ".tsv"

  if not os.path.isfile(newnamefile):  continue    # nothing to add
  newnamelines = open(newnamefile,"r").readlines()

  myoldnames = set()
  if not os.path.isfile(oldnamefile):
    # reserve the first "new" name as an old name
    name = newnamelines.pop(0).rstrip().split("\t")[0]
    myoldnames.add(name)
  else :
    # read old_names file
    # it has the form archive/old_names/old_names_0.tsv
    for line in open(oldnamefile,"r"):
      myline = line.rstrip().split("\t")
      name = myline[0]
      seize = myline[1]
      myoldnames.add(name)
      old_namelines[sector].append(line)
  old_names[sector] = list(myoldnames)

  # read new_names file, bail if nothing new
  # it has the form seizuredir/names_0.tsv
  new_names[sector] = []
  for line in newnamelines:
    name = line.rstrip().split("\t")[0]
    if name in old_names[sector]:
      print("New elephant ",name," in sector ",secname," has already been seen")
      exit(-1)
    new_names[sector].append(name)
    new_namelines[sector].append(line)

# JDEBUG, I think this is impossible, since if something is culled we hard exit!
  if len(new_names[sector]) == 0:  # all were culled
    continue

  # be sure to remove old (temp) directories if present
  # and be sure to clean up at end, maybe only a single temp directory
  # since archiving should happen after each sector run
  # create run directories if needed
  rundir = seizuredir + "/"
  if not os.path.isdir(rundir):
    os.mkdir(rundir)

  # assemble lines for the "old" file, the case of a sector with no previous
  # samples is handled in the "newlines" code below
  oldinputdir = inputs_archive + "/"
  oldlines = []
  if os.path.isdir(oldinputdir):
    for oldinputfile in os.listdir(oldinputdir):
      for line in open(oldinputdir + "/" + oldinputfile,"r"):
        if line.startswith("Match"):  continue   # header
        sid = line.rstrip().split(",")[0]
        if sid in old_names[sector]:
          oldlines.append(line)

  # assemble lines for the "new" file and handle the case of one of the "new" sids
  # is to be treated as an "old" sid
  # 
  # csv format used because that is what the Rscripts expect
  prepfilename = rundir + "prep" + secname + ".csv"
  newlines = []
  for line in open(prepfilename,"r"):
    if line.startswith("Match"):   # header
      continue
    sid = line.rstrip().split(",")[0]
    if sid in new_names[sector]:
      newlines.append(line)
    if sid in old_names[sector]:
      oldlines.append(line)
  
  # write "old" and "new" files
  #
  # csv format used because that is what the Rscripts expect
  oldfilename = rundir + "old" + secname + ".csv"
  oldfile = open(oldfilename,"w")
  newfilename = rundir + "new" + secname + ".csv"
  newfile = open(newfilename,"w")

  # NB:  if there are no "old" lines, we must borrow an elephant from "new"
  # to make up our "old" file
  oldfile.write(header + "\n")
  newfile.write(header + "\n")
  for oldline in oldlines:
    oldfile.write(oldline)
  for newline in newlines:
    newfile.write(newline)
  oldfile.close()
  newfile.close()

  # copy fammatch code into run directory
  safecopy(ivorydir + "/src/calculate_LRs.R", rundir + "calculate_LRs.R")
  safecopy(ivorydir + "/src/LR_functions.R", rundir + "LR_functions.R")

  # run fammatch
  os.chdir(rundir)  # we do this to be able to run the Rscripts but we need to then
                    # pass the local filenames to it
  rfile = "ref_" + secname + "_fammatch.csv"
  ofile = "old" + secname + ".csv"
  nfile = "new" + secname + ".csv"
  command = ["Rscript","calculate_LRs.R",species,rfile,ofile,nfile]
  print("Calculating familial matches for sector ",sector)
  run_and_report(command,"Unable to execute calculate_LRs.R")

  # archive files

  # add new sample names to old_names
  if len(old_namelines[sector]) > 0 or len(new_namelines[sector]) > 0:
    outfile = open(oldnamefile,"w")
    for line in old_namelines[sector]:
      outfile.write(line) 
    for line in new_namelines[sector]:
      outfile.write(line)
    outfile.close()

  # make a new seizure file of old_inputs
  # we don't copy "newfile" because one sample might have gone into "oldfile"
  if len(newlines) > 0:
    # what to do if this file already exists?
    inputfile = inputs_archive + "/" + prefix + "_inputs_" + secname + ".tsv"
    infile = open(inputfile,"w")
    for line in newlines:
      infile.write(line)
    infile.close()

  # make a new seizure file of old_results
  resultsfile = "obsLRs." + species + ".txt"
  resname = prefix + "_obsLRs_" + secname + ".tsv"
  archive_resultsfile = results_archive + "/" + resname 
  command = ["cp",resultsfile,archive_resultsfile]
  run_and_report(command,"Unable to copy results file " + resultsfile + " to archive") 
