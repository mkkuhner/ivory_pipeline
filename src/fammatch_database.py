# manage the fammatch database 

# This program backs up the database and will restore from backups if
# it seems to have failed

# NOTE:  The input "cutoff" value for reports is in log scale.  The
# LRs are NOT, so we un-log this before use.  If you do not want to use
# a cutoff, pass "None" for this parameter.  (Not zero!)

from datetime import datetime
now = datetime.now()
datestring = now.strftime("%d/%m/%Y $H:%M:%S")
import math

#################
# classes

class match_entry:
  def __init__(self,header,inputlist):
    self.secno = inputlist[header.index("secno")]
    self.seizures = []
    self.seizures.append(inputlist[header.index("sz1")])
    self.seizures.append(inputlist[header.index("sz2")])
    self.sids = []
    self.sids.append(inputlist[header.index("s1")])
    self.sids.append(inputlist[header.index("s2")])
    # sort the sids, keeping the seizures synchronized
    if self.sids[0] > self.sids[1]:
      print("Expected input to be sorted!")
      # swap:  this looks funny but is idiom
      self.sids[0], self.sids[1] = self.sids[1], self.sids[0]
      self.seizures[0], self.seizures[1] = self.seizures[1], self.seizures[0]
    self.lrs = []
    self.lrs.append(float(inputlist[header.index("DM_LR")]))
    self.lrs.append(float(inputlist[header.index("PO_LR")]))
    self.lrs.append(float(inputlist[header.index("FS_LR")]))
    self.lrs.append(float(inputlist[header.index("HS_LR")]))
    self.maxlr = max(self.lrs)
    self.nloci = int(inputlist[header.index("nloci")])
    self.date = datestring

  def __str__(self):
    returnlist = []
    returnlist.append(self.secno)
    returnlist += self.seizures
    returnlist += self.sids
    returnlist += [str(x) for x in self.lrs]
    # we deliberately do not write maxlr as it is not part of the file format
    returnlist.append(str(self.nloci))
    returnval = "\t".join(returnlist) + "\n"
    return returnval

  def contains_seizure(self,seizurename):
    return seizurename in self.seizures

  def is_significant(self,cutoff,minloci):
    if cutoff is not None:
      return self.maxlr >= cutoff and self.nloci >= minloci
    else:
      return self.nloci >= minloci

  def rename_seizure(self,oldname,newname):
    if self.seizures[0] == oldname:
      self.seizures[0] = newname  
    if self.seizures[1] == oldname:
      self.seizures[1] = newname  

####

class match_database:
  def __init__(self,inputfile):
    self.db = {}    # dict makes for faster searches
    self.index = 0
    self.header = None
    self.read_database_file(inputfile)
    if self.header is None:
      msg = "Database file does not have appropriate header"
      raise RuntimeError(msg)

  def add_entry(self,inputlist,newheader):
    if newheader != self.header:
      msg = "All db files must have identical headers"
      raise RuntimeError(msg)
    try:
      newentry = match_entry(self.header,inputlist)
    except:
      msg = "Could not create database entry:  malformed input?"
      raise RuntimeError(msg)
    key = tuple(newentry.sids)
    if key in self.db:
      msg = "Duplicate entry for sids: " + newentry.sids[0] + " " + newentry.sids[1]
      raise RuntimeError(msg)
    self.db[key] = newentry

  def numentries(self):
    return len(self.db)

  def __iter__(self):
    return iter(self.db.values())

  def __str__(self):
    outputstr = "\t".join(self.header) + "\n"
    for key, value in self.db.items():
      outputstr += str(value)
    return outputstr

  def read_database_file(self, datafile):
    first = True
    try:
      for line in open(datafile,"r"):
        line = line.rstrip().split("\t")
        if first:
          first = False
          newheader = line
          if self.header is None:
            self.header = newheader
          # we do not check if header is the same as before; this will be
          # caught in add_entry 
          continue
        self.add_entry(line,newheader)
    except SystemExit:
      msg = "Exit called unexpectedly"
      raise RuntimeError(msg)
    except RuntimeError as e:
      print("RuntimeError:",e)
    except:
      msg = "Error in reading database file " + datafile
      raise RuntimeError(msg)

  def remove_seizure(self,seizurename):
    numremoved = 0
    newdb = {}
    for key,value in self.db.items():
      if not value.contains_seizure(seizurename):
        newdb[key] = value
      else:
        numremoved += 1
    self.db = newdb
    if numremoved == 0:
      print("No entries removed for seizure",seizurename,"--is there a typo?")
    return numremoved

  def return_selected_from_seizure(self,seizurename,cutoff,minloci):
    printform = "\t".join(self.header) + "\n"
    numfound = 0
    for key,value in self.db.items():
      if value.contains_seizure(seizurename):
        numfound += 1
        if value.is_significant(cutoff,minloci):
          printform += str(value)
    if numfound == 0:
      print("No information found on seizure",seizurename,"--is there a typo?")
    return printform

  def return_selected(self,cutoff,minloci):
    printform = "\t".join(self.header) + "\n"
    for key,value in self.db.items():
      if value.is_significant(cutoff,minloci):
        printform += str(value)
    return printform

  def write_database(self,outfilename):
    try:
      outfile = open(outfilename,"w")
      outfile.write(str(self))
      outfile.close()
    except:
      msg = "Unable to write database to filename " + outfilename
      raise RuntimeError(msg)

  def rename_seizure(self,oldname,newname):
    for key in self.db:
      self.db[key].rename_seizure(oldname,newname)


################
# functions

