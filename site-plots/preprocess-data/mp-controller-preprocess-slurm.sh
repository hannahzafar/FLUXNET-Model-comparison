#!/usr/bin/env bash
#SBATCH --job-name=multi_script_run
#SBATCH --output=slurm-%j.out      # Capture both stdout and stderr
#SBATCH --error=slurm-%j.out       # Same log file for errors
#SBATCH --account=s1460
#SBATCH --time=2:30:00

# Preprocess all sites via parallel processing on a compute node

pixi run $NOBACKUP/ghgc/micasa/AmeriFlux-analysis/mp-controller-preprocessing.py
