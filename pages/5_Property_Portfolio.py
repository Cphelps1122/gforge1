import streamlit as st
import pandas as pd
import numpy as np
from utils.load_data import load_property_ledger
from components.header import render_header

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
render_header()

# ─────────────────────────────────────────────
# PAGE CSS — Enterprise Dark Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Summary Bar ─────────────────────────── */
.summary-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
    flex-wrap: wrap;
}
.summary-tile {
    flex: 1 1 120px;
    background: linear-gradient(135deg, #1a1f2e 0%, #232a3d 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 18px 14px;
    text-align: center;
    min-width: 120px;
}
.summary-tile .label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #8892a4;
    margin-bottom: 6px;
}
.summary-tile .value {
    font-size: 22px;
    font-weight: 700;
    color: #f0f2f6;
}

/* ── Property Card ───────────────────────── */
.prop-card {
    max-width: 640px;
    margin: 0 auto;
    background: linear-gradient(145deg, #1a1f2e 0%, #212839 100%);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 0;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.28);
}
.card-header {
    padding: 24px 28px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.card-title {
    font-size: 20px;
    font-weight: 700;
    color: #f0f2f6;
    margin: 0;
}
.utility-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 10px;
}
.util-tag {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(96,165,250,0.12);
    color: #60a5fa;
    border: 1px solid rgba(96,165,250,0.2);
}
.status-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 3px 12px;
    border-radius: 20px;
}
.status-active {
    background: rgba(52,211,153,0.12);
    color: #34d399;
    border: 1px solid rgba(52,211,153,0.25);
}
.status-inactive {
    background: rgba(251,146,60,0.12);
    color: #fb923c;
    border: 1px solid rgba(251,146,60,0.25);
}

