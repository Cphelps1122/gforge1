import streamlit as st
import pandas as pd
from utils.load_data import load_property_ledger
from utils.formatting import money

st.title("Benchmarking")

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
# Benchmarking Controls
# -----------------------------
st.subheader("Benchmarking Controls")

utility_types = sorted(df["Utility"].unique())
selected_utility = st.selectbox("Select Utility Type", utility_types)

metric_options = {
    "Cost per Unit": "Cost_per_Unit",
    "Cost per Occupied Room": "Cost_per_Occupied_Room",
    "Cost per Available Room": "Cost_per_Available_Room",
    "CPOR": "CPOR",
    "CPAR": "CPAR",
}

selected_metric_label = st.selectbox("Select Benchmark Metric", list(metric_options.keys()))
selected_metric = metric_options[selected_metric_label]

df_filtered = df[df["Utility"] == selected_utility]

# -----------------------------
# Benchmark Table
# -----------------------------
st.subheader(f"{selected_utility} — Benchmark Table ({selected_metric_label})")

df_display = df_filtered.copy()

# Format money columns
money_cols = [
    "$ Amount", "Cost_per_Unit", "Cost_per_Occupied_Room",
    "Cost_per_Available_Room", "CPOR", "CPAR"
]

for col in money_cols:
    if col in df_display.columns:
        df_display[col] = df_display[col].apply(money)

st.dataframe(df_display, use_container_width=True)

# -----------------------------
# Benchmark Summary
# -----------------------------
st.subheader("Benchmark Summary")

benchmark_value = df_filtered[selected_metric].mean()
st.metric(f"Portfolio Average {selected_metric_label}", money(benchmark_value))
