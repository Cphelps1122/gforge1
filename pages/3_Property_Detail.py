import streamlit as st

# Require uploaded file BEFORE anything else
if "uploaded_file" not in st.session_state or st.session_state["uploaded_file"] is None:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file in the sidebar.")
    st.stop()

import altair as alt
from utils.load_data import load_property_ledger

df, month_order = load_property_ledger()

st.title("🏨 Property Detail")

prop = st.selectbox("Select Property", sorted(df["Property Name"].unique()))
f = df[df["Property Name"] == prop].copy()

st.subheader(f"{prop} – Occupancy & Efficiency Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg CPOR", f"${f['Cost_per_Occupied_Room'].mean():.2f}")
col2.metric("Avg CPAR", f"${f['Cost_per_Available_Room'].mean():.2f}")
col3.metric("Avg Usage/Occ Room", f"{f['Usage_per_Occupied_Room'].mean():.2f}")
col4.metric("Avg Usage/Avail Room", f"{f['Usage_per_Available_Room'].mean():.2f}")

st.subheader("Monthly Spend & Usage")

m = f.groupby(["Year", "Month"], as_index=False).agg({
    "$ Amount": "sum",
    "Usage": "sum"
})

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