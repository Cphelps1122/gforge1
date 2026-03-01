import streamlit as st
from utils.load_data import load_property_ledger
from utils.map_utils import (
    build_property_coordinates,
    build_property_summary,
    render_property_map
)

st.title("🗺️ Property Map with Occupancy Heat Layer")

df, month_order = load_property_ledger()

if df is None:
    st.error("Could not load data from uploaded file.")
    st.stop()

# Build coordinates + summary
props = build_property_coordinates(df)
summary = build_property_summary(df)

# --- Property Filters ---
property_list = sorted(df["Property Name"].unique())
selected_properties = st.multiselect(
    "Select Properties",
    property_list,
    default=property_list
)

df_filtered = df[df["Property Name"].isin(selected_properties)]
props_filtered = props[props["Property Name"].isin(selected_properties)]
summary_filtered = summary[summary["Property Name"].isin(selected_properties)]

# --- Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Occupancy Heat Map")
    render_property_map(props_filtered)

with col2:
    st.subheader("Property Summary")
    if summary_filtered.empty:
        st.warning("No summary data available.")
    else:
        st.dataframe(summary_filtered)
