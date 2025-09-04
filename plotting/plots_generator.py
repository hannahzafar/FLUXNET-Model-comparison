#!/usr/bin/env python
# Generate maps, NEE and NPP comparison plots for each site

# Import config variables and functions
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MICASA_PREPROCESSED_DATA, FLUX_DATA_PATH, FLUX_METADATA

from utils.functions import import_flux_metadata, import_flux_site_data, convert_flux_to_micasa_units, replace_outliers_with_nan, clean_flux_datasets

# Import other modules
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import cartopy.crs as ccrs
import os

##### Functions ########
def import_flux_and_prep_data(site_ID, timedelta):
    # Import site AmeriFlux FLUXNET data
    fluxnet_sel = import_flux_site_data(FLUX_DATA_PATH, site_ID, timedelta)

    # Generate old and new list to clean data
    cols = fluxnet_sel.columns.tolist()
    list = [cols[0], cols[-1]]
    new_list = ["NEE (kgC m-2 s-1)", "GPP_DT (kgC m-2 s-1)"]

    # Convert and clean datasets 
    for old, new in zip(list, new_list):
       fluxnet_sel = convert_flux_to_micasa_units(fluxnet_sel, old, new)
       fluxnet_sel = clean_flux_datasets(fluxnet_sel, new, "NEE_VUT_REF_QC")

    # Mask GPP outliers
    fluxnet_sel = replace_outliers_with_nan(fluxnet_sel, "GPP_DT (kgC m-2 s-1)")

    return fluxnet_sel

######### input arguments ############
# Input site ID
if __name__ == "main":
    parser = argparse.ArgumentParser(description="User-specified parameters")
    parser.add_argument(
        "site_ID", type=str, help="FluxNet/AmeriFLUX Site Identifier (XX-XXX)"
    )
    args = parser.parse_args()
    site_ID = args.site_ID

    # Define misc variables
    timedelta = "DD"

    ############## Check if run is necessary #############
    # Check if output file for the site already exists (quits if so)
    output_dir = "plots"
    output_filename = f"{site_ID}_NEE_NPP.png"
    output_path = os.path.join(output_dir, output_filename)

    # If the file exists, exit the script
    if os.path.exists(output_path):
        print(f"File for site {site_ID} already exists: {output_path}. Exiting.")
        sys.exit()  # Exit the script immediately

    #################### Import Flux Data ##############################
    # Import metadata and identify site ID lat/lon
    fluxnet_meta = import_flux_metadata(FLUX_METADATA)
    site_lat = fluxnet_meta.loc[fluxnet_meta["Site ID"] == site_ID, "Latitude (degrees)"].values
    site_lon = fluxnet_meta.loc[fluxnet_meta["Site ID"] == site_ID, "Longitude (degrees)"].values

    fluxnet_data = import_flux_and_prep_data(site_ID, timedelta)

    ############ Import Preprocessed Micasa Data ################
    filename = f"{site_ID}_micasa_{timedelta}.csv"
    path = os.path.join(MICASA_PREPROCESSED_DATA, filename)
    micasa_ds = pd.read_csv(path, index_col=0, parse_dates=True)

    ############## Append datasets #########################
    # Make clean dataframe and append together
    ## NEE
    NEE_ds = pd.DataFrame()
    NEE_ds["MiCASA"] = micasa_ds["MiCASA NEE (kg m-2 s-1)"]
    NEE_ds["FluxNet"] = fluxnet_data["NEE (kgC m-2 s-1)"]

    ## NPP
    NPP_ds = pd.DataFrame()
    NPP_ds["MiCASA"] = micasa_ds["MiCASA NPP (kg m-2 s-1)"]
    NPP_ds["FluxNet DT GPP/2"] = fluxnet_data["GPP_DT (kgC m-2 s-1)"] / 2


    ######### Create plots ########################
    # Create a subplot grid with specific width ratios
    fig, axs = plt.subplots(
        4,
        1,
        # subplot_kw={'projection': proj},
        gridspec_kw={"height_ratios": [1.2, 2, 0.25, 2], "hspace": 0.01},
        figsize=(10, 12),
    )

    # Define the map projection
    proj = ccrs.PlateCarree()

    # Pick map location based on location of site
    if site_lat >= 20:
        # North America extents
        min_lon, max_lon = -170, -57
        min_lat, max_lat = 25, 74

    else:
        # South America extents
        min_lon, max_lon = -90, -30
        min_lat, max_lat = -60, 12

    axs[0].axis("off")
    axs[0] = plt.subplot(4, 1, 1, projection=proj, frameon=False)
    axs[0].set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())
    axs[0].coastlines()
    axs[0].scatter(
        site_lon, site_lat, marker="*", s=300, color="yellow", edgecolor="black", zorder=3
    )

    #TODO: Make this a function I can call for stats analysis?
    NEE_ds.plot(ax=axs[1], ylabel="NEE\n(kgC m$^{-2}$ s$^{-1}$)")
    # Format x-axis labels
    axs[1].xaxis.set_major_locator(mdates.AutoDateLocator())
    # Disable minor ticks completely
    axs[1].tick_params(axis="x", which="minor", labelsize=0, labelcolor="none")

    axs[2].set_visible(False)

    NPP_ds.plot(ax=axs[3], ylabel="NPP\n(kgC m$^{-2}$ s$^{-1}$)")
    # Format x-axis labels
    axs[3].xaxis.set_major_locator(mdates.AutoDateLocator())
    # Disable minor ticks completely
    axs[3].tick_params(axis="x", which="minor", labelsize=0, labelcolor="none")


    date_format = mdates.DateFormatter("%b %Y")
    for i in range(1, 4, 2):
        axs[i].xaxis.set_major_formatter(date_format)
        axs[i].set_xlabel("")
    fig.suptitle(f"{site_ID}", y=0.9, fontsize=14)

    output_path = os.path.join(output_dir, output_filename)

    fig.savefig(output_path)
    print(f"Plot written to: {output_path}")
