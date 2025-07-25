#!/usr/bin/env python
# Extract fluxnet and micasa data as csv for plotting

# Import config variables
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MICASA_DATA_PATH, FLUX_DATA_PATH, FLUX_METADATA

# Import other modules
import pandas as pd
import xarray as xr
import glob
import argparse
import os
import pytz
from timezonefinder import TimezoneFinder


######### functions ############
def get_single_match(base_path, pattern):
    """Get exactly one file matching the pattern in base_path.

    Args:
        base_path: Path object - base directory to search in
        pattern: str - glob pattern (can include subdirectories)

    Returns:
        Path: Single matching file path
    """
    if not isinstance(base_path, Path):
        raise TypeError(f"base_path must be a Path object, got {type(base_path)}")

    # Use glob.glob for complex patterns with subdirectories
    full_pattern = str(base_path / pattern)
    matches = glob.glob(full_pattern)

    # Convert back to Path objects
    matches = [Path(m) for m in matches]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        raise ValueError(f"No matches found for pattern '{pattern}' in {base_path}")
    else:
        raise ValueError(f"Multiple matches found for pattern '{pattern}': {matches}")


# Function to convert local standard time (no DLS) time to UTC
tf = TimezoneFinder()


def local_std_to_utc_std(df, col, lat, lon):
    def convert_row(row):
        # Find the timezone for the given lat/lon
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if timezone_str is not None:
            timezone = pytz.timezone(timezone_str)
            # Localize datetime without DST
            standard_time = timezone.normalize(
                timezone.localize(row[col], is_dst=False)
            )
            # Convert to UTC
            return standard_time.astimezone(pytz.utc)
        else:
            raise ValueError("Cannot determine site time zone")

    df["utc_time"] = df.apply(convert_row, axis=1)
    return df


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
pattern = (
    "AMF_"
    + site_ID
    + "_FLUXNET_SUBSET_*/AMF_"
    + site_ID
    + "_FLUXNET_SUBSET_"
    + timedelta
    + "*.csv"
)
site_file = get_single_match(FLUX_DATA_PATH, pattern)

# print(site_file)
fluxnet_sel = pd.read_csv(site_file)

# select subset of columns + convert to datetime objects
if timedelta == "HH":
    fluxnet_sel_dates = fluxnet_sel.loc[:, ["TIMESTAMP_START", "TIMESTAMP_END"]].copy()
    fluxnet_sel_dates["TIMESTAMP_START"] = pd.to_datetime(
        fluxnet_sel_dates["TIMESTAMP_START"], format="%Y%m%d%H%M"
    )
    fluxnet_sel_dates["TIMESTAMP_END"] = pd.to_datetime(
        fluxnet_sel_dates["TIMESTAMP_END"], format="%Y%m%d%H%M"
    )

    # Convert time to UTC
    fluxnet_sel_dates = local_std_to_utc_std(
        fluxnet_sel_dates, "TIMESTAMP_START", site_lat, site_lon
    )
    fluxnet_sel_dates = fluxnet_sel_dates.set_index("utc_time")

elif timedelta == "DD":
    fluxnet_sel_dates = fluxnet_sel.loc[:, ["TIMESTAMP"]].copy()
    fluxnet_sel_dates["TIMESTAMP"] = pd.to_datetime(
        fluxnet_sel_dates["TIMESTAMP"], format="%Y%m%d"
    )
    fluxnet_sel_dates = fluxnet_sel_dates.set_index("TIMESTAMP")

else:
    raise ValueError(f"Timedelta invalid")
# Create a list of unique dates from the site
time = fluxnet_sel_dates.index
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
