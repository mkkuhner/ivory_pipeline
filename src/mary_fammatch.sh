# Set up and run familial matching R scripts

# This script is meant to be run in the parent directory of all seizures:  it
# takes PREFIX (the name of the seizure to be analyzed) as its argument.
# It will create a new directory PREFIX/fammatch for its work and will spawn
# jobs to run familial matching in each of the subN directories as needed.

# WARNING:  it will terminate before those jobs finish!  You will need
# to make sure they have finished before doing anything downstream of them.
# (That's why this script stops where it does....)

#### CHANGE THESE LINES FOR SPECIFIC MACHINE

# ivory pipeline main directory (not /src)
pipedir="/home/mkkuhner/scat/ivory_pipeline"

# reference data
datadir="/home/mkkuhner/data"

# SCAT /src
scatdir="/home/mkkuhner/scat/scat-master/src"

# VORONOI /src
vordir="/home/mkkuhner/scat/voronoi-master/src"

####

cd $1
rm -rf fammatch
mkdir fammatch
cd fammatch
for s in forest savannah
do 
  if [ -d ../n${s} ]
  then
    mkdir outdir_${s}
    echo "running in ${1} for ${s}"
    ${scatdir}/SCAT2 -Z -H2 ../${1}_${s}.txt ${datadir}/zones_39_${s}.txt outdir_${s} 16
  fi
done
python3 ${pipedir}/src/make_fammatch_incremental.py $1 outdir ${datadir}/fammatch_inputs ${datadir}/zones_39
for i in 0 1 2 3 4 5
do
  if [ -d "sub${i}" ]
  then
    echo "Processing in sub${i}"
    if [ -f ONLY_ONE_SAMPLE ]
    then
      echo "Only one sample ever seen in this subregion -- skipping"
    else
      cp ${pipedir}/src/calculate_LRs.R sub${i}/
      cp ${pipedir}/src/LR_functions.R sub${i}/
      cd sub${i}
      source runrscript.sh &
      cd ..
    fi
  fi
done
cd ../..
echo "Script completed for $1"
echo "Warning:  familial matching runs may be ongoing!"
