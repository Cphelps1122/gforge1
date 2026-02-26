import streamlit as st
import altair as alt
from utils.load_data import load_property_ledger

st.set_page_config(page_title="Benchmarking – gforge1", layout="wide")

df, month_order = load_property_ledger()

st.title("📊 Property Benchmarking")
st.write("Compare properties on cost, usage, occupancy, and weather-normalized intensity.")

# -----------------------------
# AGGREGATE PROPERTY-LEVEL METRICS
# -----------------------------
bench = df.groupby("Property Name").agg({
    "$ Amount": "sum",
    "Usage": "sum",
    "Cost_per_Occupied_Room": "mean",
    "Cost_per_Available_Room": "mean",
    "Usage_per_Occupied_Room": "mean",
    "Usage_per_HDD": "mean",
    "Occupied Rooms": "mean",
    "# Units": "first"
}).reset_index()

bench["Occ_Ratio"] = bench["Occupied Rooms"] / bench["# Units"]

# -----------------------------
# CONTROLS
# -----------------------------
metric_choice = st.selectbox(
    "Benchmark Metric",
    [
        "Total Spend ($ Amount)",
        "Total Usage",
        "CPOR (Cost per Occupied Room)",
        "CPAR (Cost per Available Room)",
        "Usage per Occupied Room",
        "Usage per HDD",
        "Occupancy Ratio"
    ]
)

metric_map = {
    "Total Spend ($ Amount)": "$ Amount",
    "Total Usage": "Usage",
    "CPOR (Cost per Occupied Room)": "Cost_per_Occupied_Room",
    "CPAR (Cost per Available Room)": "Cost_per_Available_Room",
    "Usage per Occupied Room": "Usage_per_Occupied_Room",
    "Usage per HDD": "Usage_per_HDD",
    "Occupancy Ratio": "Occ_Ratio",
}

metric_col = metric_map[metric_choice]

st.subheader(f"Benchmark – {metric_choice}")

chart = (
    alt.Chart(bench.sort_values(metric_col, ascending=False))
    .mark_bar()
    .encode(
        x=alt.X("Property Name:N", sort="-y"),
        y=alt.Y(f"{metric_col}:Q"),
        tooltip=[
            "Property Name",
            "$ Amount",
            "Usage",
            "Cost_per_Occupied_Room",
            "Cost_per_Available_Room",
            "Usage_per_Occupied_Room",
            "Usage_per_HDD",
            "Occ_Ratio"
        ]
    )
)

st.altair_chart(chart.properties(height=400), use_container_width=True)

st.subheader("Benchmark Table")
st.dataframe(
    bench[
        [
            "Property Name",
            "$ Amount",
            "Usage",
            "Cost_per_Occupied_Room",
            "Cost_per_Available_Room",
            "Usage_per_Occupied_Room",
            "Usage_per_HDD",
            "Occ_Ratio"
        ]
    ].sort_values("$ Amount", ascending=False),
    use_container_width=True,
    height=450
)