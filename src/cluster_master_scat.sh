#!/bin/bash

#SBATCH --job-name=UNAME                               # give a unique name
#SBATCH --account=wasser
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=4G
#SBATCH --time=100:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mkkuhner@uw.edu
#SBATCH -o scat.%j.out
#SBATCH -e scat.%j.err
#SBATCH --chdir=LOCALPATH  # set local directory

pwd; hostname; date;

module load gcc/10.2.0

/gscratch/wasser/mkkuhner/scat/SCAT2 -A 1 NUMIND -Z -S SEED -g MAPFILE DATAFILE REGIONFILE outputs 16 100 20 100
