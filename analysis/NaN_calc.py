#!/usr/bin/env python
# Calculate and export FluxNet NaN stats for plotting and analysis

# Import config variables and functions
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FLUX_METADATA

from utils.functions import import_flux_metadata
from plotting.plots_generator import import_flux_and_prep_data
import pandas as pd

# Define misc variables
timedelta = "DD"

#################### Import Flux Data ##############################
# Import site metadata csv
fluxnet_meta = import_flux_metadata(FLUX_METADATA)
ids_list = fluxnet_meta["Site ID"]

results = []

for site_ID in ids_list:
    # create a site id dictionary to append to results
    site_dict = {"SiteID" : site_ID}

    fluxnet_data = import_flux_and_prep_data(site_ID, timedelta)
    # Subset needed columns
    columns = ["NEE (kgC m-2 s-1)", "GPP_DT (kgC m-2 s-1)"]
    fluxnet_sub = fluxnet_data[columns]
    # NaNs between NEE and NPP are both generated from NEE_VUT_REF_QC,
    # but there's additional values thrown out for NPP outliers, so calc separately
    for col_name, df_col in fluxnet_sub.items():
        new_col_name = col_name[:3] + '_pct_nan'
        site_dict[new_col_name] = df_col.isna().mean() * 100

    results.append(site_dict)

# Convert results 
ds = pd.DataFrame(results)
fname = "nan_results.csv"
ds.to_csv(fname, index=False)
print(f"CSV written to: {fname}")
