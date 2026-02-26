import streamlit as st
import altair as alt
from utils.load_data import load_property_ledger

st.set_page_config(page_title="Property Detail – gforge1", layout="wide")

# Load data
df, month_order = load_property_ledger()

# -----------------------------
# PAGE HEADER
# -----------------------------
st.title("🏨 Property Detail")

# Property selector
prop = st.selectbox("Select Property", sorted(df["Property Name"].unique()))
f = df[df["Property Name"] == prop].copy()

# -----------------------------
# OCCUPANCY METRICS
# -----------------------------
st.subheader(f"{prop} – Occupancy & Efficiency Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Avg CPOR (Cost per Occupied Room)",
              f"${f['Cost_per_Occupied_Room'].mean():.2f}")

with col2:
    st.metric("Avg CPAR (Cost per Available Room)",
              f"${f['Cost_per_Available_Room'].mean():.2f}")

with col3:
    st.metric("Usage per Occupied Room",
              f"{f['Usage_per_Occupied_Room'].mean():.2f}")

with col4:
    st.metric("Usage per Available Room",
              f"{f['Usage_per_Available_Room'].mean():.2f}")

# -----------------------------
# UTILITY BREAKDOWN
# -----------------------------
st.subheader("Utility Breakdown")

util_breakdown = (
    f.groupby("Utility", as_index=False)[["$ Amount", "Usage"]].sum()
)

col5, col6 = st.columns(2)

with col5:
    st.markdown("#### Spend by Utility")
    chart_spend = (
        alt.Chart(util_breakdown)
        .mark_bar()
        .encode(
            x="Utility:N",
            y="$ Amount:Q",
            tooltip=["Utility", "$ Amount"]
        )
    )
    st.altair_chart(chart_spend.properties(height=320), use_container_width=True)

with col6:
    st.markdown("#### Usage by Utility")
    chart_usage = (
        alt.Chart(util_breakdown)
        .mark_bar()
        .encode(
            x="Utility:N",
            y="Usage:Q",
            tooltip=["Utility", "Usage"]
        )
    )
    st.altair_chart(chart_usage.properties(height=320), use_container_width=True)

# -----------------------------
# WEATHER-NORMALIZED USAGE TREND
# -----------------------------
st.subheader("Weather-Normalized Usage Trend")

weather_norm = (
    f.groupby(["Year", "Month"], as_index=False)[["Usage_per_HDD", "Usage_per_CDD"]].mean()
)

chart_weather = (
    alt.Chart(weather_norm)
    .mark_line(point=True)
    .encode(
        x=alt.X("Month", sort=month_order),
        y="Usage_per_HDD",
        color="Year:N",
        tooltip=["Year", "Month", "Usage_per_HDD", "Usage_per_CDD"]
    )
)

st.altair_chart(chart_weather.properties(height=320), use_container_width=True)

# -----------------------------
# RAW BILL LEDGER
# -----------------------------
st.subheader("Bill Ledger")

ledger_cols = [
    "Billing Date", "Utility", "Usage", "$ Amount",
    "Number Days Billed", "Read period",
    "Previous Reading", "Current Reading",
    "Occupied Rooms", "# Units",
    "Cost_per_Occupied_Room", "Cost_per_Available_Room", "CDD", "HDD", "Usage_per_HDD", "Usage_per_CDD"
]

st.dataframe(
    f[ledger_cols].sort_values("Billing Date"),
    use_container_width=True,
    height=450
)