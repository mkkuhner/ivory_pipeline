# This program reads voronoiin.txt, deduces which scat-output files
# (named 000r etc.) will be present in the directory where it is run,
# and deletes them all.  Use it to clean up after a Voronoi run, to
# save space and clutter.  If you did this by mistake, you can regenerate
# these files by rerunning scat2voronoi.py.

import os

tags = ["r","s","t","u","v","w","x","y","z"]

vlines = open("voronoiin.txt","r").readlines()
assert len(vlines) == 1
vlines = vlines[0]
vlines = vlines.rstrip().split()
numentries = vlines[0]
entries = vlines[1:]
assert len(entries) == int(numentries)
files_to_delete =[]
for entry in entries:
  entryno = entry
  if len(entryno) == 1:
    entryno = "00" + entryno
  if len(entryno) == 2:
    entryno = "0" + entryno
  for tag in tags:
    files_to_delete.append(entryno+tag)

command = "rm -f "
for ftd in files_to_delete:
  os.system(command + ftd)

print("Deleted all remnant Voronoi input files")
