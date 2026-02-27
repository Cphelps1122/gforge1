import streamlit as st

# Correct guard: check the persistent key
if "uploaded_file_obj" not in st.session_state:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file in the sidebar.")
    st.stop()

import pydeck as pdk
from utils.load_data import load_property_ledger
from utils.geo import add_coordinates

df, _ = load_property_ledger()
uploaded_file = st.session_state["uploaded_file_obj"]

df = add_coordinates(df, uploaded_file)

st.title("🗺️ Property Map with Occupancy Overlays")

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

props["Occ_Ratio"] = props["Occupied Rooms"] / props["# Units"]
props["Radius"] = (props["Occ_Ratio"].fillna(0) * 3000) + 500

def occ_to_color(r):
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
    zoom=9,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "{Property Name}\n{City}, {State}\nOcc Ratio: {Occ_Ratio}"}
)


st.pydeck_chart(deck)

