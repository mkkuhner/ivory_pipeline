# manage the fammatch database 

# move sorting to rout2db.py and make that program overwrite its input.
# check that entries really are sorted in same_sids

from datetime import datetime
now = datetime.now()
datestring = now.strftime("%d/%m/%Y $H:%M:%S")

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
    return self.maxlr >= cutoff and self.nloci >= minloci

  def same_sids(self,other):
    if self.sids == other.sids:  return True
    return False

####

class match_database:
  def __init__(self,inputfile):
    self.db = []
    self.index = 0
    self.header = None
    self.read_database_file(inputfile)
    assert self.header is not None

  def add_entry(self,inputlist,newheader):
    if newheader != self.header:
      print("**Error:  headers of database files incompatible")
      print("All db files must have identical headers")
      exit(-1)
    newentry = match_entry(self.header,inputlist)
    for oldentry in self.db:
      if oldentry.same_sids(newentry):
        print("Duplicate entry for sids: ",oldentry.sids[0],oldentry.sids[1])
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
          # we do not check if header is the same as before; this will be
          # caught in add_entry 
          continue
        self.add_entry(line,newheader)
    except SystemExit:
      raise
    except:
      print("**Error in database file",datafile)
      print("Here is Python's diagnosis of the problem")
      raise

  def backup_database(self,filename):
    backupname = filename + "_bak"
    print("Modifying database:  backup will be in", backupname)
    shutil.copyfile(filename,backupname)

  def remove_seizure(self,seizurename):
    numremoved = 0
    newdb = []
    for entry in self.db:
      if not entry.contains_seizure(seizurename):
        newdb.append(entry)
      else:
        numremoved += 1
    self.db = newdb
    print("No entries removed for seizure",seizurename,"--is there a typo?")
    return numremoved

  def return_selected_from_seizure(self,seizurename,cutoff,minloci):
    printform = "\t".join(self.header) + "\n"
    numfound = 0
    for entry in self.db:
      if entry.contains_seizure(seizurename):
        numfound += 1
        if entry.is_significant(cutoff,minloci):
          printform += str(entry)
    if numfound == 0:
      print("No information found on seizure",seizurename,"--is there a typo?")
    return printform

  def return_selected(self,cutoff,minloci):
    printform = "\t".join(self.header) + "\n"
    for entry in self.db:
      if entry.is_significant(cutoff,minloci):
        printform += str(entry)
    return printform

################
# functions

def print_usage_statement():
  print("USAGE: python3 fammatch_database.py database action argument [reportfile cutoff minloci]")
  print("Legal actions:  create, verify, add, remove, report")
  print("Examples:  python3 fammatch_database.py database.tsv add newdata.tsv")
  print("\tpython3 fammatch_database.py database.tsv report seizurename reportfile 2.0 13")
  print("\tpython3 fammatch_database.py database.tsv report ALL reportfile 2.0 13")
  print("\tpython3 fammatch_database.py database.tsv remove seizurename")
  print("\tpython3 fammatch_database.py database.tsv verify")
  print("\tpython3 fammatch_database.py database.tsv create newdata.tsv")

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
legalactions = ["add","report","remove","verify","create"]
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
  database = match_database(olddatafile)
  print("Database",olddatafile,"exists and can be read successfully")
  exit(0)

argument = sys.argv[3]

# CREATE action 
if action == "create":
  newdata = argument
  database = match_database(newdata)
  outfile = open(olddatafile,"w")
  outfile.write(str(database))
  outfile.close()
  print("Created database",olddatafile,"based on",newdata)
  exit(0)

# ADD action
if action == "add":
  database = match_database(olddatafile)
  database.backup_database(olddatafile)
  newdata = argument
  database.read_database_file(newdata)
  outfile = open(olddatafile,"w")
  outfile.write(str(database))
  outfile.close()
  print("Added",newdata,"to",olddatafile)
  exit(0)

# REPORT action
if action == "report":
  database = match_database(olddatafile)
  reportfile = sys.argv[4]
  cutoff = float(sys.argv[5])
  minloci = int(sys.argv[6])
  report = open(reportfile,"w")
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
  database = match_database(olddatafile)
  database.backup_database(olddatafile)
  badseizure = argument
  numremoved = database.remove_seizure(badseizure)
  outfile = open(olddatafile,"w")
  outfile.write(str(database))
  outfile.close()
  print("Removed ",numremoved," entries from database",olddatafile)
  exit(0)
