import streamlit as st
import pandas as pd
import altair as alt

from utils.load_data import load_property_ledger
from utils.charts import cost_trend_chart, usage_trend_chart

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

st.title("🏨 Property Detail")

# -----------------------------
# FILTERS
# -----------------------------
col1, col2 = st.columns(2)

properties = sorted(df["Property Name"].unique())
years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []

prop = col1.selectbox("Select Property", properties)
selected_years = col2.multiselect("Years", years, default=years)

f = df[df["Property Name"] == prop].copy()
if selected_years:
    f = f[f["Year"].isin(selected_years)]

f = f.dropna(subset=["Year", "Month"]) if {"Year", "Month"}.issubset(f.columns) else f

if f.empty:
    st.warning("No data available for this property and year selection.")
    st.stop()

# -----------------------------
# SUMMARY METRICS
# -----------------------------
colA, colB, colC = st.columns(3)

total_spend = f["$ Amount"].sum() if "$ Amount" in f.columns else None
total_usage = f["Usage"].sum() if "Usage" in f.columns else None

colA.metric("Total Spend", f"${total_spend:,.0f}" if total_spend is not None else "N/A")
colB.metric("Total Usage", f"{total_usage:,.0f}" if total_usage is not None else "N/A")
colC.metric("Bills Count", len(f))

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

if "Utility" in f.columns and "$ Amount" in f.columns and "Year" in f.columns:
    util_df = (
        f.groupby(["Utility", "Year"], as_index=False)["$ Amount"]
        .sum()
    )

    chart = (
        alt.Chart(util_df)
        .mark_bar()
        .encode(
            x=alt.X("Utility:N", title="Utility"),
            y=alt.Y("$ Amount:Q", title="Spend ($)"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Utility", "Year", "$ Amount"],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Utility breakdown not available for this dataset.")

# -----------------------------
# RAW TABLE
# -----------------------------
st.subheader("Raw Data")
st.dataframe(f)
