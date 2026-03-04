import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import os
import glob

from utils.load_data import load_property_ledger

# ============================================================
# 1. LOAD LEDGER
# ============================================================
df, month_order = load_property_ledger()
st.title("📍 Property Map")

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

df.columns = df.columns.str.strip()

# Ensure Full Address exists
if "Full Address" not in df.columns:
    st.error("Raw Data must contain a column named 'Full Address'.")
    st.stop()

# ============================================================
# 2. GEOCODING CACHE
# ============================================================
CACHE_PATH = "data/geocode_cache.csv"

if os.path.exists(CACHE_PATH):
    cache = pd.read_csv(CACHE_PATH)
    cache.columns = cache.columns.str.strip()
else:
    cache = pd.DataFrame(columns=["Full Address", "Latitude", "Longitude"])

def geocode_address(address: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=10, headers={"User-Agent": "streamlit-map"})
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None, None
    return None, None

# Attach cached coordinates
df = df.merge(cache, on="Full Address", how="left")

# Geocode missing
missing_geo = df[df["Latitude"].isna() | df["Longitude"].isna()]

if not missing_geo.empty:
    st.info(f"Geocoding {len(missing_geo)} addresses...")

    new_entries = []
    for _, row in missing_geo.iterrows():
        lat, lon = geocode_address(row["Full Address"])
        new_entries.append({
            "Full Address": row["Full Address"],
            "Latitude": lat,
            "Longitude": lon
        })

    new_df = pd.DataFrame(new_entries)
    cache = pd.concat([cache, new_df], ignore_index=True)
    cache.drop_duplicates(subset=["Full Address"], keep="last", inplace=True)
    cache.to_csv(CACHE_PATH, index=False)

    df = df.drop(columns=["Latitude", "Longitude"], errors="ignore")
    df = df.merge(cache, on="Full Address", how="left")

df = df.dropna(subset=["Latitude", "Longitude"])

if df.empty:
    st.error("No valid coordinates available.")
    st.stop()

# ============================================================
# 3. FILTERS
# ============================================================
col_f1, col_f2 = st.columns(2)

if "Year" not in df.columns:
    st.error("Raw Data must contain a 'Year' column.")
    st.stop()

years = sorted(df["Year"].dropna().unique())
selected_year = col_f1.selectbox("Year", years)

utilities = ["All"] + sorted(df["Utility"].dropna().unique()) if "Utility" in df.columns else ["All"]
selected_utility = col_f2.selectbox("Utility Filter", utilities)

f = df[df["Year"] == selected_year].copy()
if selected_utility != "All" and "Utility" in df.columns:
    f = f[f["Utility"] == selected_utility]

if f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ============================================================
# 4. LAYER TOGGLES
# ============================================================
st.subheader("Map Layers")

c1, c2, c3, c4, c5 = st.columns(5)
show_spend = c1.checkbox("Spend", value=True)
show_usage = c2.checkbox("Usage", value=False)
show_eff = c3.checkbox("Efficiency", value=False)
show_occ = c4.checkbox("Occupancy", value=False)
show_outliers = c5.checkbox("Outliers", value=False)

# ============================================================
# 5. AGGREGATE TO PROPERTY LEVEL
# ============================================================
agg_cols = {}
if "$ Amount" in f.columns:
    agg_cols["$ Amount"] = "sum"
if "Usage" in f.columns:
    agg_cols["Usage"] = "sum"
for col in ["CPOR", "CPAR", "Occupancy %"]:
    if col in f.columns:
        agg_cols[col] = "mean"

group_cols = ["Property Name", "Latitude", "Longitude"]
if "Utility" in f.columns:
    group_cols.append("Utility")

prop = f.groupby(group_cols, as_index=False).agg(agg_cols)

# ============================================================
# 6. COLOR MAPPING
# ============================================================
utility_colors = {
    "Electric": [255, 215, 0, 180],
    "Gas": [30, 144, 255, 180],
    "Water": [32, 178, 170, 180],
}

prop["utility_color"] = prop["Utility"].apply(
    lambda u: utility_colors.get(u, [200, 200, 200, 180])
) if "Utility" in prop.columns else [[200, 200, 200, 180]] * len(prop)

prop["base_color"] = [[160, 160, 160, 140]] * len(prop)

# Spend radius
if "$ Amount" in prop.columns:
    max_spend = prop["$ Amount"].max() or 1
    prop["spend_radius"] = (prop["$ Amount"] / max_spend * 40000).clip(lower=5000)
else:
    prop["spend_radius"] = 0

# Usage radius
if "Usage" in prop.columns:
    max_usage = prop["Usage"].max() or 1
    prop["usage_radius"] = (prop["Usage"] / max_usage * 40000).clip(lower=5000)
