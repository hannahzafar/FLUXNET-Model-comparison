#!/usr/bin/env bash
#SBATCH --account=s1460
#SBATCH --time=1:30:00
# Preprocess a single site on compute node with pixi


pixi run $NOBACKUP/ghgc/micasa/FLUXNET-Model-comparison/site-plots/preprocess-data/data-preprocessing.py AR-TF1 
