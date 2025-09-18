#!/usr/bin/env python
# Calculating RMSE between MiCASA and FluxNet

# Import config variables and functions
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MICASA_PREPROCESSED_DATA, FLUX_METADATA

from utils.functions import import_flux_metadata
from plotting.plots_generator import import_flux_and_prep_data
import pandas as pd
import os
from sklearn.metrics import root_mean_squared_error

# Define misc variables
timedelta = "DD"

#################### Import Flux Data ##############################
# Import site metadata csv
fluxnet_meta = import_flux_metadata(FLUX_METADATA)
ids_list = fluxnet_meta["Site ID"]

results = []

for site_ID in ids_list:
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
    # Drop NA values for RMSE
    NEE_ds_clean = NEE_ds.dropna(subset=['FluxNet'])
    NEE_RMSE = root_mean_squared_error(NEE_ds_clean.MiCASA, NEE_ds_clean.FluxNet)

    ## NPP
    NPP_ds = pd.DataFrame()
    NPP_ds["MiCASA"] = micasa_ds["MiCASA NPP (kg m-2 s-1)"]
    NPP_ds["FluxNet DT GPP/2"] = fluxnet_data["GPP_DT (kgC m-2 s-1)"] / 2
    # Drop NA values for RMSE
    NPP_ds_clean = NPP_ds.dropna(subset=['FluxNet DT GPP/2'])
    NPP_RMSE = root_mean_squared_error(NPP_ds_clean.MiCASA, NPP_ds_clean["FluxNet DT GPP/2"])

    # Write values out to a list
    results.append({
        'SiteID' : site_ID,
        'NEE_RMSE': NEE_RMSE,
        'NPP_RMSE': NPP_RMSE,
    })

ds = pd.DataFrame(results)
fname = "RMSE_results.csv"
ds.to_csv(fname, index=False)
print(f"CSV written to: {fname}")
