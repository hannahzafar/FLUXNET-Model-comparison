# =============================================================================
# DATA CONFIGURATION
# =============================================================================
# The datasets used in this repository are note included in this repo but are publicly available.
# 
# Instructions:
#FIX: add the directions to download the dataset
# 2. Update DATASET_PATH below to point to your file

# =============================================================================
import os
from pathlib import Path

# Get the environment variable
NOBACKUP = os.environ['NOBACKUP']  # Will error if not set

MICASA_DATA_PATH = Path(NOBACKUP) / "ghgc" / "micasa" / "micasa-data"
FLUX_DATA_PATH = Path(NOBACKUP) / "ghgc" / "micasa" / "ameriflux-data/"
