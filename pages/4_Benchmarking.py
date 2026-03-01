import streamlit as st

# Correct guard: check the persistent key
if "uploaded_file_obj" not in st.session_state:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file in the sidebar.")
    st.stop()

import altair as alt
from utils.load_data import load_property_ledger

df, month_order = load_property_ledger()

st.title("📊 Portfolio Benchmarking")

metric = st.selectbox(
    "Benchmark Metric",
    [
        "Cost_per_Occupied_Room",
        "Cost_per_Available_Room",
        "Usage_per_Occupied_Room",
        "Usage_per_Available_Room",
        "Cost_per_Unit",
    ],
)

latest = df.sort_values("Billing Date").groupby("Property Name").tail(3)
bench = latest.groupby("Property Name", as_index=False)[metric].mean()

bench = bench.sort_values(metric, ascending=True)

chart = (
    alt.Chart(bench)
    .mark_bar()
    .encode(
        x=alt.X(metric + ":Q"),
        y=alt.Y("Property Name:N", sort="-x"),
        tooltip=["Property Name", metric],
    )
)

st.altair_chart(chart, use_container_width=True)

st.subheader("Benchmark Table")

st.dataframe(bench, use_container_width=True)
