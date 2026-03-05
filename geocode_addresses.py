import pandas as pd
import requests
import time

df = pd.read_excel("data/yourfile.xlsx", sheet_name="Raw Data")
df.columns = df.columns.str.strip()

def normalize(col):
    import re
    return re.sub(r"[^a-z0-9]", "", col.lower())

normalized = {normalize(c): c for c in df.columns}

col_property = normalized["propertyname"]
col_city = normalized["city"]
col_state = normalized["state"]
col_zip = normalized["zipcode"]

df["full_address"] = (
    df[col_property].astype(str)
    + ", "
    + df[col_city].astype(str)
    + ", "
    + df[col_state].astype(str)
    + " "
    + df[col_zip].astype(str)
)

def geocode(addr):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": addr, "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent": "batch-geocoder"})
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        return None, None
    return None, None

results = []
for addr in df["full_address"].unique():
    lat, lon = geocode(addr)
    results.append({"full_address": addr, "Latitude": lat, "Longitude": lon})
    print("Geocoded:", addr, lat, lon)
    time.sleep(1)  # required by Nominatim

pd.DataFrame(results).to_csv("data/geocode_cache.csv", index=False)
print("DONE")
