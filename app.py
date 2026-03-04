import streamlit as st
import altair as alt
import pandas as pd

from utils.load_data import load_property_ledger
from utils.metrics import portfolio_metrics
from utils.charts import (
    cost_trend_chart,
    usage_trend_chart,
    spend_by_utility_chart,
)

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

# Last updated
if "Billing Date" in df.columns:
    last_dt = df["Billing Date"].max()
    last_updated = last_dt.strftime("%b %d, %Y") if pd.notna(last_dt) else "N/A"
else:
    last_updated = "N/A"

# -----------------------------
# HEADER
# -----------------------------
st.title("🏨 Portfolio Utility Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")

# -----------------------------
# FILTERS
# -----------------------------
col_f1, col_f2, col_f3 = st.columns(3)

properties = ["All"] + sorted(df["Property Name"].unique())
utilities = ["All"] + sorted(df["Utility"].unique())
years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []

selected_property = col_f1.selectbox("Property", properties)
selected_utility = col_f2.selectbox("Utility", utilities)
selected_years = col_f3.multiselect("Years", years, default=years)

f = df.copy()
if selected_property != "All":
    f = f[f["Property Name"] == selected_property]
if selected_utility != "All":
    f = f[f["Utility"] == selected_utility]
if selected_years:
    f = f[f["Year"].isin(selected_years)]

if f.empty:
    st.warning("No data for selected filters.")
    st.stop()

# -----------------------------
# METRICS + YOY
# -----------------------------
metrics = portfolio_metrics(f)

if "Year" in f.columns:
    current_year = max(selected_years) if selected_years else f["Year"].max()
    prev_year = current_year - 1

    cy_spend = f[f["Year"] == current_year]["$ Amount"].sum()
    py_spend = f[f["Year"] == prev_year]["$ Amount"].sum()
    yoy_spend = (cy_spend - py_spend) / py_spend * 100 if py_spend not in (0, None) else None

    cy_usage = f[f["Year"] == current_year]["Usage"].sum()
    py_usage = f[f["Year"] == prev_year]["Usage"].sum()
    yoy_usage = (cy_usage - py_usage) / py_usage * 100 if py_usage not in (0, None) else None
else:
    yoy_spend = None
    yoy_usage = None

colA, colB, colC, colD = st.columns(4)
colA.metric("Years", metrics["years"])
colB.metric(
    "Total Spend",
    f"${metrics['total_spend']:,.0f}" if metrics["total_spend"] is not None else "N/A",
)
colC.metric(
    "Total Usage",
    f"{metrics['total_usage']:,.0f}" if metrics["total_usage"] is not None else "N/A",
)
colD.metric(
    "YOY Spend Change",
    f"{yoy_spend:.1f}%" if yoy_spend is not None else "N/A",
)

# -----------------------------
# YOY TRENDS
# -----------------------------
st.subheader("Year-over-Year Spend Trend")
st.altair_chart(cost_trend_chart(f), use_container_width=True)

st.subheader("Year-over-Year Usage Trend")
st.altair_chart(usage_trend_chart(f), use_container_width=True)

# -----------------------------
# UTILITY BREAKDOWN
# -----------------------------
st.subheader("Spend by Utility (by Year)")
st.altair_chart(spend_by_utility_chart(f), use_container_width=True)
