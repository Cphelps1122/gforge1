import pandas as pd
from geopy.geocoders import Nominatim
from functools import lru_cache

geolocator = Nominatim(user_agent="gforge1")

@lru_cache(maxsize=None)
def geocode_address(full_address):
    try:
        loc = geolocator.geocode(full_address)
        if loc:
            return loc.latitude, loc.longitude
    except:
        return None, None
    return None, None

def load_provider_addresses(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="Provider")
    df["Full Address"] = (
        df["Address"].astype(str) + ", " +
        df["City"].astype(str) + ", " +
        df["State"].astype(str) + " " +
        df["Zip Code"].astype(str)
    )
    return df[["Code", "Name of utility provider", "Full Address"]]

def add_coordinates(df, uploaded_file):
    provider_df = load_provider_addresses(uploaded_file)

    df["Latitude"] = None
    df["Longitude"] = None

    for prop in df["Property Name"].unique():
        sub = df[df["Property Name"] == prop].iloc[0]
        provider_code = sub["Provider Code"]

        provider_row = provider_df[provider_df["Code"] == provider_code]
        if provider_row.empty:
            continue

        full_address = provider_row["Full Address"].iloc[0]
        lat, lon = geocode_address(full_address)

        df.loc[df["Property Name"] == prop, "Latitude"] = lat
        df.loc[df["Property Name"] == prop, "Longitude"] = lon

    return df