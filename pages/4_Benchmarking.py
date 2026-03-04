import streamlit as st
import pandas as pd
import altair as alt

from utils.load_data import load_property_ledger

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

# Ensure Year exists
if "Year" not in df.columns and "Billing Date" in df.columns:
    df["Year"] = df["Billing Date"].dt.year

st.title("📊 Portfolio Benchmarking Platform")

# -----------------------------
# INFO / LEGEND
# -----------------------------
with st.expander("ℹ️ Benchmarking Definitions"):
    st.markdown("""
### **Key Benchmarking Metrics**

**CPOR (Cost per Occupied Room)**  
Total spend divided by occupied rooms. Lower is better.

**CPAR (Cost per Available Room)**  
Spend divided by total rooms. Normalizes for property size.

**Cost per Unit**  
Spend divided by usage. Indicates rate efficiency.

**Usage per Occupied Room**  
How much utility is consumed per occupied room.

**YOY Change**  
Year-over-year percent change.

**Outlier**  
A property whose metric is statistically far from the portfolio average (high Z-score).
""")

# -----------------------------
# FILTERS
# -----------------------------
col_f1, col_f2, col_f3 = st.columns(3)

years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []
selected_year = col_f1.selectbox("Benchmark Year", years if years else [None])

utilities = ["All"] + sorted(df["Utility"].unique()) if "Utility" in df.columns else ["All"]
selected_utility = col_f2.selectbox("Utility Filter", utilities)

metric_category = col_f3.selectbox(
    "Metric Category",
    [
        "Cost Efficiency",
        "Usage Efficiency",
        "Rate Efficiency",
        "Occupancy-Normalized",
    ],
)

f = df.copy()
if selected_year is not None:
    f = f[f["Year"] == selected_year]
if selected_utility != "All" and "Utility" in f.columns:
    f = f[f["Utility"] == selected_utility]

if f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# EXECUTIVE BENCHMARKING KPIs (NOW FIRST)
# -----------------------------
st.subheader("🏆 Executive Benchmarking KPIs")

total_spend = f["$ Amount"].sum() if "$ Amount" in f.columns else None
total_usage = f["Usage"].sum() if "Usage" in f.columns else None
avg_cpor = f["CPOR"].mean() if "CPOR" in f.columns else None
avg_cpar = f["CPAR"].mean() if "CPAR" in f.columns else None

# YOY vs previous year
if "Year" in df.columns and selected_year is not None:
    prev_year = selected_year - 1
    prev = df[df["Year"] == prev_year]
    py_spend = prev["$ Amount"].sum() if "$ Amount" in prev.columns else None
    py_usage = prev["Usage"].sum() if "Usage" in prev.columns else None
    py_cpor = prev["CPOR"].mean() if "CPOR" in prev.columns else None
    py_cpar = prev["CPAR"].mean() if "CPAR" in prev.columns else None

    yoy_spend = (
        (total_spend - py_spend) / py_spend * 100
        if py_spend not in (0, None) and total_spend is not None
        else None
    )
    yoy_usage = (
        (total_usage - py_usage) / py_usage * 100
        if py_usage not in (0, None) and total_usage is not None
        else None
    )
    yoy_cpor = (
        (avg_cpor - py_cpor) / py_cpor * 100
        if py_cpor not in (0, None) and avg_cpor is not None
        else None
    )
    yoy_cpar = (
        (avg_cpar - py_cpar) / py_cpar * 100
        if py_cpar not in (0, None) and avg_cpar is not None
        else None
    )
else:
    yoy_spend = yoy_usage = yoy_cpor = yoy_cpar = None

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Spend", f"${total_spend:,.0f}" if total_spend is not None else "N/A")
k2.metric("Total Usage", f"{total_usage:,.0f}" if total_usage is not None else "N/A")
k3.metric("Avg CPOR", f"${avg_cpor:,.2f}" if avg_cpor is not None else "N/A")
k4.metric("Avg CPAR", f"${avg_cpar:,.2f}" if avg_cpar is not None else "N/A")

k5, k6, k7, k8 = st.columns(4)
k5.metric("YOY Spend Change", f"{yoy_spend:.1f}%" if yoy_spend is not None else "N/A")
k6.metric("YOY Usage Change", f"{yoy_usage:.1f}%" if yoy_usage is not None else "N/A")
k7.metric("YOY CPOR Change", f"{yoy_cpor:.1f}%" if yoy_cpor is not None else "N/A")
k8.metric("YOY CPAR Change", f"{yoy_cpar:.1f}%" if yoy_cpar is not None else "N/A")

# -----------------------------
# METRIC SELECTION BY CATEGORY
# -----------------------------
if metric_category == "Cost Efficiency":
    metric_options = ["CPOR", "CPAR", "Cost_per_Unit"]
elif metric_category == "Usage Efficiency":
    metric_options = ["Usage_per_Occupied_Room"]
elif metric_category == "Rate Efficiency":
    metric_options = ["Cost_per_Unit"]
