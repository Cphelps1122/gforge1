###############################################################################
# 5_Property_Portfolio.py  –  Premium Portfolio Dashboard
# Repo:  gforge1 (dev2 branch)  ·  pages/5_Property_Portfolio.py
#
# LIVE DATA  →  load_property_ledger() from Google Sheets
# SPARKLINES →  matplotlib (Agg backend, RGBA tuples)
# NAV        →  session_state → 3_Property_Detail.py
###############################################################################

import streamlit as st

# ── Page config MUST be the very first Streamlit call ────────────────────────
st.set_page_config(
    page_title="Property Portfolio",
    page_icon="🏢",
    layout="wide",
)

import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime, timedelta

# Matplotlib – headless backend BEFORE importing pyplot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.load_data import load_property_ledger
from components.header import render_header

# ═══════════════════════════════════════════════════════════════════════════════
# CSS  –  enterprise dark-card styling
# ═══════════════════════════════════════════════════════════════════════════════
PORTFOLIO_CSS = """
<style>
/* ── Summary bar tiles ────────────────────────────────────────────────────── */
.summary-bar {
    display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;
}
.summary-tile {
    flex: 1 1 140px;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px 16px;
    text-align: center;
    min-width: 140px;
}
.summary-tile .tile-label {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1.2px; color: #94a3b8; margin-bottom: 6px;
}
.summary-tile .tile-value {
    font-size: 22px; font-weight: 700; color: #f1f5f9;
}

/* ── Property card ────────────────────────────────────────────────────────── */
.prop-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 28px 24px;
    margin-bottom: 20px;
    transition: border-color 0.2s;
}
.prop-card:hover { border-color: #60a5fa; }

.prop-card .card-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 14px;
}
.prop-card .card-title {
    font-size: 20px; font-weight: 700; color: #f1f5f9; margin: 0;
}
.prop-card .status-pill {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; padding: 4px 12px; border-radius: 20px;
}
.pill-active  { background: #065f46; color: #6ee7b7; }
.pill-stale   { background: #78350f; color: #fcd34d; }
.pill-inactive{ background: #7f1d1d; color: #fca5a5; }

.prop-card .sparkline-wrap {
    text-align: center; margin: 14px 0 18px 0;
}
.prop-card .sparkline-wrap img {
    width: 100%; max-width: 440px; border-radius: 8px;
}

.prop-card .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
}
.metric-box {
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 10px; padding: 12px 10px; text-align: center;
}
.metric-box .m-label {
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; color: #64748b; margin-bottom: 4px;
}
.metric-box .m-value {
    font-size: 16px; font-weight: 700; color: #e2e8f0;
}
.yoy-up   { color: #f87171 !important; }
.yoy-down { color: #4ade80 !important; }
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SPARKLINE GENERATOR  (matplotlib → base64 PNG)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_sparkline(values, width=5.0, height=1.2,
                       line_color="#60a5fa",
                       fill_color=(96/255, 165/255, 250/255, 0.18)):
    """Return a base64-encoded PNG sparkline image string."""
    if not values or len(values) < 2:
        return None

    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    x = list(range(len(values)))
    ax.plot(x, values, color=line_color, linewidth=2, solid_capstyle="round")
    ax.fill_between(x, values, min(values), color=fill_color)

    # Endpoint dot
    ax.scatter([x[-1]], [values[-1]], color=line_color, s=28, zorder=5)

    ax.set_xlim(x[0], x[-1])
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, transparent=True,
                bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER  –  compute property-level metrics from filtered df
# ═══════════════════════════════════════════════════════════════════════════════
def compute_property_metrics(prop_df):
    """Return a dict of card-level KPIs for one property (filtered by utility)."""
    total_cost = prop_df["$ Amount"].sum() if "$ Amount" in prop_df.columns else 0
    total_usage = prop_df["Usage"].sum() if "Usage" in prop_df.columns else 0

    # Unique month count for Avg Monthly
    if {"Year", "Month_Num"}.issubset(prop_df.columns):
        n_months = prop_df.groupby(["Year", "Month_Num"]).ngroups
    else:
        n_months = max(prop_df.shape[0], 1)
    avg_monthly = total_cost / n_months if n_months else 0

    # YOY change
    yoy = None
    if "Year" in prop_df.columns and prop_df["Year"].nunique() >= 2:
        years = sorted(prop_df["Year"].dropna().unique())
        cy, py = years[-1], years[-2]
        cy_spend = prop_df.loc[prop_df["Year"] == cy, "$ Amount"].sum()
        py_spend = prop_df.loc[prop_df["Year"] == py, "$ Amount"].sum()
        if py_spend and py_spend != 0:
            yoy = (cy_spend - py_spend) / py_spend * 100

    # CPOR / CPAR
    avg_cpor = prop_df["CPOR"].mean() if "CPOR" in prop_df.columns else None
    avg_cpar = prop_df["CPAR"].mean() if "CPAR" in prop_df.columns else None

    # Sparkline data  –  monthly spend sorted chronologically
    spark_values = []
    if {"Year", "Month_Num", "$ Amount"}.issubset(prop_df.columns):
        grp = (
            prop_df.groupby(["Year", "Month_Num"], as_index=False)["$ Amount"]
            .sum()
            .sort_values(["Year", "Month_Num"])
        )
        spark_values = grp["$ Amount"].tolist()

    # Status  –  Active / Stale / Inactive based on last Billing Date
    status = "Inactive"
    if "Billing Date" in prop_df.columns:
        last_bill = pd.to_datetime(prop_df["Billing Date"], errors="coerce").max()
        if pd.notna(last_bill):
            days_ago = (datetime.now() - last_bill).days
            if days_ago <= 120:
                status = "Active"
            elif days_ago <= 240:
                status = "Stale"

    # Bill count
    bill_count = len(prop_df)

    return {
        "total_cost": total_cost,
        "avg_monthly": avg_monthly,
        "total_usage": total_usage,
        "yoy": yoy,
        "avg_cpor": avg_cpor,
        "avg_cpar": avg_cpar,
        "spark_values": spark_values,
        "status": status,
        "bill_count": bill_count,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER  –  single property card
# ═══════════════════════════════════════════════════════════════════════════════
def render_property_card(prop_name, m):
    """Render an enterprise-grade property card with sparkline + metrics."""

    # Status pill class
    pill_cls = {
        "Active": "pill-active",
        "Stale": "pill-stale",
        "Inactive": "pill-inactive",
    }.get(m["status"], "pill-inactive")

    # Sparkline image tag
    spark_html = ""
    spark_b64 = generate_sparkline(m["spark_values"])
    if spark_b64:
        spark_html = (
            f'<div class="sparkline-wrap">'
            f'<img src="data:image/png;base64,{spark_b64}" '
            f'alt="spend sparkline" />'
            f'</div>'
        )

    # YOY display
    if m["yoy"] is not None:
        yoy_cls = "yoy-up" if m["yoy"] > 0 else "yoy-down"
        yoy_arrow = "▲" if m["yoy"] > 0 else "▼"
        yoy_str = f'<span class="{yoy_cls}">{yoy_arrow} {abs(m["yoy"]):.1f}%</span>'
    else:
        yoy_str = "N/A"

    # Format helpers
    def fmt_dollar(v):
        return f"${v:,.0f}" if v is not None else "N/A"

    def fmt_num(v, dec=0):
        if v is None:
            return "N/A"
        return f"{v:,.{dec}f}"

    card_html = f"""
    <div class="prop-card">
      <div class="card-header">
        <h3 class="card-title">{prop_name}</h3>
        <span class="status-pill {pill_cls}">{m['status']}</span>
      </div>
      {spark_html}
      <div class="metrics-grid">
        <div class="metric-box">
          <div class="m-label">Total Cost</div>
          <div class="m-value">{fmt_dollar(m['total_cost'])}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">Avg Monthly</div>
          <div class="m-value">{fmt_dollar(m['avg_monthly'])}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">Total Usage</div>
          <div class="m-value">{fmt_num(m['total_usage'])}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">YOY Change</div>
          <div class="m-value">{yoy_str}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">Avg CPOR</div>
          <div class="m-value">{fmt_num(m['avg_cpor'], 2)}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">Avg CPAR</div>
          <div class="m-value">{fmt_num(m['avg_cpar'], 2)}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">Bills</div>
          <div class="m-value">{m['bill_count']}</div>
        </div>
      </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER  –  summary bar (portfolio-wide KPIs)
