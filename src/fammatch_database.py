# manage the fammatch database 

# move sorting to rout2db.py and make that program overwrite its input.
# check that entries really are sorted in same_sids

# report on how many things you added

from datetime import datetime
now = datetime.now()
datestring = now.strftime("%d/%m/%Y $H:%M:%S")

#################
# classes

class match_entry:
  def __init__(self,header,inputline):
    self.secno = inputline[header.index("secno")]
    self.seizures = []
    self.seizures.append(inputline[header.index("sz1")])
    self.seizures.append(inputline[header.index("sz2")])
    self.sids = []
    self.sids.append(inputline[header.index("s1")])
    self.sids.append(inputline[header.index("s2")])
    # sort the sids, keeping the seizures synchronized
    if self.sids[0] > self.sids[1]:
      print("Expected input to be sorted!")
      # swap:  this looks funny but is idiom
      self.sids[0], self.sids[1] = self.sids[1], self.sids[0]
      self.seizures[0], self.seizures[1] = self.seizures[1], self.seizures[0]
    self.lrs = []
    self.lrs.append(float(inputline[header.index("DM_LR")]))
    self.lrs.append(float(inputline[header.index("PO_LR")]))
    self.lrs.append(float(inputline[header.index("FS_LR")]))
    self.lrs.append(float(inputline[header.index("HS_LR")]))
    self.maxlr = max(self.lrs)
    self.nloci = int(inputline[header.index("nloci")])
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

  def is_significant(cutoff,minloci):
    return self.maxlr >= cutoff and self.nloci >= minloci

  def same_sids(self,other):
    if self.sids == other.sids:  return True
    return False

####

class match_database:
  def __init__(self):
    self.db = []
    self.index = 0
    self.header = None

  def add_entry(self,newentry):
    for oldentry in self.db:
      if oldentry.same_sids(newentry):
        print("Duplicate entry for sids: ",oldentry.sids[0],oldentry.sids[1])
        print("Old entry:")
        print(oldentry)
        print("New entry:")
        print(newentry)
        exit(-1)
    self.db.append(newentry)

  def numentries(self):
    return len(self.db)

  def __iter__(self):
    self.index = 0
    return self

  def __next__(self):
    if self.index == len(self.db):
      raise StopIteration
    self.index += 1
    return self.db[self.index-1]
        
  def __str__(self):
    outputstr = "\t".join(self.header) + "\n"
    for entry in database:
      outputstr += str(entry)
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
          else:
            if self.header != newheader:
              print("**Error:  headers of database files incompatible")
              print("All db files must have identical headers")
              exit(-1)
          continue
        match = match_entry(self.header,line)
      self.add_entry(match)
    except SystemExit:
      raise
    except:
      print("**Error in database file",datafile)
      print("Here is Python's diagnosis of the problem")
      raise

################
# main

import sys, os
import shutil

allowable_argument_numbers = [3,4,7]
if len(sys.argv) not in allowable_argument_numbers:
  print("USAGE: python3 fammatch_database.py database action argument [reportfile cutoff minloci]")
  print("Examples:  database add newdata")
  print("\tdatabase report seizurename reportfile 2.0 13")
  print("\tdatabase remove seizurename")
  print("\tdatabase verify")
  print("If no database exists, the add command will create one")
  exit(-1)

olddatafile = sys.argv[1]
action = sys.argv[2]

# determine what action is being done
legalactions = ["add","report","remove","verify"]
if action not in legalactions:
  print("Unrecognized action ",action)
  exit(-1)

database = match_database()

# check if database exists 
db_exists = os.path.isfile(olddatafile)

# there must be a database already for all operations but "add"
if not db_exists:
  if action == "add":
    print("Creating new database file",olddatafile)
  else:
    print("Database",olddatafile,"does not exist")
    exit(-1)

# VERIFY action; make sure database can be read successfully
if action == "verify":
  database.read_database_file(olddatafile)
  print("Database",olddatafile,"exists and can be read successfully")
  exit(0)

# parse remaining arguments
argument = sys.argv[3]
if len(sys.argv) > 4:
  reportfile = sys.argv[4]
  cutoff = sys.argv[5]
  minloci = sys.argv[6]

# read old database
if db_exists:
  database.read_database_file(olddatafile)

if db_exists and (action == "remove" or action == "add"):
  backupname = olddatafile + "_bak"
  print("**Modifying database file",olddatafile)
  print("Backup will be in", backupname)
  shutil.copyfile(olddatafile,backupname)

# ADD action
if action == "add":
  newdata = argument
  database.read_database_file(newdata)
  outfile = open(olddatafile,"w")
  outfile.write(str(database))
  outfile.close()
  exit(0)

# REPORT action
if action == "report":
  report = open(reportfile,"w")
  report.write("\t".join(database.header) + "\n")
  seizurename = argument
  for entry in database:
    if entry.contains_seizure(seizurename):
      if entry.is_significant(cutoff,minloci):
        report.write(entry)
  report.close()
  exit(0)

# REMOVE action
if action == "remove":
  badseizure = argument
  newdb = match_database()
  numremoved = 0
  for entry in database:
    if not entry.contains_seizure(badseizure):
      newdb.add_entry(entry)
    else:
      numremoved += 1
  database = newdb
  outfile = open(olddatafile,"w")
  outfile.write(str(database))
  outfile.close()
  print("Removed ",numremoved," entries")
  exit(0)
