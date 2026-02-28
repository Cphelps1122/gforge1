import streamlit as st
import pandas as pd
from prophet import Prophet
from utils.load_data import load_property_ledger
from utils.formatting import money

st.title("Forecasting")

# Auto-load newest file
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No data available. Please add an Excel file to /data.")
    st.stop()

# -----------------------------
# Forecasting Controls
# -----------------------------
st.subheader("Forecasting Controls")

utility_types = sorted(df["Utility"].unique())
selected_utility = st.selectbox("Select Utility Type", utility_types)

df_util = df[df["Utility"] == selected_utility]

# Aggregate monthly
df_monthly = (
    df_util.groupby("Month")["$ Amount"]
    .sum()
    .reset_index()
    .sort_values("Month")
)

df_monthly.rename(columns={"Month": "ds", "$ Amount": "y"}, inplace=True)

# -----------------------------
# Prophet Model
# -----------------------------
model = Prophet()
model.fit(df_monthly)

future = model.make_future_dataframe(periods=12, freq="M")
forecast = model.predict(future)

# -----------------------------
# Display Forecast Chart
# -----------------------------
st.subheader(f"{selected_utility} — 12‑Month Cost Forecast")

fig = model.plot(forecast)
st.pyplot(fig)

# -----------------------------
# Forecast Table
# -----------------------------
st.subheader("Forecast Table")

forecast_display = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
forecast_display["yhat"] = forecast_display["yhat"].apply(money)
forecast_display["yhat_lower"] = forecast_display["yhat_lower"].apply(money)
forecast_display["yhat_upper"] = forecast_display["yhat_upper"].apply(money)

st.dataframe(forecast_display, use_container_width=True)
