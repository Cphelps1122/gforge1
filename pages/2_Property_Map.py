import streamlit as st
from utils.load_data import load_property_ledger
from utils.map_utils import build_property_coordinates, build_property_summary, render_property_map

st.title("Property Map")

df, month_order = load_property_ledger()

if df is None:
    st.error("Could not load data from uploaded file.")
    st.stop()

# Build coordinates
props = build_property_coordinates(df)

# Build summary
summary = build_property_summary(df)

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Portfolio Map")
    render_property_map(props)

with col2:
    st.subheader("Property Summary")
    if summary.empty:
        st.warning("No summary data available.")
    else:
        st.dataframe(summary)
