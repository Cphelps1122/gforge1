import streamlit as st
import pydeck as pdk
from utils.load_data import load_property_ledger
from utils.geo import add_coordinates

st.set_page_config(page_title="Property Map – gforge1", layout="wide")

df, _ = load_property_ledger()
df = add_coordinates(df)

st.title("🗺️ Property Map with Occupancy Overlays")
st.write("Map of properties with marker size and color reflecting occupancy and intensity.")

# -----------------------------
# AGGREGATE PROPERTY-LEVEL METRICS
# -----------------------------
props = df.groupby("Property Name").agg({
    "Latitude": "first",
    "Longitude": "first",
    "City": "first",
    "State": "first",
    "Occupied Rooms": "mean",
    "# Units": "first",
    "$ Amount": "sum",
    "Usage": "sum"
}).reset_index()

props = props.dropna(subset=["Latitude", "Longitude"])

if props.empty:
    st.warning("No coordinates available. Check Provider sheet or geocoding.")
else:
    # Occupancy ratio
    props["Occ_Ratio"] = props["Occupied Rooms"] / props["# Units"]

    # Marker radius scaled by occupancy
    props["Radius"] = (props["Occ_Ratio"].fillna(0) * 3000) + 500

    # Color by occupancy (low = red, high = green-ish)
    def occ_to_color(r):
        if r is None:
            return [128, 128, 128]
        if r < 0.4:
            return [200, 60, 60]
        elif r < 0.7:
            return [230, 180, 60]
        else:
            return [60, 160, 90]

    props["Color"] = props["Occ_Ratio"].apply(occ_to_color)

    layer = pdk.Layer(
        "ScatterplotLayer",
        props,
        get_position=["Longitude", "Latitude"],
        get_radius="Radius",
        get_fill_color="Color",
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=props["Latitude"].mean(),
        longitude=props["Longitude"].mean(),
        zoom=8,
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "text": "{Property Name}\n{City}, {State}\nOcc Ratio: {Occ_Ratio}\nUsage: {Usage}\nSpend: ${$ Amount}"
        }
    )

    st.pydeck_chart(deck)
