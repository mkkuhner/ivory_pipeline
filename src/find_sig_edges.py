# find all edges with weight >= 1.0 in seizure_edges.csv and write to
# sig_seizure_edges.csv

outfile = open("sig_seizure_edges.csv","w")

for line in open("seizure_edges.csv","r"):
  line = line.rstrip().split(",")
  if line[0] == "Seizure1":  continue   # skip header
  s1, s2, score = line
  if float(score) < 1.0:  continue
  outline = [s1,s2,score]
  outline = ",".join(outline) + "\n"
  outfile.write(outline)

outfile.close()