else:
    metric_options = ["CPOR", "Usage_per_Occupied_Room"]

available_metrics = [m for m in metric_options if m in f.columns]
selected_metric = st.selectbox("Benchmark Metric", available_metrics)

# -----------------------------
# BUILD RANK DF (used in summary + ranking)
# -----------------------------
rank_df = (
    f.groupby("Property Name", as_index=False)[selected_metric]
    .mean()
    .dropna(subset=[selected_metric])
)

if not rank_df.empty:
    rank_df = rank_df.sort_values(selected_metric, ascending=True)
    rank_df["Rank"] = range(1, len(rank_df) + 1)

# -----------------------------
# OUTLIER DETECTION (used in summary + outlier section)
# -----------------------------
outlier_rows = []
outlier_metrics = [
    ("CPOR", "CPOR"),
    ("CPAR", "CPAR"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occ Room"),
]

for col_name, label in outlier_metrics:
    if col_name in f.columns:
        agg = (
            f.groupby("Property Name", as_index=False)[col_name]
            .mean()
            .dropna(subset=[col_name])
        )
        if not agg.empty:
            mean = agg[col_name].mean()
            std = agg[col_name].std()
            if std and std > 0:
                agg["Z"] = (agg[col_name] - mean) / std
                for _, row in agg.iterrows():
                    if abs(row["Z"]) >= 2:
                        outlier_rows.append(
                            {
                                "Property Name": row["Property Name"],
                                "Metric": label,
                                "Value": round(row[col_name], 3),
                                "Z-Score": round(row["Z"], 2),
                            }
                        )

# -----------------------------
# BENCHMARKING SUMMARY (NOW SECOND)
# -----------------------------
st.subheader("📌 Benchmarking Summary")

summary_lines = []

if rank_df is not None and not rank_df.empty:
    best_prop = rank_df.iloc[0]["Property Name"]
    worst_prop = rank_df.iloc[-1]["Property Name"]
    summary_lines.append(f"- **Best performer for {selected_metric.replace('_', ' ')}:** {best_prop}")
    summary_lines.append(f"- **Lowest performer for {selected_metric.replace('_', ' ')}:** {worst_prop}")

if outlier_rows:
    summary_lines.append(f"- **Outliers detected:** {len(outlier_rows)} properties show unusual efficiency patterns.")
else:
    summary_lines.append("- No strong outliers detected across key efficiency metrics.")

if yoy_cpor is not None:
    if yoy_cpor < 0:
        summary_lines.append(f"- **Portfolio CPOR improved** by {abs(yoy_cpor):.1f}% vs prior year.")
    elif yoy_cpor > 0:
        summary_lines.append(f"- **Portfolio CPOR worsened** by {yoy_cpor:.1f}% vs prior year.")
    else:
        summary_lines.append("- **Portfolio CPOR unchanged** vs prior year.")

if yoy_cpar is not None:
    if yoy_cpar < 0:
        summary_lines.append(f"- **Portfolio CPAR improved** by {abs(yoy_cpar):.1f}% vs prior year.")
    elif yoy_cpar > 0:
        summary_lines.append(f"- **Portfolio CPAR worsened** by {yoy_cpar:.1f}% vs prior year.")
    else:
        summary_lines.append("- **Portfolio CPAR unchanged** vs prior year.")

if not summary_lines:
    summary_lines.append("No significant benchmarking insights could be derived with the current filters.")

st.markdown("\n".join(summary_lines))

# -----------------------------
# PROPERTIES REQUIRING ATTENTION (NOW THIRD)
# -----------------------------
st.subheader("🚨 Properties Requiring Attention (Outliers)")

if outlier_rows:
    st.dataframe(pd.DataFrame(outlier_rows))
else:
    st.info("No strong outliers detected based on current thresholds.")

# -----------------------------
# PORTFOLIO EFFICIENCY RANKING
# -----------------------------
st.subheader("🏅 Portfolio Efficiency Ranking")

if rank_df.empty:
    st.info("No data available to rank properties for this metric.")
else:
    chart_rank = (
        alt.Chart(rank_df)
        .mark_bar()
        .encode(
            x=alt.X(selected_metric + ":Q", title=selected_metric.replace("_", " ")),
            y=alt.Y("Property Name:N", sort="-x", title="Property"),
            color=alt.Color(selected_metric + ":Q", legend=None),
            tooltip=["Property Name", selected_metric, "Rank"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart_rank, use_container_width=True)
    st.dataframe(rank_df)

# -----------------------------
# EFFICIENCY SCORECARDS
# -----------------------------
st.subheader("📇 Efficiency Scorecards by Property")

metrics_to_grade = [
    ("CPOR", "CPOR"),
    ("CPAR", "CPAR"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occ Room"),
]

score_rows = []

for prop_name, group in f.groupby("Property Name"):
    row = {"Property Name": prop_name}
    for col_name, label in metrics_to_grade:
        if col_name in f.columns:
            prop_val = group[col_name].mean()
            port_val = f[col_name].mean()
            if pd.notna(prop_val) and pd.notna(port_val) and port_val != 0:
                diff_pct = (prop_val - port_val) / port_val * 100
                if diff_pct <= -20:
                    grade = "A"
                elif diff_pct <= -10:
                    grade = "B"
                elif abs(diff_pct) <= 10:
                    grade = "C"
                elif diff_pct <= 25:
                    grade = "D"
                else:
                    grade = "F"
                row[label + " Grade"] = grade
            else:
                row[label + " Grade"] = "N/A"
        else:
            row[label + " Grade"] = "N/A"
    score_rows.append(row)

if score_rows:
    st.dataframe(pd.DataFrame(score_rows))
else:
    st.info("Not enough data to compute efficiency scorecards.")

# -----------------------------
# SCATTERPLOTS
# -----------------------------
st.subheader("📈 Benchmarking Scatterplots")

scatter_cols = st.columns(2)

with scatter_cols[0]:
    st.markdown("**Spend vs Usage**")
    if {"$ Amount", "Usage", "Property Name"}.issubset(f.columns):
        agg_scatter = (
            f.groupby("Property Name", as_index=False)[["$ Amount", "Usage"]]
            .sum()
            .rename(columns={"$ Amount": "Spend"})
        )
        chart_scatter1 = (
            alt.Chart(agg_scatter)
            .mark_circle(size=120)
            .encode(
                x=alt.X("Usage:Q", title="Usage"),
                y=alt.Y("Spend:Q", title="Spend ($)"),
                tooltip=["Property Name", "Usage", "Spend"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_scatter1, use_container_width=True)
    else:
        st.info("Spend vs Usage scatterplot not available.")

with scatter_cols[1]:
    st.markdown("**CPOR vs CPAR**")
    if {"CPOR", "CPAR", "Property Name"}.issubset(f.columns):
        agg_eff = (
            f.groupby("Property Name", as_index=False)[["CPOR", "CPAR"]]
            .mean()
            .dropna(subset=["CPOR", "CPAR"])
        )
        if not agg_eff.empty:
            chart_scatter2 = (
                alt.Chart(agg_eff)
                .mark_circle(size=120)
                .encode(
                    x=alt.X("CPOR:Q", title="CPOR"),
                    y=alt.Y("CPAR:Q", title="CPAR"),
                    tooltip=["Property Name", "CPOR", "CPAR"],
                )
                .properties(height=350)
            )
            st.altair_chart(chart_scatter2, use_container_width=True)
        else:
            st.info("Not enough CPOR/CPAR data for scatterplot.")
    else:
        st.info("CPOR/CPAR scatterplot not available.")

# -----------------------------
# HEATMAP
# -----------------------------
st.subheader("🔥 Portfolio Efficiency Heatmap")

heat_metrics = [
    ("CPOR", "CPOR"),
    ("CPAR", "CPAR"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occ Room"),
]

heat_rows = []

for prop_name, group in f.groupby("Property Name"):
    for col_name, label in heat_metrics:
        if col_name in f.columns:
            val = group[col_name].mean()
            if pd.notna(val):
                heat_rows.append(
                    {"Property Name": prop_name, "Metric": label, "Value": val}
                )

if heat_rows:
    heat_df = pd.DataFrame(heat_rows)
    chart_heat = (
        alt.Chart(heat_df)
        .mark_rect()
        .encode(
            x=alt.X("Metric:N", title="Metric"),
            y=alt.Y("Property Name:N", title="Property"),
            color=alt.Color("Value:Q", title="Value", scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
            tooltip=["Property Name", "Metric", "Value"],
        )
        .properties(height=500)
    )
    st.altair_chart(chart_heat, use_container_width=True)
else:
    st.info("Not enough data to build heatmap.")

# -----------------------------
# UTILITY-LEVEL BENCHMARKING
# -----------------------------
st.subheader("🔌 Utility-Level Benchmarking")

if "Utility" in f.columns and "Property Name" in f.columns:
    util_metric = st.selectbox(
        "Utility Benchmark Metric",
        [m for m in ["CPOR", "CPAR", "Cost_per_Unit", "Usage_per_Occupied_Room"] if m in f.columns],
    )

    if util_metric:
        util_df = (
            f.groupby(["Utility", "Property Name"], as_index=False)[util_metric]
            .mean()
            .dropna(subset=[util_metric])
        )

        if not util_df.empty:
            chart_util = (
                alt.Chart(util_df)
                .mark_bar()
                .encode(
                    x=alt.X(util_metric + ":Q", title=util_metric.replace("_", " ")),
                    y=alt.Y("Property Name:N", sort="-x", title="Property"),
                    color=alt.Color("Utility:N", title="Utility"),
                    tooltip=["Property Name", "Utility", util_metric],
                )
                .properties(height=500)
            )
            st.altair_chart(chart_util, use_container_width=True)
        else:
            st.info("No utility-level data available for this metric.")
    else:
        st.info("No utility-level metrics available.")
else:
    st.info("Utility-level benchmarking not available.")
