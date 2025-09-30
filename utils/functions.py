# Functions used in this project

from pathlib import Path
import glob
import numpy as np
import pandas as pd
import pytz
from timezonefinder import TimezoneFinder


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

def import_site_RMSE_data(flux_metadata_path,RMSE_results_path):
    fluxnet_meta = import_flux_metadata(flux_metadata_path)
    site_subset = ['Site ID', 
               'Longitude (degrees)',
                'Latitude (degrees)',
               ]
    site_subset = ['Site ID', 
               'Longitude (degrees)',
                'Latitude (degrees)',
               ]
    df_meta = fluxnet_meta[site_subset]
    df_meta = df_meta.set_index('Site ID')
    df_meta = df_meta.rename(columns={'Latitude (degrees)': 'lat', 'Longitude (degrees)': 'lon'})

    RMSE_results = pd.read_csv(RMSE_results_path, index_col='SiteID')
    return df_meta.join(RMSE_results, on='Site ID', how="inner")

def local_std_to_utc_std(df, col, lat, lon):
    """ Convert local standard time (no DLS) to UTC

    Args:
        df (pd.DataFrame): dataframe with time values to conver
        col (str): Column Name containing values to convert
        lat: latitude
        lon: longitude

    Returns:
        pd.Dataframe: A dataframe with an additional column in UTC time 
    """
    def convert_row(row):
        # Find the timezone for the given lat/lon
        tf = TimezoneFinder()
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

    if timedelta == "DD":
        fluxnet_sel_sub = fluxnet_sel.loc[:,
        ["TIMESTAMP", "NEE_VUT_REF", "NEE_VUT_REF_QC", "GPP_NT_VUT_REF", "GPP_DT_VUT_REF"],
        ].copy()
        fluxnet_sel_sub["TIMESTAMP"] = pd.to_datetime(
                fluxnet_sel_sub["TIMESTAMP"], format="%Y%m%d"
            )
        fluxnet_sel_sub = fluxnet_sel_sub.set_index("TIMESTAMP")
        return fluxnet_sel_sub

    elif timedelta == "HH":
        raise ValueError("Half-hourly data parsing incomplete, refer to utils/functions.py")
        #TODO: Fix this so that the formatting works similar to DD but then need to pass function
        """
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
        """
    else:
        raise ValueError(f"Timedelta {timedelta} invalid")


def convert_flux_to_micasa_units(df_in, column, new_column):
    """ Convert Flux daily data units (gC m-2 d-1) to MiCASA (kgC m-2 s-1)
    Args:
        df_in (pd.Dataframe): The input DataFrame.
        column (str): The column name to be converted.
        new_column (str): The new name for the converted column.

    Returns:
        pd.Dataframe: The DataFrame with an added column of converted values.

    """
    df = df_in.copy()
    df[new_column] = df[column] * 1e-3 / 86400

    return df


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

def clean_flux_datasets(df, column, QC_column):
    """ Set values to nan where FluxNet QC < 1

    Args:
        df (pd.DataFrame): The DataFrame.
        column (str): The column name to clean.
        QC_column (str): The column name to obtain QC values

    Returns:
        pd.DataFrame: The DataFrame with poor QC readings as nan.
    """
    df[column] = df[column].mask(df[QC_column] < 1, np.nan)

    return df
