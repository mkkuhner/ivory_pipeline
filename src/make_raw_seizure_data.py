# NOTE:  python3 program!

# this program reads the master ivory database and a spreadsheet of names
# and writes one file per (possibly merged) seizure based on rules from
# Sam Wasser 2020/11/30.

# it does NOT check for 10+ msats; that will be done downstream.  It writes
# individual scat-style files, minus the region column (that is, 17 entries per line,
# two lines per sample)

# this function carries out renaming of groupings that lack a seizure number
# it returns False as its first return value if that grouping is not to be used
# based on information from Sam Wasser 11/30/2020

def get_correct_seizure_name(inname):
  inname = inname.split()
  inname = "".join(inname)
  str1="03.Bone2008"
  str2="07.DRC_tissue_2012(G2012)"
  str3="37.SSD_06-16_stkp(SS.A2016)"
  if inname == str1:
    return False,"Bone_2008"
  if inname == str2:
    return True,"DRC_tissue_2012"
  if inname == str3:
    return True,"SSF_06-16_stkp"
  return False, "UNKNOWN"

def mergename(name):
  if name == "PHL_S1_1996" or name == "PHL_S2_1997":
    return "PHL_S1-2"
  if name == "PHL_S7_2009" or name == "PHL_S8_2009":
    return "PHL_S7-8"
  if name == "USA_07-17_2.0tA" or name == "USA_07-17_2.0tB":
    return name[:-1]
  return name

import sys
import csv

if len(sys.argv) != 4:
  print("USAGE:  python3 make_raw_seizure_data.py ivoryfile.csv namefile.csv outdir")
  exit(-1)

ivoryfile = sys.argv[1]
namefile = sys.argv[2]
outdir = sys.argv[3]

# read the name file
seizureno_to_name = {}

# make name dictionary, including merges
with open(namefile,newline="") as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    if line[0].startswith("Processing"):
      lineid_index = 0
      labid_index = line.index("Lab ID")
      seizure_index = line.index("Seizure #")
      samname_index = line.index("Revised Name (Sam)")
      continue
    lineid = line[lineid_index]
    labid = line[labid_index]
    seizureno = line[seizure_index]
    samname = line[samname_index]
    # revise the name to our standards
    nameparts = [] 
    newpart = ""
    for c in samname:
      if c == "," or c == " ":
        if newpart != "": 
          nameparts.append(newpart)
          newpart = ""
      else:
        newpart = newpart + c
    if newpart != "":
      nameparts.append(newpart)
    samname = "_".join(nameparts)
    samname = mergename(samname)
    if seizureno != "":
      seizureno_to_name[seizureno] = samname

# read the ivory master file and parse out entries into dictionary by seizure ID
sdat = {}
with open(ivoryfile,newline="") as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    if line[0].startswith("Seizure"):  
      header = line
      matchindex = header.index("Match ID")
      seizureindex = header.index("Seizure #")
      sfileindex = header.index("Seizure file name file associated")
      firstmsat = header.index("FH67")
      lastmsat = firstmsat+32
      continue
    seizureid = line[seizureindex]
    if seizureid.isnumeric():
      samname = seizureno_to_name[seizureid]
    else:    # unnumbered seizure
      sfile = line[sfileindex]
      if sfile == "":  print(line)
      status,samname = get_correct_seizure_name(sfile)
      if status == False:  continue
    samname = mergename(samname)
    sid = line[matchindex]
    if samname not in sdat:
      sdat[samname] = {}
    sdat[samname][sid] = line

printnames = list(sdat.keys())
printnames.sort()
for samname in printnames:
  print(samname,len(sdat[samname]))
      
# make individual seizure data files

if outdir[-1] != "/":
  outdir = outdir + "/"
for samname in sdat:
  outfilename = outdir + samname + "_raw.tsv"
  outfile = open(outfilename,"w")
  outline = "Sample\t"
  msatnames = header[firstmsat:lastmsat:2] 
  outline += "\t".join(msatnames)
  outline += "\n"
  outfile.write(outline)
  for sid in sdat[samname]:
    data = sdat[samname][sid][firstmsat:lastmsat]
    outline1 = sid 
    outline2 = sid 
    odd = True
    for m in data:
      if m == "":  m = "-999"
      if odd:
        outline1 += "\t" + m
      else:
        outline2 += "\t" + m
      odd = not odd
    outline1 += "\n"
    outline2 += "\n"
    outfile.write(outline1)
    outfile.write(outline2)
  outfile.close()

