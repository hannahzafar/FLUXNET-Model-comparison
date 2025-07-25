#!/usr/bin/env python
# Script to control multiprocessing for data-preprocessing.py

# Import config variables
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FLUX_METADATA

# Import other modules
import pandas as pd
import subprocess
import multiprocessing
from functools import partial


def run_py_script(script, arg):
    """
    This function runs a python script with one argument via subprocess
    and returns a subprocess error if it occurs
    """
    cmd = ["python", script, arg]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )  # check=True will crash if error
        print(result.stdout.strip())
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return f"FAILED: {arg}"


def run_multiprocessing(script, arg_list):
    """
    This function runs run_py_script over a list of input arguments via multiprocessing
    """
    run_script_with_arg = partial(
        run_py_script, script
    )  # create a partial function to input script to

    with (
        multiprocessing.Pool() as pool
    ):  # should be fine to not specify pool size as long as no mem issues
        results = pool.map(run_script_with_arg, arg_list)
    return results


if __name__ == "__main__":  # Guard preventing future import issues
    # Import/format the list of paths (for large data, put inside the guard)
    ameriflux_meta = pd.read_csv(FLUX_METADATA, sep="\t")
    fluxnet_meta = ameriflux_meta.loc[ameriflux_meta["AmeriFlux FLUXNET Data"] == "Yes"]
    fluxnet_list = fluxnet_meta["Site ID"].to_list()

    script = "data-preprocessing.py"

    # Initialize run
    results = run_multiprocessing(script, fluxnet_list)
