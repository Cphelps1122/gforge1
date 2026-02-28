import streamlit as st
import pydeck as pdk
from utils.load_data import load_property_ledger
from utils.formatting import money

st.title("Property Map")

# Ensure file is uploaded
uploaded_file = st.session_state.get("uploaded_file_obj")
if uploaded_file is None:
    st.write("Please upload your Excel file using the sidebar.")
    st.stop()

df, month_order = load_property_ledger(uploaded_file)

if df is None or df.empty:
    st.error("Unable to load data. Please check the uploaded file.")
    st.stop()

# -----------------------------
# Validate map columns
# -----------------------------
required_cols = ["Latitude", "Longitude", "Property Name", "$ Amount"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column for mapping: {col}")
        st.stop()

# -----------------------------
# Map View
# -----------------------------
st.subheader("Portfolio Map View")

df_map = df.copy()
df_map["Formatted Cost"] = df_map["$ Amount"].apply(money)

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
