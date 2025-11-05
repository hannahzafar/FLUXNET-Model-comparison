#!/usr/bin/env python
# Process MERRA-2 data for fluxnet analysis

from merra2_tools import MERRA2_ROOT, find_MERRA2_files, create_vzarr_store
import argparse

# NOTE: How am I going to select years, if Amerflux years varies across sites?
# AmeriFlux FLUXNET spans 1991-2021 across all the sites, individual sites vary, let's just start with that
parser = argparse.ArgumentParser(description="Dataset selection")
varlist = ["T2M", "PRECTOTCORR"]
parser.add_argument(
    "var",
    metavar="var",
    type=str,
    choices=varlist,
    help=f"Data variable choice: {', '.join(varlist)}",
)
var = parser.parse_args().var

start_yr, end_yr = [1991, 2021]
if var == "T2M":
    freq1 = "tavg"
    freq2 = "M"
    group = "slv"

if var == "PRECTOTCORR":
    freq1 = "tavg"
    freq2 = "M"
    group = "flx"

details, fileslist = find_MERRA2_files(
    MERRA2_ROOT, freq1, freq2, group, start_yr, end_yr
)
print(details)
import sys

sys.exit()

vstore_loc = create_vzarr_store(details, fileslist)
print(vstore_loc)
