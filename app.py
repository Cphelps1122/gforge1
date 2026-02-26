import streamlit as st
import altair as alt
from utils.load_data import load_property_ledger
from utils.metrics import portfolio_metrics
from utils.charts import cost_trend_chart, usage_trend_chart, spend_by_property_chart

st.set_page_config(page_title="gforge1 – Utility Dashboard", layout="wide")

# -----------------------------
# SIDEBAR: FILE UPLOADER + NAV
# -----------------------------
st.sidebar.title("Upload Data File")
uploaded = st.sidebar.file_uploader(
    "Upload your McNeill Excel file",
    type=["xlsx"],
    key="uploaded_file"
)

st.sidebar.title("Navigation")
st.sidebar.write("Use the sidebar to switch pages.")

# If no file, stop here
if uploaded is None:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file (with a `Property` sheet and `Provider` sheet) to begin.")
    st.stop()

# -----------------------------
# GLOBAL STYLES
# -----------------------------
st.markdown("""
<style>
.block-container {padding-top:1rem;padding-bottom:1rem;padding-left:2rem;padding-right:2rem;}
h1,h2,h3 {font-weight:600;color:#1F3B4D;}
.header-container {background:linear-gradient(90deg,#1F618D,#2980B9);padding:15px 25px;
border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.12);margin-bottom:20px;color:#ffffff;}
.metric-card {background-color:#ffffff;padding:15px 20px;border-radius:12px;
box-shadow:0 2px 8px rgba(0,0,0,0.06);}
.section-card {background-color:#ffffff;padding:20px;border-radius:12px;
box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:25px;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
with st.spinner("Loading McNeill utility ledger…"):
    df, month_order = load_property_ledger()

if df is None:
    st.error("Could not load data from uploaded file.")
    st.stop()

last_updated = df["Billing Date"].max()
metrics = portfolio_metrics(df)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    f"""
    <div class="header-container">
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

with col1:
    st.metric("Properties", metrics["properties"])
with col2:
    st.metric("Utilities", metrics["utilities"])
with col3:
    st.metric("Years of History", metrics["years"])
with col4:
    st.metric("Total Spend", f"${metrics['total_spend']:,.0f}")
with col5:
    st.metric("Total Usage", f"{metrics['total_usage']:,.0f}")
with col6:
    st.metric("Avg Cost/Unit", f"${metrics['avg_cost_per_unit']:.2f}")

col7, col8, col9 = st.columns(3)
with col7:
    st.metric("Avg CPOR", f"${metrics['avg_cpor']:.2f}")
with col8:
    st.metric("Avg CPAR", f"${metrics['avg_cpar']:.2f}")
with col9:
    st.metric("Avg Usage/HDD", f"{df['Usage_per_HDD'].mean():.2f}")

# -----------------------------
# FILTERS
# -----------------------------
st.subheader("Filters")

f1, f2, f3 = st.columns(3)

with f1:
    prop = st.selectbox("Property", ["All"] + sorted(df["Property Name"].unique()))
with f2:
    util = st.selectbox("Utility", ["All"] + sorted(df["Utility"].unique()))
with f3:
    year = st.selectbox("Year", ["All"] + sorted(df["Year"].unique()))

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

with c1:
    st.metric("Filtered Spend", f"${filtered_metrics['total_spend']:,.0f}")
with c2:
    st.metric("Filtered Usage", f"{filtered_metrics['total_usage']:,.0f}")
with c3:
    st.metric("Filtered Avg Cost/Unit", f"${filtered_metrics['avg_cost_per_unit']:.2f}")
with c4:
    st.metric("Filtered Bills", f"{filtered_metrics['bills_count']:,}")
with c5:
    st.metric("Filtered CPOR", f"${filtered_metrics['avg_cpor']:.2f}")
with c6:
    st.metric("Filtered Usage/HDD", f"{f['Usage_per_HDD'].mean():.2f}")

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("Cost & Usage Trends")

row1 = st.columns(2)

with row1[0]:
    st.markdown("#### Monthly Cost Trend")
    st.altair_chart(cost_trend_chart(f, month_order).properties(height=320), use_container_width=True)

with row1[1]:
    st.markdown("#### Monthly Usage Trend")
    st.altair_chart(usage_trend_chart(f, month_order).properties(height=320), use_container_width=True)

# -----------------------------
# WEATHER-NORMALIZED TREND
# -----------------------------
st.subheader("Weather-Normalized Usage Trend (Portfolio)")

weather_portfolio = (
    df.groupby(["Year", "Month"], as_index=False)[["Usage_per_HDD"]].mean()
)

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

st.altair_chart(chart_weather.properties(height=320), use_container_width=True)

# -----------------------------
# SPEND BY PROPERTY
# -----------------------------
st.subheader("Spend by Property")
st.altair_chart(spend_by_property_chart(df).properties(height=380), use_container_width=True)
