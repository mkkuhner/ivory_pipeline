# assess accuracy of SCAT and VORONOI/CLUST results on a data set made of 
# known location reference  

# scat is scored as median lat/long
# clust and voronoi are scored based on indprobs/printprobs:
# mean lat/long weighted by probability

#############################################################################
# functions

def makerange(entries):
  assert len(entries) == 2
  lat = entries[0]
  long = entries[1]
  if lat.endswith(","):
    lat = lat[:-1]
  lat = float(lat)
  long = float(long)
  return (lat,long)

def read_summary_file(infile):
  # we will score whatever we find in this summary file, which
  # might be some combo of scat, voronoi, or clust results
  scores = {}
  tags = {}
  for line in open(infile,"r"):
    line = line.rstrip().split("\t")
    if line[0] == "SID":   # header 
      # discard first two entries SID and species
      # assume the rest are tags for results
      tags = {}
      for tag in line[2:]:
        tags[tag] = line.index(tag)
        scores[tag] = []
      continue
    sid = line[0]
    species = line[1]
    for tag, index in tags.items():
      latlong = line[index].split(",")
      latlong = [float(x.strip()) for x in latlong]
      scores[tag].append([sid,species,latlong])

  return scores

##############################################################################
# main

import sys
import ivory_lib as iv
import statistics

legal_species = ["savannah","forest"]

if len(sys.argv) != 5:
  print("USAGE:  python score_clust_sims.py prefix species cluster_zone ivory_paths")
  exit(-1)
prefix = sys.argv[1]
species = sys.argv[2]
centerreg = sys.argv[3]
if species not in legal_species:
  print("Unknown species", species)
  exit(-1)
pathsfile = sys.argv[4]
pathdir = iv.readivorypath(pathsfile)

# read zones file
zonedir, zoneprefix = pathdir["zones_prefix"]
zonefile = zonedir + zoneprefix + "_" + species + ".txt"
zonedata = {}
for line in open(zonefile,"r"):
  line = line.rstrip().split()
  zone = line[1]
  lat = float(line[3])
  long = float(line[4])
  zonedata[zone] = (lat,long)


elephants = []
for line in open(prefix + "_clust_names.txt","r"):
  line = line.rstrip()
  elephants.append(line)

## read sim input file to find which elephants were used
#elephants = set()    # so we can add twice without getting duplicates
#for line in open(simfile,"r"):
#  line = line.rstrip().split()
#  sid, zone = line[0:2]
#  if zone == "-1":  # "unknown" elephant
#    elephants.add(sid)
#  else:
#    break # no more unknowns after first known

#elephants = list(elephants)

centerlatlong = zonedata[centerreg]
print("zone center was",centerreg,"at latlong",centerlatlong[0],centerlatlong[1])

# find out what zone the elephant was in (shame we lost that info!)
print("getting locdata")
locdata = {}
refdir, refprefix = pathdir["reference_prefix"]
reffile = refdir + refprefix + "_known.txt"

for line in open(reffile,"r"):
  line = line.rstrip().split()
  sid = line[0]
  if sid not in elephants:  continue
  if sid in locdata:  continue   # second entry for this sid, not needed
  zone = line[1]
  locdata[sid] = zonedata[zone]

# read summary file and score
resultfile = "reports/" + prefix + "_point_estimates.tsv" 
scores = read_summary_file(resultfile)

outfile = "reports/" + prefix + "_scoring.tsv"
outfile = open(outfile,"w")
header = ["sid","true location"]
results_by_sid = {}
dists_by_tag = {}
taglist = list(scores.keys())    # for consistent ordering
newtaglist = []
for tag in taglist:
  if "best" not in tag:
    newtaglist.append(tag)
taglist = newtaglist
for tag in taglist:
  dists_by_tag[tag] = []
  header.append(tag)
  for entry in scores[tag]:
    sid = entry[0]
    true_latlong = locdata[sid]
    if sid not in results_by_sid:
      results_by_sid[sid] = [sid]
      latlongprint = str(true_latlong[0]) + ", " + str(true_latlong[1])
      results_by_sid[sid].append(latlongprint)
    my_species = entry[1]
    assert my_species == species
    latlong = entry[2]
    mydist = iv.dist_between(latlong, true_latlong)
    results_by_sid[sid].append(str(round(mydist,4)))
    dists_by_tag[tag].append(mydist)

# write the report
header = "\t".join(header) + "\n"
outfile.write(header)
for sid in results_by_sid:
  printline = "\t".join(results_by_sid[sid]) + "\n"
  outfile.write(printline)

outline = ["\nMean","---"]
for tag in taglist:
  outline.append(str(round(statistics.mean(dists_by_tag[tag]),4)))
outline = "\t".join(outline) + "\n"
outfile.write(outline)

outfile.close()
