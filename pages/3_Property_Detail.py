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

st.title("Property Detail")

# -----------------------------
# PROPERTY SELECTOR
# -----------------------------
prop = st.selectbox("Select Property", sorted(df["Property Name"].unique()))

# Filter to selected property
f = df[df["Property Name"] == prop].copy()

# Drop rows missing Year or Month (bad Billing Date)
f = f.dropna(subset=["Year", "Month"])

if f.empty:
    st.warning("No data available for this property.")
    st.stop()

# -----------------------------
# SUMMARY METRICS
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Spend", f"${f['$ Amount'].sum():,.0f}")
col2.metric("Total Usage", f"{f['Usage'].sum():,.0f}")
col3.metric("Bills Count", len(f))

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("Spend Trend")

spend_chart = (
    alt.Chart(f)
    .mark_line(point=True)
    .encode(
        x=alt.X("Billing Date:T", title="Billing Date"),
        y=alt.Y("$ Amount:Q", title="Spend ($)"),
        tooltip=["Billing Date", "$ Amount"]
    )
    .properties(height=300)
)

st.altair_chart(spend_chart, use_container_width=True)

st.subheader("Usage Trend")

usage_chart = (
    alt.Chart(f)
    .mark_line(point=True)
    .encode(
        x=alt.X("Billing Date:T", title="Billing Date"),
        y=alt.Y("Usage:Q", title="Usage"),
        tooltip=["Billing Date", "Usage"]
    )
    .properties(height=300)
)

st.altair_chart(usage_chart, use_container_width=True)

# -----------------------------
# RAW TABLE
# -----------------------------
st.subheader("Raw Data")
st.dataframe(f)
