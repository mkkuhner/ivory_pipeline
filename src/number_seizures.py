## number_seizures.py
#  takes a file with seizure name, number, and optional additional columns
#  returns a file where the seizures are renumbered chronologically and the
#  additional columns are simply carried

# ties are broken alphabetically on seizure name 

# we assume that years are either 1950-1999 or 2000-2049, because we have to
# disambiguate 2 digit years.  We are in deep trouble if we ever get a seizure from,
# say, 1920.

##################
# functions

def get_month_year(seizurename):
  # assumes all seizure names in form ISO_MM_YY_nnt 
  date = seizurename.split("_")[1]
  stuff = date.split("-")
  month = int(stuff[0])
  year = int(stuff[1])
  if year > 30:  year = 1900 + year
  else:  year = 2000 + year
  return month,year

##################
# main
import sys
if len(sys.argv) != 3:
  print("USAGE:  python3 number_seizures.py infile outfile")
  exit(-1)

infile = sys.argv[1]
outfile = sys.argv[2]

seizures = []
for line in open(infile,"r"):
  line = line.rstrip().split()
  seizure = line[0]
  additional = line[2:]
  month,year = get_month_year(seizure)
  seizures.append([year,month,seizure,additional])

seizures.sort()

outfile = open(outfile,"w")
count = 1
for entry in seizures:
  year,month,seizure,additional = entry
  outline = [seizure,str(count)] + additional
  outline = "\t".join(outline) + "\n"
  outfile.write(outline)
  count += 1
outfile.close()
