# Check an input microsatellite file for legality

MSAT_NAMES = ["FH67","FH71","FH19","FH129","FH60","FH127","FH126","FH153","FH94","FH48","FH40","FH39","FH103","FH102","S03","S04"]
MSATS = len(MSAT_NAMES)

# functions

def report_error(filename, lineno, error):
  print("Error in",filename,"line",lineno,":  ",error)
  exit(-1)

def legal_msat_value(msat):
  try:
    msat = int(msat)
  except:
    return False
  if msat == -999:  return True
  if 0 < msat <= 300:  return True
  return False

# main

import sys

if len(sys.argv) != 2:
  print("USAGE:  python3 validate_input_file.py infile")
  exit(-1)

# read input file
infilename = sys.argv[1]
infile = open(infilename,"r")
header = infile.readline()
datalines = infile.readlines()
infile.close()

# check header legality:
lineno = 1
header = header.rstrip().split("\t")

if header[0] != "MatchID":
  errormsg = "First entry in header must be MatchID"
  report_error(infilename,lineno,errormsg)

msatnames = header[1:]
num_msats = len(msatnames)
if num_msats != MSATS:
  errormsg = "Number of msat entries in header was " + str(num_msats) + " but should be " + str(MSATS)
  report_error(infilename,lineno,errormsg)
if msatnames != MSAT_NAMES:
  errormsg = "List of microsats in header is incorrect"
  report_error(infilename,lineno,errormsg)

# check entry legality:
sidlines = {}
for line in datalines:
  lineno += 1
  line = line.rstrip().split("\t")
  sid = line[0]
  if sid not in sidlines:
    sidlines[sid] = []
  sidlines[sid].append(lineno)
  msats = line[1:]
  if len(msats) != MSATS:
    errormsg = "Found " + str(len(msats)) + " microsats but expected " + str(MSATS)
    report_error(infilename,lineno,errormsg)
  for msat in msats:
    if not legal_msat_value(msat):
      errormsg = "Illegal msat value " + msat
      report_error(infilename,lineno,errormsg)

# check that each SID present exactly twice
for sid, lines in sidlines.items():
  count = len(lines)
  if count != 2:
    all_lines = [str(x) for x in lines]
    all_lines = ",".join(all_lines)
    if count == 1:
      errormsg = sid + " has " + str(count) + " haplotype but should have 2"
    else:
      errormsg = sid + " has " + str(count) + " haplotypes but should have 2"
    report_error(infilename,all_lines,errormsg)
print("No errors detected")