/* ── KPI Strip ───────────────────────────── */
.kpi-strip {
    display: flex;
    padding: 20px 28px;
    gap: 0;
}
.kpi-cell {
    flex: 1;
    text-align: center;
    border-right: 1px solid rgba(255,255,255,0.06);
    padding: 0 8px;
}
.kpi-cell:last-child { border-right: none; }
.kpi-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #8892a4;
    margin-bottom: 4px;
}
.kpi-value {
    font-size: 18px;
    font-weight: 700;
    color: #f0f2f6;
}
.kpi-sub {
    font-size: 11px;
    font-weight: 600;
    margin-top: 3px;
}
.kpi-up   { color: #f87171; }   /* red  — costs rising = bad   */
.kpi-down { color: #34d399; }   /* green — costs falling = good */
.kpi-flat { color: #8892a4; }

/* ── Sparkline Section ───────────────────── */
.sparkline-section {
    padding: 16px 28px 20px;
    border-top: 1px solid rgba(255,255,255,0.05);
}
.sparkline-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #8892a4;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
if "Year" not in df.columns and "Billing Date" in df.columns:
    df["Year"] = df["Billing Date"].dt.year
if "Month_Num" not in df.columns and "Billing Date" in df.columns:
    df["Month_Num"] = df["Billing Date"].dt.month

st.title("Property Portfolio")


# ─────────────────────────────────────────────
# PURE SVG SPARKLINE GENERATOR
# ─────────────────────────────────────────────
def make_sparkline(values, width=540, height=48, stroke_width=2):
    """Pure SVG sparkline — no external libraries.
    Colors INVERTED for costs: green = falling (good), red = rising (bad)."""
    vals = [float(v) for v in values if pd.notna(v)]
    if len(vals) < 2:
        return ""

    mn, mx = min(vals), max(vals)
    rng = mx - mn if mx != mn else 1
    pad = 6
    usable_h = height - 2 * pad
    n = len(vals)

    pts = []
    for i, v in enumerate(vals):
        x = round(i / (n - 1) * width, 2)
        y = round(pad + usable_h - ((v - mn) / rng) * usable_h, 2)
        pts.append((x, y))

    polyline = " ".join(f"{x},{y}" for x, y in pts)

    # Trend colour — compare first-third avg to last-third avg
    third = max(1, n // 3)
    early = sum(vals[:third]) / third
    late  = sum(vals[-third:]) / third
    if late > early * 1.02:
        color = "#f87171"       # red   — costs rising
    elif late < early * 0.98:
        color = "#34d399"       # green — costs falling
    else:
        color = "#60a5fa"       # blue  — flat

    gid = f"sg{abs(hash(tuple(vals))) % 99999}"
    last_x, last_y = pts[-1]

    svg = (
        f'<svg width="100%" height="{height}" '
        f'viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="0,{height} {polyline} {width},{height}" '
        f'fill="url(#{gid})" stroke="none"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>'
        f'</svg>'
    )
    return svg


# ─────────────────────────────────────────────
# BUILD PORTFOLIO DATA (per-property aggregation)
# ─────────────────────────────────────────────
def build_portfolio(data):
    """Aggregate per-property: total cost, avg monthly, usage, YOY, sparkline data."""
    portfolio = {}
    for prop_name, grp in data.groupby("Property Name"):
        total_cost = grp["$ Amount"].sum() if "$ Amount" in grp.columns else 0
        bill_count = len(grp)
        total_usage = grp["Usage"].sum() if "Usage" in grp.columns else 0

        # Avg monthly — divide by distinct (Year, Month) combos
        if {"Year", "Month_Num"}.issubset(grp.columns):
            unique_months = grp.groupby(["Year", "Month_Num"]).ngroups
            avg_monthly = total_cost / max(unique_months, 1)
        else:
            avg_monthly = total_cost / max(bill_count, 1)

        # YOY cost change
        yoy_change = None
        if "Year" in grp.columns and grp["Year"].nunique() >= 2:
            yrs = sorted(grp["Year"].dropna().unique())
            cy, py = yrs[-1], yrs[-2]
            cy_cost = grp.loc[grp["Year"] == cy, "$ Amount"].sum() if "$ Amount" in grp.columns else 0
            py_cost = grp.loc[grp["Year"] == py, "$ Amount"].sum() if "$ Amount" in grp.columns else 0
            if py_cost and py_cost != 0:
                yoy_change = ((cy_cost - py_cost) / py_cost) * 100

        # Cost history for sparkline (monthly buckets, chronological)
        cost_history = []
        if {"Year", "Month_Num", "$ Amount"}.issubset(grp.columns):
            hist = (
                grp.groupby(["Year", "Month_Num"], as_index=False)["$ Amount"]
                .sum()
                .sort_values(["Year", "Month_Num"])
            )
            cost_history = hist["$ Amount"].tolist()

        # Utility list
        utilities = sorted(grp["Utility"].unique().tolist()) if "Utility" in grp.columns else []

        # Status — active vs stale (no bill in 120+ days)
        status = "active"
        if "Billing Date" in grp.columns:
            last_bill = grp["Billing Date"].max()
            if pd.notna(last_bill) and (pd.Timestamp.now() - last_bill).days > 120:
                status = "inactive"

        portfolio[prop_name] = {
            "total_cost":   total_cost,
            "avg_monthly":  avg_monthly,
            "total_usage":  total_usage,
            "bill_count":   bill_count,
            "yoy_change":   yoy_change,
            "cost_history": cost_history,
            "utilities":    utilities,
            "status":       status,
        }
    return portfolio


# ─────────────────────────────────────────────
# FORMATTING HELPERS
# ─────────────────────────────────────────────
def fmt_currency(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"${val / 1_000:,.1f}K"
    return f"${val:,.0f}"

def fmt_number(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if abs(val) >= 1_000_000:
        return f"{val / 1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"{val / 1_000:,.1f}K"
    return f"{val:,.0f}"


# ─────────────────────────────────────────────
# FILTERS — Utility Type  |  Property
# ─────────────────────────────────────────────
col_f1, col_f2 = st.columns(2)

all_utilities = sorted(df["Utility"].unique().tolist()) if "Utility" in df.columns else []
utility_options = ["Select All"] + all_utilities
selected_utility = col_f1.selectbox("Utility Type", utility_options, index=0)

# Apply utility filter BEFORE anything else
if selected_utility != "Select All":
    filtered_df = df[df["Utility"] == selected_utility].copy()
else:
    filtered_df = df.copy()

# Property dropdown — repopulates based on utility filter
avail_props = sorted(filtered_df["Property Name"].unique().tolist()) if "Property Name" in filtered_df.columns else []
if not avail_props:
    st.warning("No properties found for the selected utility filter.")
    st.stop()

selected_property = col_f2.selectbox("Select Property", avail_props, index=0)


# ─────────────────────────────────────────────
# SUMMARY BAR — aggregate across ALL properties
#   (scoped to the selected utility filter)
# ─────────────────────────────────────────────
total_spend_all  = filtered_df["$ Amount"].sum() if "$ Amount" in filtered_df.columns else 0
total_usage_all  = filtered_df["Usage"].sum()    if "Usage"    in filtered_df.columns else 0
property_count   = filtered_df["Property Name"].nunique() if "Property Name" in filtered_df.columns else 0
bill_count_all   = len(filtered_df)
avg_cpor = filtered_df["CPOR"].mean() if "CPOR" in filtered_df.columns and not filtered_df["CPOR"].isna().all() else None
avg_cpar = filtered_df["CPAR"].mean() if "CPAR" in filtered_df.columns and not filtered_df["CPAR"].isna().all() else None

summary_html = f"""
<div class="summary-bar">
    <div class="summary-tile">
        <div class="label">Properties</div>
        <div class="value">{property_count}</div>
    </div>
    <div class="summary-tile">
        <div class="label">Total Spend</div>
        <div class="value">{fmt_currency(total_spend_all)}</div>
    </div>
    <div class="summary-tile">
        <div class="label">Total Usage</div>
        <div class="value">{fmt_number(total_usage_all)}</div>
    </div>
    <div class="summary-tile">
        <div class="label">Bills</div>
        <div class="value">{bill_count_all:,}</div>
    </div>
    <div class="summary-tile">
        <div class="label">Avg CPOR</div>
        <div class="value">{f"${avg_cpor:,.2f}" if avg_cpor is not None else "N/A"}</div>
    </div>
    <div class="summary-tile">
        <div class="label">Avg CPAR</div>
        <div class="value">{f"${avg_cpar:,.2f}" if avg_cpar is not None else "N/A"}</div>
    </div>
</div>
"""
st.markdown(summary_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RENDER SELECTED PROPERTY CARD
# ─────────────────────────────────────────────
portfolio = build_portfolio(filtered_df)

if selected_property not in portfolio:
    st.warning("No data available for the selected property.")
    st.stop()

p = portfolio[selected_property]

# Utility tags
tags_html = "".join(f'<span class="util-tag">{u}</span>' for u in p["utilities"])

# Status badge
status_cls   = "status-active" if p["status"] == "active" else "status-inactive"
status_label = "Active" if p["status"] == "active" else "Stale"

# YOY badge (inverted: red = costs rising, green = costs falling)
if p["yoy_change"] is not None:
    if p["yoy_change"] > 2:
        yoy_cls, yoy_arrow = "kpi-up", "▲"
    elif p["yoy_change"] < -2:
        yoy_cls, yoy_arrow = "kpi-down", "▼"
    else:
        yoy_cls, yoy_arrow = "kpi-flat", "●"
    yoy_html = f'<div class="kpi-sub {yoy_cls}">{yoy_arrow} {abs(p["yoy_change"]):.1f}% YOY</div>'
else:
    yoy_html = '<div class="kpi-sub kpi-flat">— No YOY</div>'

# Sparkline
sparkline_svg = make_sparkline(p["cost_history"])
sparkline_block = sparkline_svg if sparkline_svg else (
    '<div style="color:#8892a4;font-size:12px;">Not enough data for sparkline</div>'
)

card_html = f"""
<div class="prop-card">
    <!-- Header -->
    <div class="card-header">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div class="card-title">{selected_property}</div>
            <span class="status-badge {status_cls}">{status_label}</span>
        </div>
        <div class="utility-tags">{tags_html}</div>
    </div>

    <!-- KPI Strip -->
    <div class="kpi-strip">
        <div class="kpi-cell">
            <div class="kpi-label">Total Cost</div>
            <div class="kpi-value">{fmt_currency(p["total_cost"])}</div>
            {yoy_html}
        </div>
        <div class="kpi-cell">
            <div class="kpi-label">Avg Monthly</div>
            <div class="kpi-value">{fmt_currency(p["avg_monthly"])}</div>
        </div>
        <div class="kpi-cell">
            <div class="kpi-label">Total Usage</div>
            <div class="kpi-value">{fmt_number(p["total_usage"])}</div>
        </div>
        <div class="kpi-cell">
            <div class="kpi-label">Bills</div>
            <div class="kpi-value">{p["bill_count"]:,}</div>
        </div>
    </div>

    <!-- Sparkline -->
    <div class="sparkline-section">
        <div class="sparkline-label">Cost Trend</div>
        {sparkline_block}
    </div>
</div>
"""
st.markdown(card_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# NAVIGATION → Property Detail
# ─────────────────────────────────────────────
st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    if st.button("View Full Details →", use_container_width=True, type="primary"):
        st.session_state["selected_property"] = selected_property
        st.switch_page("pages/3_Property_Detail.py")
