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

st.title("🏨 Property Energy Detail")

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

if f.empty:
    st.warning("No data available for this property and year selection.")
    st.stop()

# -----------------------------
# YOY KPIs
# -----------------------------
total_spend = f["$ Amount"].sum() if "$ Amount" in f.columns else None
total_usage = f["Usage"].sum() if "Usage" in f.columns else None

if "Year" in f.columns:
    current_year = max(selected_years) if selected_years else f["Year"].max()
    prev_year = current_year - 1

    cy_spend = f[f["Year"] == current_year]["$ Amount"].sum() if "$ Amount" in f.columns else None
    py_spend = f[f["Year"] == prev_year]["$ Amount"].sum() if "$ Amount" in f.columns else None
    yoy_spend = (
        (cy_spend - py_spend) / py_spend * 100
        if py_spend not in (0, None) and cy_spend is not None
        else None
    )

    cy_usage = f[f["Year"] == current_year]["Usage"].sum() if "Usage" in f.columns else None
    py_usage = f[f["Year"] == prev_year]["Usage"].sum() if "Usage" in f.columns else None
    yoy_usage = (
        (cy_usage - py_usage) / py_usage * 100
        if py_usage not in (0, None) and cy_usage is not None
        else None
    )

    cy_cpor = f[f["Year"] == current_year]["CPOR"].mean() if "CPOR" in f.columns else None
    py_cpor = f[f["Year"] == prev_year]["CPOR"].mean() if "CPOR" in f.columns else None
    yoy_cpor = (
        (cy_cpor - py_cpor) / py_cpor * 100
        if py_cpor not in (0, None) and cy_cpor is not None
        else None
    )
else:
    yoy_spend = yoy_usage = yoy_cpor = None

colA, colB, colC = st.columns(3)
colA.metric("Total Spend", f"${total_spend:,.0f}" if total_spend is not None else "N/A")
colB.metric("Total Usage", f"{total_usage:,.0f}" if total_usage is not None else "N/A")
colC.metric(
    "YOY Spend Change",
    f"{yoy_spend:.1f}%" if yoy_spend is not None else "N/A",
)

colD, colE = st.columns(2)
colD.metric(
    "YOY Usage Change",
    f"{yoy_usage:.1f}%" if yoy_usage is not None else "N/A",
)
colE.metric(
    "YOY CPOR Change",
    f"{yoy_cpor:.1f}%" if yoy_cpor is not None else "N/A",
)

# -----------------------------
# CPOR HERO TREND (PER PROPERTY)
# -----------------------------
st.subheader("Year-over-Year Efficiency Trend (CPOR)")

if {"CPOR", "Month_Num", "Year"}.issubset(f.columns):
    cpor_df = (
        f.groupby(["Year", "Month_Num"], as_index=False)["CPOR"]
        .mean()
        .dropna(subset=["CPOR"])
    )

    chart_cpor = (
        alt.Chart(cpor_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month_Num:O", title="Month"),
            y=alt.Y("CPOR:Q", title="Cost per Occupied Room"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Year", "Month_Num", "CPOR"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_cpor, use_container_width=True)
else:
    st.info("Not enough data to build CPOR trend for this property.")

# -----------------------------
# UTILITY BREAKDOWN (PROPERTY LEVEL)
# -----------------------------
st.subheader("Utility Spend & Usage for This Property")

if {"Utility", "Year", "$ Amount", "Usage"}.issubset(f.columns):
    util_agg = (
        f.groupby(["Utility", "Year"], as_index=False)[["$ Amount", "Usage"]]
        .sum()
    )

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.markdown("**Spend by Utility (by Year)**")
        chart_spend = (
            alt.Chart(util_agg)
            .mark_bar()
            .encode(
                x=alt.X("Utility:N", title="Utility"),
                y=alt.Y("$ Amount:Q", title="Spend ($)"),
                color=alt.Color("Year:N", title="Year"),
                tooltip=["Utility", "Year", "$ Amount"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_spend, use_container_width=True)

    with col_u2:
        st.markdown("**Usage by Utility (by Year)**")
        chart_usage = (
            alt.Chart(util_agg)
            .mark_bar()
            .encode(
                x=alt.X("Utility:N", title="Utility"),
                y=alt.Y("Usage:Q", title="Usage"),
                color=alt.Color("Year:N", title="Year"),
                tooltip=["Utility", "Year", "Usage"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_usage, use_container_width=True)
else:
    st.info("Utility-level breakdown not fully available for this property.")

# -----------------------------
# RAW TABLE
# -----------------------------
st.subheader("Raw Data")
st.dataframe(f)
