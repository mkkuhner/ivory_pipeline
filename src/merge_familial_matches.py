# this program takes a set of newly run familial matching results
# called subN/obsLRs.species.txt, where N is subregion number, and
# species is forest for sub0 and sub1 and savannah for all other 
# subregions.  It also takes results from previous runs (on all 
# previously analyzed seizures) which are in its run directory and are 
# called obsLRs.species.N.txt, where N is again the subregion number.

# It proceeds by copying the newly run results to files named
# subN/obsLRs.species.txt_original, and then overwrites the original
# subN/obsLRs.species.txt with a merge of the old and new results.

nsub = 6

import shutil

for subreg in range(0,nsub):
  if subreg < 2:  species = "forest"
  else:  species = "savannah"
  subdir = "sub" + str(subreg)
  oldfile = "obsLRs." + species + "." + str(subreg) + ".txt"
  newfile = subdir + "/" + "obsLRs." + species + ".txt"
  savefile = newfile + "_original"
  shutil.copy2(newfile,savefile
