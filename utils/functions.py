# Functions used in this project

from pathlib import Path
import glob
import numpy as np
import pandas as pd


def import_flux_metadata(flux_metadata_path):
    """ Import FLUXNET only Ameriflux metadata information

    Args: 
        flux_metadata_path (Path object): Path to Ameriflux metadata CSV


    Returns:
        fluxnet_sel_sub (pd.DataFrame): clean dataframe of 
    """

    # Import site metadata csv
    ameriflux_meta = pd.read_csv(flux_metadata_path, sep="\t")
    fluxnet_meta = ameriflux_meta.loc[
            ameriflux_meta["AmeriFlux FLUXNET Data"] == "Yes"
            ]  # use FLUXNET only
    return fluxnet_meta

def import_flux_site_data(flux_data_path, site_ID, timedelta):
    """ Import site data for selected site ID and timedelta

    Args: 
        flux_data_path (Path object): path to flux data CSVs
        site_ID (str): FluxNet Site ID of interest
        timedelta (str): measurement frequency (HH or DD)

    Returns:
        fluxnet_sel_sub (pd.DataFrame): A cleaned DataFrame with all sites metadata
    """
    pattern = (
        "AMF_"
        + site_ID
        + "_FLUXNET_SUBSET_*/AMF_"
        + site_ID
        + "_FLUXNET_SUBSET_"
        + timedelta
        + "*.csv"
    )
    site_file = get_single_match(flux_data_path, pattern)
    fluxnet_sel = pd.read_csv(site_file)
    fluxnet_sel_sub = fluxnet_sel.loc[
        :,
        ["TIMESTAMP", "NEE_VUT_REF", "NEE_VUT_REF_QC", "GPP_NT_VUT_REF", "GPP_DT_VUT_REF"],
    ].copy()
    fluxnet_sel_sub["TIMESTAMP"] = pd.to_datetime(
        fluxnet_sel_sub["TIMESTAMP"], format="%Y%m%d"
    )
    fluxnet_sel_sub = fluxnet_sel_sub.set_index("TIMESTAMP")
    return fluxnet_sel_sub


def get_single_match(base_path, pattern):
    """Get exactly one file matching the pattern in base_path.

    Args:
        base_path (Path object): base directory to search in
        pattern (str): glob pattern (can include subdirectories)

    Returns:
        Path (Path object): Single matching file path
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


def replace_outliers_with_nan(df, column):
    """Replace outliers (1.5 IQR above/below) in a DataFrame column with NaN.

    Args:
        df (pd.DataFrame): The DataFrame.
        column (str): The column name to check for outliers.

    Returns:
        pd.DataFrame: The DataFrame with outliers replaced by NaN.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df[column] = df[column].mask(
        (df[column] < lower_bound) | (df[column] > upper_bound), np.nan
    )
    return df

