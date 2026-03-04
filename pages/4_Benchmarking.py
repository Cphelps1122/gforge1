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

if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

st.title("📊 Portfolio Benchmarking")

# -----------------------------
# FILTERS
# -----------------------------
col1, col2 = st.columns(2)

years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []
selected_year = col1.selectbox("Year", years if years else [None])

metric = col2.selectbox(
    "Benchmark Metric",
    [
        "CPOR",                      # Cost per Occupied Room
        "CPAR",                      # Cost per Available Room
        "Usage_per_Occupied_Room",
        "Usage_per_Available_Room",
        "Cost_per_Unit",
    ],
)

f = df.copy()
if selected_year is not None:
    f = f[f["Year"] == selected_year]

if f.empty:
    st.warning("No data available for the selected year.")
    st.stop()

# -----------------------------
# COMPUTE BENCHMARK VALUES
# -----------------------------
bench = (
    f.groupby("Property Name", as_index=False)[metric]
    .mean()
    .dropna(subset=[metric])
)

if bench.empty:
    st.warning("No valid benchmark data for this metric/year.")
    st.stop()

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
