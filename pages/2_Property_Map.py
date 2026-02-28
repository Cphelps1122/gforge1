import streamlit as st
import pydeck as pdk
from utils.load_data import load_property_ledger
from utils.formatting import money

st.title("Property Map")

# Auto-load newest file
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No data available. Please add an Excel file to /data.")
    st.stop()

# Validate required columns
required_cols = ["Latitude", "Longitude", "Property Name", "$ Amount"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column for mapping: {col}")
        st.stop()

# Prepare map data
df_map = df.copy()
df_map["Formatted Cost"] = df_map["$ Amount"].apply(money)

# Map layer
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position=["Longitude", "Latitude"],
    get_radius=500,
    get_color=[0, 90, 200],
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=df_map["Latitude"].mean(),
    longitude=df_map["Longitude"].mean(),
    zoom=8,
)

tooltip = {
    "html": "<b>{Property Name}</b><br/>Cost: {Formatted Cost}",
    "style": {"backgroundColor": "white", "color": "black"}
}

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))
