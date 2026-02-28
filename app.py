import streamlit as st
import altair as alt
from utils.load_data import load_property_ledger
from utils.metrics import portfolio_metrics
from utils.charts import cost_trend_chart, usage_trend_chart, spend_by_property_chart
import streamlit as st
st.write("NOAA token loaded:", "NOAA_TOKEN" in st.secrets)
st.write("Token length:", len(st.secrets.get("NOAA_TOKEN", "")))

st.set_page_config(page_title="gforge1 – Utility Dashboard", layout="wide")

# -----------------------------
# SIDEBAR: FILE UPLOADER
# -----------------------------
st.sidebar.title("Upload Data File")

uploaded = st.sidebar.file_uploader(
    "Upload your McNeill Excel file",
    type=["xlsx"],
)

# ⭐ Persist file across pages
if uploaded is not None:
    st.session_state["uploaded_file_obj"] = uploaded

# ⭐ CRITICAL: ensure the file stays available even when uploaded is None
if "uploaded_file_obj" not in st.session_state:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file to begin.")
    st.stop()

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()
if df is None:
    st.error("Could not load data from uploaded file.")
    st.stop()

# ⭐ MUST come before the header
last_updated = df["Billing Date"].max()
metrics = portfolio_metrics(df)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    f"""
    <div style="background:linear-gradient(90deg,#1F618D,#2980B9);padding:15px 25px;
    border-radius:10px;color:white;margin-bottom:20px;">
        <h2>gforge1 – McNeill Utility Dashboard</h2>
        <span>Last Billing Date: {last_updated.date()}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# PORTFOLIO METRICS
# -----------------------------
st.subheader("Portfolio Overview")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Properties", metrics["properties"])
col2.metric("Utilities", metrics["utilities"])
col3.metric("Years of History", metrics["years"])
col4.metric("Total Spend", f"${metrics['total_spend']:,.0f}")
col5.metric("Total Usage", f"{metrics['total_usage']:,.0f}")
col6.metric("Avg Cost/Unit", f"${metrics['avg_cost_per_unit']:.2f}")

# -----------------------------
# FILTERS
# -----------------------------
st.subheader("Filters")

f1, f2, f3 = st.columns(3)
prop = f1.selectbox("Property", ["All"] + sorted(df["Property Name"].unique()))
util = f2.selectbox("Utility", ["All"] + sorted(df["Utility"].unique()))
year = f3.selectbox("Year", ["All"] + sorted(df["Year"].unique()))

f = df.copy()
if prop != "All":
    f = f[f["Property Name"] == prop]
if util != "All":
    f = f[f["Utility"] == util]
if year != "All":
    f = f[f["Year"] == year]

filtered_metrics = portfolio_metrics(f)

# -----------------------------
# FILTERED METRICS
# -----------------------------
st.subheader("Filtered Metrics")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Filtered Spend", f"${filtered_metrics['total_spend']:,.0f}")
c2.metric("Filtered Usage", f"{filtered_metrics['total_usage']:,.0f}")
c3.metric("Filtered Avg Cost/Unit", f"${filtered_metrics['avg_cost_per_unit']:.2f}")
c4.metric("Filtered Bills", f"{filtered_metrics['bills_count']:,}")
c5.metric("Filtered CPOR", f"${filtered_metrics['avg_cpor']:.2f}")
c6.metric("Filtered Usage/HDD", f"{f['Usage_per_HDD'].mean():.2f}")

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("Cost & Usage Trends")

row1 = st.columns(2)
row1[0].altair_chart(cost_trend_chart(f, month_order), use_container_width=True)
row1[1].altair_chart(usage_trend_chart(f, month_order), use_container_width=True)

# -----------------------------
# WEATHER-NORMALIZED TREND
# -----------------------------
st.subheader("Weather-Normalized Usage Trend")

weather_portfolio = df.groupby(["Year", "Month"], as_index=False)["Usage_per_HDD"].mean()

chart_weather = (
    alt.Chart(weather_portfolio)
    .mark_line(point=True)
    .encode(
        x=alt.X("Month", sort=month_order),
        y="Usage_per_HDD",
        color="Year:N",
        tooltip=["Year", "Month", "Usage_per_HDD"]
    )
)

st.altair_chart(chart_weather, use_container_width=True)

# -----------------------------
# SPEND BY PROPERTY
# -----------------------------
st.subheader("Spend by Property")

st.altair_chart(spend_by_property_chart(df), use_container_width=True)




