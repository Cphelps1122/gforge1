import streamlit as st

# Require uploaded file BEFORE anything else
if "uploaded_file" not in st.session_state or st.session_state["uploaded_file"] is None:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file in the sidebar.")
    st.stop()

import altair as alt
from utils.load_data import load_property_ledger

df, month_order = load_property_ledger()

st.title("🏨 Property Detail")

prop = st.selectbox("Select Property", sorted(df["Property Name"].unique()))
f = df[df["Property Name"] == prop].copy()

st.subheader(f"{prop} – Occupancy & Efficiency Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg CPOR", f"${f['Cost_per_Occupied_Room'].mean():.2f}")
col2.metric("