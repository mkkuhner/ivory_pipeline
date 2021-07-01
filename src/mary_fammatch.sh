# Set up and run familial matching R scripts

# This script is meant to be run in the parent directory of all seizures:  it
# takes PREFIX (the name of the seizure to be analyzed) as its argument.
# It will create a new directory PREFIX/fammatch for its work and will spawn
# jobs to run familial matching in each of the subN directories as needed.
# WARNING:  it can and will terminate before those jobs finish!  You will need
# to make sure they have finished before doing anything downstream of them.
# (That's why this script stops where it does....)

cd $1
mkdir fammatch
cd fammatch
mkdir outdir 
#echo "WARNING:  NOT RUNNING SCAT!"
../../SCAT2 -Z -H2 ../${1}_conjoint_nohybrids.txt ../../regionfile.v38b.txt outdir 16
python3 ../../make_fammatch_incremental.py $1 outdir ~/data/fammatch_inputs ../../regionfile.v38b.txt
for i in 0 1 2 3 4 5
do
  if [ -d "sub${i}" ]
  then
    echo "Processing in sub${i}"
    if [ -f ONLY_ONE_SAMPLE ]
    then
      echo "Only one sample ever seen in this subregion -- skipping"
    else
      cp ../../calculate_LRs.R sub${i}/
      cp ../../LR_functions.R sub${i}/
      cd sub${i}
      source runrscript.sh &
      cd ..
    fi
  fi
done
cd ../..
echo "Script completed for $1"
echo "Warning:  familial matching runs may be ongoing!"