# ═══════════════════════════════════════════════════════════════════════════════
def render_summary_bar(filtered_df):
    """Render the top-of-page dark KPI tiles across the full filtered dataset."""
    prop_count = filtered_df["Property Name"].nunique() if "Property Name" in filtered_df.columns else 0
    total_spend = filtered_df["$ Amount"].sum() if "$ Amount" in filtered_df.columns else 0
    total_usage = filtered_df["Usage"].sum() if "Usage" in filtered_df.columns else 0
    bill_count = len(filtered_df)
    avg_cpor = filtered_df["CPOR"].mean() if "CPOR" in filtered_df.columns and not filtered_df["CPOR"].dropna().empty else None
    avg_cpar = filtered_df["CPAR"].mean() if "CPAR" in filtered_df.columns and not filtered_df["CPAR"].dropna().empty else None

    def fmt(v, prefix="", dec=0):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "N/A"
        return f"{prefix}{v:,.{dec}f}"

    tiles = f"""
    <div class="summary-bar">
      <div class="summary-tile">
        <div class="tile-label">Properties</div>
        <div class="tile-value">{prop_count}</div>
      </div>
      <div class="summary-tile">
        <div class="tile-label">Total Spend</div>
        <div class="tile-value">{fmt(total_spend, '$')}</div>
      </div>
      <div class="summary-tile">
        <div class="tile-label">Total Usage</div>
        <div class="tile-value">{fmt(total_usage)}</div>
      </div>
      <div class="summary-tile">
        <div class="tile-label">Bills</div>
        <div class="tile-value">{bill_count}</div>
      </div>
      <div class="summary-tile">
        <div class="tile-label">Avg CPOR</div>
        <div class="tile-value">{fmt(avg_cpor, '$', 2)}</div>
      </div>
      <div class="summary-tile">
        <div class="tile-label">Avg CPAR</div>
        <div class="tile-value">{fmt(avg_cpar, '$', 2)}</div>
      </div>
    </div>
    """
    st.markdown(tiles, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION  →  Property Detail page
# ═══════════════════════════════════════════════════════════════════════════════
def navigate_to_detail(prop_name):
    st.session_state["selected_property"] = prop_name
    st.switch_page("pages/3_Property_Detail.py")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    # ── Header / branding ────────────────────────────────────────────────────
    render_header()

    # ── Inject CSS ───────────────────────────────────────────────────────────
    st.markdown(PORTFOLIO_CSS, unsafe_allow_html=True)

    st.title("🏢 Property Portfolio")

    # ── Load live data ───────────────────────────────────────────────────────
    df, month_order = load_property_ledger()
    if df is None or df.empty:
        st.error("❌ No data returned from Google Sheets. Check sharing permissions.")
        st.stop()

    # Ensure Billing Date is datetime
    if "Billing Date" in df.columns:
        df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

    # Ensure Year / Month_Num exist
    if "Year" not in df.columns and "Billing Date" in df.columns:
        df["Year"] = df["Billing Date"].dt.year
    if "Month_Num" not in df.columns and "Billing Date" in df.columns:
        df["Month_Num"] = df["Billing Date"].dt.month

    # ── Filters  ─────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)

    # Utility filter
    utility_types = sorted(df["Utility"].dropna().unique()) if "Utility" in df.columns else []
    util_options = ["Select All"] + utility_types
    selected_util = col_f1.selectbox("Filter by Utility", util_options, index=0)

    if selected_util != "Select All" and "Utility" in df.columns:
        filtered_df = df[df["Utility"] == selected_util].copy()
    else:
        filtered_df = df.copy()

    # Property dropdown (populated from filtered data)
    properties = sorted(filtered_df["Property Name"].dropna().unique()) if "Property Name" in filtered_df.columns else []
    if not properties:
        st.warning("No properties found for the selected utility filter.")
        st.stop()

    selected_prop = col_f2.selectbox("Select Property", properties)

    # ── Summary bar (scoped to utility filter, all properties) ───────────────
    render_summary_bar(filtered_df)

    # ── Property card ────────────────────────────────────────────────────────
    prop_df = filtered_df[filtered_df["Property Name"] == selected_prop].copy()

    if prop_df.empty:
        st.info("No billing records for this property with the current filter.")
        st.stop()

    metrics = compute_property_metrics(prop_df)
    render_property_card(selected_prop, metrics)

    # ── Navigation button ────────────────────────────────────────────────────
    if st.button("🔍  View Full Details  →", key=f"nav_{selected_prop}"):
        navigate_to_detail(selected_prop)


# ── Entry point ──────────────────────────────────────────────────────────────
main()
