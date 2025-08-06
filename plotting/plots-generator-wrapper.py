#!/usr/bin/env python
# Wrapper script to run plots-generator.py for all the sites in the Fluxnet list
#FIX: ???# (without multiprocessing, not necessary due to performance)

# Import config variables and functions
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FLUX_METADATA

# Import other modules
import pandas as pd
import importlib

# Import workaround for file with dashes in name
mp_controller = importlib.import_module("mp-controller-preprocessing")
# from mp_controller import run_py_script


if __name__ == "__main__":
    # Import/format the list of paths
    ameriflux_meta = pd.read_csv(FLUX_METADATA, sep="\t")
    fluxnet_meta = ameriflux_meta.loc[
        ameriflux_meta["AmeriFlux FLUXNET Data"] == "Yes"
    ]  # use FLUXNET only
    fluxnet_list = fluxnet_meta["Site ID"].to_list()

    script = "plots-generator.py"

    for fluxnet_item in fluxnet_list:
        mp_controller.run_py_script(script, fluxnet_item)
