
# run familial matching R scripts
mkdir fammatch
cd fammatch
mkdir outdir 
../../../SCAT2 -Z -H2 ../../${1}_conjoint_nohybrids.txt ../../../regionfile.v38b.txt outdir 16
python3 ../../../make_fammatch_incremental.py $1 outdir ~/data/fammatch_inputs ../../../regionfile.v38b.txt
for i in 0 1 2 3 4 5
do
  if [ -d "sub${i}" ]
  then
    echo "Processing in sub${i}"
    if [ -f ONLY_ONE_SAMPLE ]
    then
      echo "Only one sample ever seen in this subregion -- skipping"
    else
      cp ../../../calculate_LRs.R sub${i}/
      cp ../../../LR_functions.R sub${i}/
    fi
  fi
done
echo "Ready to run familial matching (runrscript.sh) in each subregional directory"
