import streamlit as st
import pandas as pd
import altair as alt
from utils.load_data import load_property_ledger

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

# Ensure Billing Date is datetime
df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

st.title("📊 Portfolio Benchmarking")

# -----------------------------
# METRIC SELECTOR
# -----------------------------
metric = st.selectbox(
    "Benchmark Metric",
    [
        "CPOR",                      # Cost per Occupied Room
        "CPAR",                      # Cost per Available Room
        "Usage_per_Occupied_Room",
        "Usage_per_Available_Room",
        "Cost_per_Unit",
    ],
)

# -----------------------------
# COMPUTE BENCHMARK VALUES
# -----------------------------
# Use the last 3 months of data for each property
latest = df.sort_values("Billing Date").groupby("Property Name").tail(3)

# Compute mean of selected metric
bench = latest.groupby("Property Name", as_index=False)[metric].mean()

# Sort ascending (best performers first)
bench = bench.sort_values(metric, ascending=True)

# -----------------------------
# CHART
# -----------------------------
st.subheader("Benchmark Results")

chart = (
    alt.Chart(bench)
    .mark_bar()
    .encode(
        x=alt.X(metric + ":Q", title=metric.replace("_", " ")),
        y=alt.Y("Property Name:N", sort="-x", title="Property"),
        tooltip=["Property Name", metric],
        color=alt.Color(metric + ":Q", legend=None),
    )
    .properties(height=500)
)

st.altair_chart(chart, use_container_width=True)

# -----------------------------
# TABLE
# -----------------------------
st.subheader("Benchmark Table")
st.dataframe(bench)
