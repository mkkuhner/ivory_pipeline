#!/bin/bash

#SBATCH --job-name=UNAME                               # give a unique name
#SBATCH --account=wasser
#SBATCH --partition=wasser
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=4G
#SBATCH --time=720:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mkkuhner@uw.edu
#SBATCH -o CIVscat.%j.out
#SBATCH -e CIVscat.%j.err
#SBATCH --chdir=LOCALPATH  # set local directory

pwd; hostname; date;

../scat2.2 -A 1 NUMIND -Z -S SEED -g MAPFILE DATAFILE REGIONFILE outputs 16 100 20 100
