import streamlit as st
import altair as alt
import pandas as pd

from utils.load_data import load_property_ledger
from utils.metrics import portfolio_metrics
from utils.charts import (
    cost_trend_chart,
    usage_trend_chart,
    spend_by_utility_chart
)

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None:
    st.error("No Excel file found in /data. Please upload a file.")
    st.stop()

# -----------------------------
# FIX BILLING DATE
# -----------------------------
if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
    last_dt = df["Billing Date"].max()
    if pd.notna(last_dt):
        last_updated = last_dt.strftime("%b %d, %Y")
    else:
        last_updated = "N/A"
else:
    last_updated = "N/A"

# -----------------------------
# METRICS
# -----------------------------
metrics = portfolio_metrics(df)

# -----------------------------
# HEADER
# -----------------------------
st.title("🏨 Portfolio Utility Dashboard")

st.markdown(
    f"**Last Updated:** {last_updated}"
)

colA, colB, colC, colD = st.columns(4)

colA.metric("Years", metrics["years"])
colB.metric("Total Spend", f"${metrics['total_spend']:,.0f}" if metrics["total_spend"] else "N/A")
colC.metric("Total Usage", f"{metrics['total_usage']:,.0f}" if metrics["total_usage"] else "N/A")
colD.metric("Bills Count", metrics["bills_count"])

# -----------------------------
# FILTERS
# -----------------------------
st.subheader("Filters")

properties = ["All"] + sorted(df["Property Name"].unique())
utilities = ["All"] + sorted(df["Utility"].unique())

col1, col2 = st.columns(2)
selected_property = col1.selectbox("Property", properties)
selected_utility = col2.selectbox("Utility", utilities)

filtered_df = df.copy()

if selected_property != "All":
    filtered_df = filtered_df[filtered_df["Property Name"] == selected_property]

if selected_utility != "All":
    filtered_df = filtered_df[filtered_df["Utility"] == selected_utility]

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("Spend Trend")
st.altair_chart(cost_trend_chart(filtered_df), use_container_width=True)

st.subheader("Usage Trend")
st.altair_chart(usage_trend_chart(filtered_df), use_container_width=True)

st.subheader("Spend by Utility")
st.altair_chart(spend_by_utility_chart(filtered_df), use_container_width=True)
