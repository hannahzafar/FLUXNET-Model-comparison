#!/usr/bin/env python
# Extract fluxnet and micasa data as csv for plotting

# Import config variables and functions
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MICASA_DATA_PATH, FLUX_DATA_PATH, FLUX_METADATA

from utils.functions import import_flux_site_data, get_single_match

# Import other modules
import pandas as pd
import xarray as xr
import argparse
import os


### Modified for multiprocessing: for simplicity, hard coded timedelta and variable list
# Arguments: Site ID, Fluxnet time step (HH or DD), and MiCASA variable to extract
parser = argparse.ArgumentParser(description="User-specified parameters")
parser.add_argument(
    "site_ID", type=str, help="FluxNet/AmeriFLUX Site Identifier (XX-XXX)"
)
# parser.add_argument('timedelta', type=str, choices=['HH', 'DD'],
#                      help='Time step used in Fluxnet Average Calculation')
# parser.add_argument('variable_list', type=str, nargs='+',
#                      help='MiCASA variable(s) desired for extraction (separated by spaces)')
args = parser.parse_args()
site_ID = args.site_ID

# Removed user inputs and hard coded variables
# timedelta = args.timedelta
# micasa_var_list = args.variable_list
timedelta = "DD"
micasa_var_list = ["NEE", "NPP"]

# Check if output file for the site already exists (quits if so)
output_dir = "intermediates"
for micasa_var in micasa_var_list:
    output_filename = f"{site_ID}_micasa_{timedelta}.csv"
    output_path = os.path.join(output_dir, output_filename)

    # If the file exists, exit the script
    if os.path.exists(output_path):
        print(f"File for site {site_ID} already exists: {output_path}. Exiting.")
        sys.exit()  # Exit the script immediately

# Open site ID metadata and extract lat/lon
ameriflux_meta = pd.read_csv(FLUX_METADATA, sep="\t")
site_lat = ameriflux_meta.loc[
    ameriflux_meta["Site ID"] == site_ID, "Latitude (degrees)"
].values
site_lon = ameriflux_meta.loc[
    ameriflux_meta["Site ID"] == site_ID, "Longitude (degrees)"
].values

# Open site data
fluxnet_sel = import_flux_site_data(FLUX_DATA_PATH, site_ID, timedelta)

time = fluxnet_sel.index
dates_unique = list({dt.date() for dt in time})
dates_unique.sort()

# Extract micasa data
if timedelta == "HH":
    data_path = MICASA_DATA_PATH / "3hrly/"

elif timedelta == "DD":
    data_path = MICASA_DATA_PATH / "daily/"

else:
    raise ValueError(f"Timedelta invalid")

path_list = []
for date in dates_unique:
    f_year = str(date.year)
    f_month = f"{date.month:02}"
    filename = "MiCASA_v1_flux_*" + date.strftime("%Y%m%d") + ".nc4"
    try:  # Test if the micasa file exists for that time stamp
        filepath = get_single_match(
            data_path, os.path.join(data_path, f_year, f_month, filename)
        )
        path_list.append(filepath)
    except ValueError:
        continue  # Skip missing MiCASA data

# path_list = path_list[0] # testing
# Create an empty dataframe for output
ds_out = pd.DataFrame()

with xr.open_mfdataset(path_list)[micasa_var_list] as ds:
    # Select grid closest to selected site
    ds_subset = ds.sel(lon=site_lon, lat=site_lat, method="nearest")

    # Prep data for writing to csv
    ds_subset = ds_subset.squeeze(dim=["lat", "lon"], drop=True)

    # Output a single file for each site with all variables
    for micasa_var in micasa_var_list:
        ds_out[micasa_var] = ds_subset[micasa_var].to_dataframe()
        ds_out.rename(
            columns={
                micasa_var: f"MiCASA {micasa_var} ({ds_subset[micasa_var].units})"
            },
            inplace=True,
        )
    # Write to csv
    output_dir = "intermediates"
    output_filename = f"{site_ID}_micasa_{timedelta}.csv"
    output_path = os.path.join(output_dir, output_filename)

    os.makedirs(output_dir, exist_ok=True)
    ds_out.to_csv(output_path)
    print(f"CSV written to: {output_path}")
