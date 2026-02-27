import streamlit as st

# ⭐ Correct guard: check the persistent key
if "uploaded_file_obj" not in st.session_state:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file in the sidebar.")
    st.stop()

import altair as alt
from utils.load_data import load_property_ledger

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("Could not load data from uploaded file.")
    st.stop()

st.title("🏨 Property Detail")

# -----------------------------
# PROPERTY SELECTOR
# -----------------------------
prop = st.selectbox("Select Property", sorted(df["Property Name"].unique()))

# Filter to selected property
f = df[df["Property Name"] == prop].copy()

# ⭐ Prevent empty-data crash
if f.empty:
    st.warning("No data available for this property.")
    st.stop()

# ⭐ Drop rows missing Year or Month (fixes your ValueError)
f = f.dropna(subset=["Year", "Month"])

if f.empty:
    st.warning("This property has no valid billing dates.")
    st.stop()

# -----------------------------
# METRICS
# -----------------------------
st.subheader(f"{prop} – Occupancy & Efficiency Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg CPOR", f"${f['Cost_per_Occupied_Room'].mean():.2f}")
col2.metric("Avg CPAR", f"${f['Cost_per_Available_Room'].mean():.2f}")
col3.metric("Avg Usage/Occ Room", f"{f['Usage_per_Occupied_Room'].mean():.2f}")
col4.metric("Avg Usage/Avail Room", f"{f['Usage_per_Available_Room'].mean():.2f}")

# -----------------------------
# MONTHLY CHARTS
# -----------------------------
st.subheader("Monthly Spend & Usage")

# Group safely
m = (
    f.groupby(["Year", "Month"], as_index=False)
     .agg({"$ Amount": "sum", "Usage": "sum"})
     .sort_values(["Year", "Month"])
)

left, right = st.columns(2)

cost_chart = (
    alt.Chart(m)
    .mark_line(point=True)
    .encode(
        x=alt.X("Month", sort=month_order),
        y="$ Amount",
        color="Year:N",
        tooltip=["Year", "Month", "$ Amount"]
    )
)

usage_chart = (
    alt.Chart(m)
    .mark_line(point=True)
    .encode(
        x=alt.X("Month", sort=month_order),
        y="Usage",
        color="Year:N",
        tooltip=["Year", "Month", "Usage"]
    )
)

left.altair_chart(cost_chart, use_container_width=True)
right.altair_chart(usage_chart, use_container_width=True)

# -----------------------------
# RAW DATA TABLE
# -----------------------------
st.subheader("Raw Bills")
st.dataframe(
    f[
        [
            "Billing Date",
            "Utility",
            "Usage",
            "$ Amount",
            "Number Days Billed",
            "Occupied Rooms",
            "# Units",
            "Cost_per_Unit",
            "Cost_per_Occupied_Room",
            "Cost_per_Available_Room",
        ]
    ].sort_values("Billing Date"),
    use_container_width=True,
)
