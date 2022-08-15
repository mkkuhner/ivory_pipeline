# consolidate scat results for each elephant into one file
import sys
if len(sys.argv) != 2:
  print("USAGE:  consolidate_scat.py prefix")
  print("run it in main seizure directory")
  print("results will be in consolidated_data directory off seizure directory")
  exit(-1)

prefix = sys.argv[1]
import os
basedir = prefix + "/"

# diagnose species
speciesdirs = []
if os.path.isdir(basedir + "nforest"):
  speciesdirs.append("nforest/")
if os.path.isdir(basedir + "nsavannah"):
  speciesdirs.append("nsavannah/")

datadict = {}
datadirs = [str(x) + "/" for x in range(1,10)]
for species in speciesdirs:
  print(species)
  for datadir in datadirs:
    for root,dirs,files in os.walk(basedir + species + datadir + "outputs/"):
      for file in files:
        if file.startswith("Output"):  continue
        if file not in datadict:
          datadict[file] = []
        # we delete the first 100 lines as burnin and the last line, which is acceptance rate
        filepath = basedir + species + datadir + "outputs/" + file
        data = open(filepath).readlines()
        usedata = data[100:-1]
        if len(usedata) != 100:
          print(filepath,len(usedata))
        datadict[file] += usedata

# check that everything is in order
for key in datadict:
  if len(datadict[key]) != 900:
    print(key,len(datadict[key]))
  assert len(datadict[key]) == 900

# write consolidated files
outdir = basedir + "consolidated_scat/"
if not os.path.isdir(outdir):
  os.mkdir(outdir)
for key in datadict:
  outfile = outdir + key
  outfile = open(outfile,"w")
  for line in datadict[key]:
    outfile.write(line)
  outfile.close()

print("Wrote",len(datadict),"samples")
