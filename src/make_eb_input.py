import sys

if len(sys.argv) != 5 and len(sys.argv) != 6:
  print("USAGE: python make_eb_input.py structure_outfile refdata.txt PREFIX dropout.txt")
  print("For a ref-only run, PREFIX is the reference prefix, and add the flag 'reference'")
  print("at the end of the argument list.")
  exit()

refonly = False
if len(sys.argv) == 6:
  if not sys.argv[5] == "reference":
    print("For a reference-only run, use 'reference' as the last argument")
  else:
    refonly = True
  

# NOTE:  Structure truncates names to 11 characters.  This code tests if all
# names will still be unique under truncation, and then uses the truncated names
# to cross-reference Structure output.

structdata = sys.argv[1]
refdata = sys.argv[2]
prefix = sys.argv[3]
if not refonly:
  newdata = prefix+"_unknowns.txt"
dropdata = sys.argv[4]

####
# read reference data
refsids = []
testsids = []
reflines = open(refdata,"r").readlines()
indcount = 0
for line in reflines:
  indcount += 1
  line = line.rstrip().split()
  sid = line[0]
  testsid = sid[0:11]
  if testsid not in refsids:
    refsids.append(testsid)
print("Read",len(refsids),"known location individuals")

if "CH0878" not in refsids:
  print("Elephant CH0878 was not present in the reference data set")
  print("make_eb_input.py must be modified to use a different diagnostic")
  print("savannah elephant")
  print("\nprocess FAILED")
  exit()

####
# read new data
if not refonly:
  newsids = []
  newlines = open(newdata,"r").readlines()
  for line in newlines:
    line = line.rstrip().split()
    sid = line[0]
    if sid not in newsids:
      newsids.append(sid)
  print("Read",len(newsids),"unknown location individuals")

#####
# read structure input
structlines = open(sys.argv[1],"r").readlines()

# skip to part of file with data for R script
index = 0
while structlines[index] != "Inferred ancestry of individuals:\n":
  index += 1

# skip header
index += 2

flipprobs = False 
diagnosticfound = False
probs = []
for line in structlines[index:]:

  # a blank line means we are done
  if line == "\n":
    break

  line = line.rstrip().split()
  sid = line[1]
  if sid not in refsids:
    print("Failed to find",sid,"in reference")
    exit(-1)
  p1 = line[-2]
  p2 = line[-1]

  if sid == "CH0878":
    diagnosticfound = True
    if float(p2) > float(p1):
      flipprobs = True

  probs.append([p1,p2,])

print("Read",len(probs),"Structure entries")
assert len(probs) == len(refsids)

if not diagnosticfound:
  print("Elephant CH0878 was not in the structure results.")
  print("Either another diagnostic savannah elephant must be chosen")
  print("and make_eb_input.py changed to reflect that choice, or")
  print("structure must be run on a reference dataset that includes")
  print("elephant CH0878 and the resulting structure input passed as")
  print("the structure_outfile to make_eb_input.py")
  print("\nprocess FAILED")
  exit()

if flipprobs:
  newprobs = []
  for elem in probs:
    newprobs.append([elem[1],elem[0],])
  probs = newprobs

ancestryprops_name = prefix+"_ancestryprops.txt"

outfile = open(ancestryprops_name,"w")
if not refonly:
  for sid in newsids:
    outline = "0.500 0.500\n"
    outfile.write(outline)

for prob in probs:
  outline = prob[0] + " " + prob[1] + "\n"
  outfile.write(outline)

outfile.close()

print("Wrote output to file",ancestryprops_name)

# write the ebhybrid input file
if refonly:
  ebhybrid_infilename = prefix+"_known.txt"
else:
  ebhybrid_infilename = prefix+"_plus_ref.txt"
outfile = open(ebhybrid_infilename,"w")
if not refonly:
  for line in newlines:
    outfile.write(line)
for line in reflines:
  outfile.write(line)
outfile.close()

#edit the R script
import os.path
eblines = []
if os.path.exists("ebscript_template.R"):
  scriptlines = open("ebscript_template.R","r").readlines()
  found = 0
  for line in scriptlines[:-2]:
    if "GENOTYPES" in line:
      line = line.replace("GENOTYPES",ebhybrid_infilename)
      found += 1
    if "ANCESTRYPROPS" in line:
      line = line.replace("ANCESTRYPROPS",ancestryprops_name)
      found += 1
    if "DROPOUT" in line:
      line = line.replace("DROPOUT",dropdata)
      found += 1
    eblines.append(line) 
  if found != 3:
    print("Expected 3 replacements in ebscript_template.R but found",found)
    exit(-1)
  hybtname = prefix+"_hybt"
  hpsname = prefix+"_HPs"
  eblines.append('writeResults2files("'+hybtname+'",hybt$posteriors)\n')
  eblines.append('writeResults2files("'+hpsname+'",HPs)\n')
  outfile = open("ebscript.R","w")
  for line in eblines:
    outfile.write(line)
  outfile.close()
else:
  print("Could not find file ebscript_template.R.  No changes to R-script were made.")

