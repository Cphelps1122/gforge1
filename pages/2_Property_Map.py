import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import os

from utils.load_data import load_property_ledger

# ============================================================
# 1. LOAD DATA
# ============================================================
df, month_order = load_property_ledger()

st.title("📍 Property Map")

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

# ============================================================
# 2. PAGE SUMMARY
# ============================================================
st.markdown("""
### 📍 Property Map Overview

This interactive map provides a geographic view of your entire portfolio, allowing you to quickly understand how each property is performing across key utility and efficiency metrics. Each point on the map represents a property, and the available layers help you visualize spend, usage, efficiency, occupancy, and outlier behavior in a single, unified view.

**Purpose of the Map**  
The map is designed to help you:
- Identify geographic patterns in utility performance  
- Compare properties visually across multiple metrics  
- Spot regional inefficiencies or anomalies  
- Understand how utility types (electric, gas, water) vary across locations  

**What You’re Looking At**  
By default, all properties appear as neutral grey points to provide geographic context.  
You can then toggle additional layers to reveal deeper insights:

- **Spend Layer:** Bubble size shows total spend; color reflects utility type  
- **Usage Layer:** Bubble size shows total usage; color reflects utility type  
- **Efficiency Layer:** Color gradient highlights CPOR/CPAR performance  
- **Occupancy Layer:** Color intensity reflects occupancy percentage  
- **Outlier Layer:** Red outlines highlight statistically unusual properties  

Hover over any property to see key performance metrics.
""")

# ============================================================
# 3. ENSURE REQUIRED COLUMNS
# ============================================================
required_cols = ["Property Name", "Address", "City", "State", "Utility", "Year"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns for map: {', '.join(missing)}")
    st.stop()

# ============================================================
# 4. AUTO-GEOCODING WITH LOCAL CACHE
# ============================================================
CACHE_PATH = "data/geocode_cache.csv"

# Load cache if exists
if os.path.exists(CACHE_PATH):
    cache = pd.read_csv(CACHE_PATH)
else:
    cache = pd.DataFrame(columns=["Property Name", "Latitude", "Longitude"])

def geocode_address(address):
    """Geocode using Nominatim (OpenStreetMap)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        return None, None
    return None, None

# Build full address
df["full_address"] = (
    df["Address"].astype(str) + ", " +
    df["City"].astype(str) + ", " +
    df["State"].astype(str)
)

# Merge with cache
df = df.merge(cache, on="Property Name", how="left")

# Geocode missing entries
missing_geo = df[df["Latitude"].isna() | df["Longitude"].isna()]

if not missing_geo.empty:
    st.info(f"Geocoding {len(missing_geo)} properties...")

    new_entries = []
    for _, row in missing_geo.iterrows():
        lat, lon = geocode_address(row["full_address"])
        new_entries.append({
            "Property Name": row["Property Name"],
            "Latitude": lat,
            "Longitude": lon
        })

    new_df = pd.DataFrame(new_entries)
    cache = pd.concat([cache, new_df], ignore_index=True)
    cache.to_csv(CACHE_PATH, index=False)

    df = df.drop(columns=["Latitude", "Longitude"], errors="ignore")
    df = df.merge(cache, on="Property Name", how="left")

# Drop rows still missing coordinates
df = df.dropna(subset=["Latitude", "Longitude"])

if df.empty:
    st.error("No valid coordinates available after geocoding.")
    st.stop()

# ============================================================
# 5. FILTERS
# ============================================================
col_f1, col_f2 = st.columns(2)

years = sorted(df["Year"].dropna().unique())
selected_year = col_f1.selectbox("Year", years)

utilities = ["All"] + sorted(df["Utility"].dropna().unique())
selected_utility = col_f2.selectbox("Utility Filter", utilities)

f = df[df["Year"] == selected_year].copy()
if selected_utility != "All":
    f = f[f["Utility"] == selected_utility]

if f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ============================================================
# 6. LAYER TOGGLES
# ============================================================
st.subheader("Map Layers")

c1, c2, c3, c4, c5 = st.columns(5)
show_spend = c1.checkbox("Spend", value=True)
show_usage = c2.checkbox("Usage", value=False)
show_eff = c3.checkbox("Efficiency", value=False)
show_occ = c4.checkbox("Occupancy", value=False)
show_outliers = c5.checkbox("Outliers", value=False)

# ============================================================
# 7. AGGREGATE TO PROPERTY LEVEL
# ============================================================
agg_cols = {}
if "$ Amount" in f.columns:
    agg_cols["$ Amount"] = "sum"
if "Usage" in f.columns:
    agg_cols["Usage"] = "sum"
for col in ["CPOR", "CPAR", "Occupancy %"]:
    if col in f.columns:
        agg_cols[col] = "mean"

prop = f.groupby(
    ["Property Name", "Latitude", "Longitude", "Utility"],
    as_index=False
).agg(agg_cols)

# ============================================================
# 8. COLOR MAPPING
# ============================================================
utility_colors = {
    "Electric": [255, 215, 0, 180],   # Yellow
    "Gas": [30, 144, 255, 180],       # Blue
    "Water": [32, 178, 170, 180],     # Teal
}

prop["utility_color"] = prop["Utility"].apply(
    lambda u: utility_colors.get(u, [200, 200, 200, 180])
)

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
    eff_colors = []
    for n in norm:
        r = int(255 * n)
        g = int(255 * (1 - n))
        eff_colors.append([r, g, 0, 200])
    prop["eff_color"] = eff_colors
else:
    prop["eff_color"] = [[150, 150, 150, 0]] * len(prop)

# Occupancy color
if "Occupancy %" in prop.columns:
    occ = prop["Occupancy %"].fillna(0)
    occ_norm = (occ / 100).clip(0, 1)
    occ_colors = []
    for n in occ_norm:
        b = int(255 * n)
        occ_colors.append([50, 50, b, 200])
    prop["occ_color"] = occ_colors
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

# ============================================================
# 9. TOOLTIP
# ============================================================
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

prop["spend"] = prop["$ Amount"].map(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A") if "$ Amount" in prop.columns else "N/A"
prop["usage"] = prop["Usage"].map(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A") if "Usage" in prop.columns else "N/A"
prop["cpor"] = prop["CPOR"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A") if "CPOR" in prop.columns else "N/A"
prop["cpar"] = prop["CPAR"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A") if "CPAR" in prop.columns else "N/A"
prop["occ"] = prop["Occupancy %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A") if "Occupancy %" in prop.columns else "N/A"
prop["outlier"] = prop["is_outlier"].map(lambda x: "Yes" if x else "No")

# ============================================================
# 10. BUILD LAYERS
# ============================================================
layers = []

# Base layer
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

# Spend layer
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

# Usage layer
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

# Efficiency layer
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

# Occupancy layer
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

# Outlier layer
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
# 11. VIEW STATE
# ============================================================
center_lat = prop["Latitude"].mean()
center_lon = prop["Longitude"].mean()

view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=4,
    pitch=0,
    bearing=0,
)

# ============================================================
# 12. RENDER MAP
# ============================================================
deck = pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=view_state,
    layers=layers,
    tooltip=tooltip,
)

st.pydeck_chart(deck)

st.markdown("""
**How to use this map:**  
- Use the filters above to change the year and utility view.  
- Toggle layers to explore spend, usage, efficiency, occupancy, and outliers.  
- Hover over any property to see key performance metrics.
""")