def print_usage_statement():
  print("USAGE: python3 fammatch_database.py database action argument [reportfile cutoff minloci]")
  print("Legal actions:  create, verify, add, remove, report, rename")
  print("Examples:  python3 fammatch_database.py database.tsv add newdata.tsv")
  print("\tpython3 fammatch_database.py database.tsv report seizurename reportfile 2.0 13")
  print("\tpython3 fammatch_database.py database.tsv report ALL reportfile 2.0 13")
  print("\tpython3 fammatch_database.py database.tsv remove seizurename")
  print("\tpython3 fammatch_database.py database.tsv verify")
  print("\tpython3 fammatch_database.py database.tsv create newdata.tsv")
  print("\tpython3 fammatch_database.py database.tsv rename oldname newname")

def backup_database(filename):
  backupname = filename + "_bak"
  print("Modifying database:  backup will be in", backupname)
  try:
    shutil.copyfile(filename,backupname)
  except:
    msg = "Could not back up database"
    raise RuntimeError(msg)

def restore_from_backup(filename):
  backupname = filename + "_bak"
  try:
    shutil.copyfile(backupname,filename)
  except:
    print("Could not restore database from backups")
    print("DANGER:  database may be corrupt!")
    exit(-1)
  else:
    print("Database restored from backups")

def explain_and_abend(e):
  print(e)
  exit(-1)

################
# main

import sys, os
import shutil

numargs = len(sys.argv)

if numargs < 3:
  print_usage_statement()
  exit(-1)

olddatafile = sys.argv[1]
action = sys.argv[2]

# determine what action is being done
legalactions = ["add","report","remove","verify","create","rename"]
if action not in legalactions:
  print("Unrecognized action ",action)
  exit(-1)

# check if all needed arguments present
argdict = {}
argdict["add"] = 4
argdict["report"] = 7
argdict["remove"] = 4
argdict["verify"] = 3
argdict["create"] = 4
argdict["rename"] = 5

if numargs != argdict[action]:
  print(action,"command requires",argdict[action],"arguments but received",numargs)
  exit(-1)


# check if database exists 
db_exists = os.path.isfile(olddatafile)

# there must be a database already for all operations but "create"
if not db_exists:
  if action != "create":
    print("Database",olddatafile,"does not exist")
    print("To create a new database use 'create'")
    exit(-1)
else:
  if action == "create":
    print("Database file",olddatafile,"already exists")
    print("To add to it, use 'add'")
    exit(-1)

# VERIFY action; make sure database can be read successfully
if action == "verify":
  try:
    database = match_database(olddatafile)
  except RuntimeError as e:
    explain_and_abend(e)
  else:
    print("Database",olddatafile,"exists and can be read successfully")
    exit(0)

argument = sys.argv[3]

# CREATE action 
if action == "create":
  try:
    newdata = argument
    database = match_database(newdata)
  except RuntimeError as e:
    explain_and_abend(e)
  else:
    try:
      database.write_database(olddatafile)
    except RuntimeError as e:
      explain_and_abend(e)
    else:
      print("Created database",olddatafile,"based on",newdata)
      exit(0)

# ADD action
if action == "add":
  backup_database(olddatafile)

  # do non-writing operations; abend if failure
  try:
    database = match_database(olddatafile)
    newdata = argument
    database.read_database_file(newdata)
  except RuntimeError as e:
    explain_and_abend(e)

  # do writing operations; restore and abend if failure
  try:
    database.write_database(olddatafile)
  except RuntimeError as e:
    restore_from_backup(olddatafile)
    explain_and_abend(e)
  else:
    print("Added",newdata,"to",olddatafile)
    exit(0)

# REPORT action
if action == "report":
  # no backup as this does not modify database
  # read database
  try:
    database = match_database(olddatafile)
  except RuntimeError as e:
    explain_and_abend(e)

  # write report
  try:
    reportfile = sys.argv[4]
    report = open(reportfile,"w")
  except:
    print("Unable to open report file")
    exit(-1)
  cutoff = sys.argv[5]
  if cutoff == "None": 
     cutoff = None
  else:
    cutoff = 10**float(cutoff)  # it is given in log scale, need non-log here
  minloci = int(sys.argv[6])
  seizurename = argument
  if seizurename == "ALL":
    report.write(database.return_selected(cutoff,minloci))
  else:
    report.write(database.return_selected_from_seizure(seizurename,cutoff,minloci))
  report.close()
  print("Report written on seizure",argument,"to file",reportfile)
  exit(0)

# REMOVE action
if action == "remove":
  # make backup
  backup_database(olddatafile)

  # non-writing operations; abend on failure
  try:
    database = match_database(olddatafile)
    badseizure = argument
    numremoved = database.remove_seizure(badseizure)
    outfile = open(olddatafile,"w")
  except RuntimeError as e:
    explain_and_abend(e)

  # writing operations; restore and abend on failure
  try:
    outfile.write(str(database))
    outfile.close()
  except RuntimeError as e:
    restore_from_backup(olddatafile)
    explain_and_abend(e)

  print("Removed ",numremoved," entries from database",olddatafile)
  exit(0)

# RENAME action
if action == "rename":
  # make backup
  backup_database(olddatafile)

  # non-writing operations; abend on failure
  try:
    database = match_database(olddatafile)
    oldname = sys.argv[3]
    newname = sys.argv[4]
    outfile = open(olddatafile,"w")
  except RuntimeError as e:
    explain_and_abend(e)

  # writing operations:  restore and abend on failure
  try:
    database.rename_seizure(oldname,newname)
    outfile.write(str(database))
    outfile.close()
  except RuntimeError as e:
    restore_from_backup(olddatafile)
    explain_and_abend(e)
  print("Seizure",oldname,"renamed",newname,"successfully")
  exit(0)
