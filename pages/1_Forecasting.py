import streamlit as st
import pandas as pd
import altair as alt
from prophet import Prophet
from utils.load_data import load_property_ledger

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

# Ensure Billing Date is datetime
df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

st.title("📈 Forecasting Center")

# -----------------------------
# FILTERS
# -----------------------------
col1, col2, col3 = st.columns(3)

prop = col1.selectbox("Property", ["All"] + sorted(df["Property Name"].unique()))
util = col2.selectbox("Utility", ["All"] + sorted(df["Utility"].unique()))
target = col3.selectbox("Forecast Target", ["Spend ($ Amount)", "Usage"])

# -----------------------------
# APPLY FILTERS
# -----------------------------
f = df.copy()

if prop != "All":
    f = f[f["Property Name"] == prop]

if util != "All":
    f = f[f["Utility"] == util]

if f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# BUILD TIME SERIES
# -----------------------------
if target == "Spend ($ Amount)":
    ts = (
        f.groupby("Billing Date", as_index=False)["$ Amount"]
        .sum()
        .rename(columns={"Billing Date": "ds", "$ Amount": "y"})
    )
else:  # Usage
    ts = (
        f.groupby("Billing Date", as_index=False)["Usage"]
        .sum()
        .rename(columns={"Billing Date": "ds", "Usage": "y"})
    )

# Prophet requires no NaN
ts = ts.dropna()

if ts.empty:
    st.warning("Not enough data to build a forecast.")
    st.stop()

# -----------------------------
# RUN PROPHET
# -----------------------------
m = Prophet()
m.fit(ts)

future = m.make_future_dataframe(periods=12, freq="MS")
forecast = m.predict(future)

# -----------------------------
# CHART
# -----------------------------
st.subheader("Forecast")

chart = (
    alt.Chart(forecast)
    .mark_line()
    .encode(
        x="ds:T",
        y="yhat:Q",
        tooltip=["ds", "yhat", "yhat_lower", "yhat_upper"]
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)