else:
    prop["usage_radius"] = 0

# Efficiency color
eff_metric = "CPOR" if "CPOR" in prop.columns else ("CPAR" if "CPAR" in prop.columns else None)
if eff_metric:
    vals = prop[eff_metric].copy()
    vmin, vmax = vals.min(), vals.max()
    if vmin == vmax:
        vmin, vmax = 0, 1
    norm = (vals - vmin) / (vmax - vmin + 1e-9)
    prop["eff_color"] = [
        [int(255 * n), int(255 * (1 - n)), 0, 200] for n in norm
    ]
else:
    prop["eff_color"] = [[150, 150, 150, 0]] * len(prop)

# Occupancy color
if "Occupancy %" in prop.columns:
    occ_norm = (prop["Occupancy %"].fillna(0) / 100).clip(0, 1)
    prop["occ_color"] = [
        [50, 50, int(255 * n), 200] for n in occ_norm
    ]
else:
    prop["occ_color"] = [[150, 150, 150, 0]] * len(prop)

# Outlier flag
prop["is_outlier"] = False
if eff_metric:
    m = prop[eff_metric].mean()
    s = prop[eff_metric].std()
    if s and s > 0:
        z = (prop[eff_metric] - m) / s
        prop["is_outlier"] = z.abs() >= 2

# Tooltip fields
prop["spend"] = (
    prop["$ Amount"].map(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    if "$ Amount" in prop.columns else "N/A"
)
prop["usage"] = (
    prop["Usage"].map(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
    if "Usage" in prop.columns else "N/A"
)
prop["cpor"] = (
    prop["CPOR"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
    if "CPOR" in prop.columns else "N/A"
)
prop["cpar"] = (
    prop["CPAR"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
    if "CPAR" in prop.columns else "N/A"
)
prop["occ"] = (
    prop["Occupancy %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    if "Occupancy %" in prop.columns else "N/A"
)
prop["outlier"] = prop["is_outlier"].map(lambda x: "Yes" if x else "No")

tooltip = {
    "html": """
<b>{Property Name}</b><br/>
Utility: {Utility}<br/>
Spend: {spend}<br/>
Usage: {usage}<br/>
CPOR: {cpor}<br/>
CPAR: {cpar}<br/>
Occupancy: {occ}<br/>
Outlier: {outlier}
""",
    "style": {"backgroundColor": "rgba(0, 0, 0, 0.8)", "color": "white"},
}

# ============================================================
# 7. BUILD LAYERS
# ============================================================
layers = []

layers.append(
    pdk.Layer(
        "ScatterplotLayer",
        data=prop,
        get_position=["Longitude", "Latitude"],
        get_radius=4000,
        get_fill_color="base_color",
        pickable=True,
        opacity=0.6,
    )
)

if show_spend and "$ Amount" in prop.columns:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=prop[prop["$ Amount"] > 0],
            get_position=["Longitude", "Latitude"],
            get_radius="spend_radius",
            get_fill_color="utility_color",
            pickable=True,
            opacity=0.5,
        )
    )

if show_usage and "Usage" in prop.columns:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=prop[prop["Usage"] > 0],
            get_position=["Longitude", "Latitude"],
            get_radius="usage_radius",
            get_fill_color="utility_color",
            pickable=True,
            opacity=0.5,
        )
    )

if show_eff and eff_metric:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=prop[pd.notna(prop[eff_metric])],
            get_position=["Longitude", "Latitude"],
            get_radius=6000,
            get_fill_color="eff_color",
            pickable=True,
            opacity=0.7,
        )
    )

if show_occ and "Occupancy %" in prop.columns:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=prop[pd.notna(prop["Occupancy %"])],
            get_position=["Longitude", "Latitude"],
            get_radius=6000,
            get_fill_color="occ_color",
            pickable=True,
            opacity=0.7,
        )
    )

if show_outliers and prop["is_outlier"].any():
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=prop[prop["is_outlier"]],
            get_position=["Longitude", "Latitude"],
            get_radius=8000,
            get_fill_color=[255, 0, 0, 0],
            get_line_color=[255, 0, 0],
            line_width_min_pixels=2,
            stroked=True,
            filled=False,
            pickable=True,
            opacity=0.9,
        )
    )

# ============================================================
# 8. RENDER MAP
# ============================================================
view_state = pdk.ViewState(
    latitude=prop["Latitude"].mean(),
    longitude=prop["Longitude"].mean(),
    zoom=4,
    pitch=0,
    bearing=0,
)

deck = pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=view_state,
    layers=layers,
    tooltip=tooltip,
)

st.pydeck_chart(deck)
