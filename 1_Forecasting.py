import streamlit as st
import altair as alt
from prophet import Prophet
from utils.load_data import load_property_ledger

st.set_page_config(page_title="Forecasting – gforge1", layout="wide")

df, month_order = load_property_ledger()

st.title("📈 Forecasting Center")
st.write("Forecasting portfolio and weather-normalized performance across properties and utilities.")

# -----------------------------
# FILTERS
# -----------------------------
col1, col2, col3 = st.columns(3)
prop = col1.selectbox("Property", ["All"] + sorted(df["Property Name"].unique()))
util = col2.selectbox("Utility", ["All"] + sorted(df["Utility"].unique()))
target = col3.selectbox(
    "Forecast Target",
    ["Spend ($ Amount)", "Usage", "Usage per HDD"]
)

f = df.copy()
if prop != "All":
    f = f[f["Property Name"] == prop]
if util != "All":
    f = f[f["Utility"] == util]

# -----------------------------
# BUILD TIME SERIES
# -----------------------------
if target == "Spend ($ Amount)":
    ts = (
        f.groupby("Billing Date", as_index=False)["$ Amount"].sum()
        .rename(columns={"Billing Date": "ds", "$ Amount": "y"})
    )
    y_label = "Forecasted Spend"
elif target == "Usage":
    ts = (
        f.groupby("Billing Date", as_index=False)["Usage"].sum()
        .rename(columns={"Billing Date": "ds", "Usage": "y"})
    )
    y_label = "Forecasted Usage"
else:  # Usage per HDD
    ts = (
        f.groupby("Billing Date", as_index=False)["Usage_per_HDD"].mean()
        .rename(columns={"Billing Date": "ds", "Usage_per_HDD": "y"})
    )
    y_label = "Forecasted Usage per HDD"

st.subheader(f"Time Series – {target}")

if len(ts) < 5:
    st.warning("Not enough data points to generate a reliable forecast.")
else:
    st.line_chart(ts.set_index("ds")["y"])

    # -----------------------------
    # PROPHET FORECAST
    # -----------------------------
    st.subheader(f"Prophet Forecast – {y_label}")

    model = Prophet()
    model.fit(ts)

    future = model.make_future_dataframe(periods=180)
    forecast = model.predict(future)

    base = alt.Chart(forecast).encode(x="ds:T")
    line = base.mark_line(color="#1F618D").encode(y="yhat:Q")
    band = base.mark_area(opacity=0.2).encode(y="yhat_lower:Q", y2="yhat_upper:Q")

    st.altair_chart((band + line).properties(height=400), use_container_width=True)
