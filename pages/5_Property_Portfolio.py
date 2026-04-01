import streamlit as st
import matplotlib
matplotlib.use("Agg")  # headless backend — no GUI needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import base64, io, textwrap
from dataclasses import dataclass, field
from typing import List, Optional

# ──────────────────────────────────────────────────
# CONFIG — edit these to match your project
# ──────────────────────────────────────────────────
TARGET_DETAIL_PAGE = "pages/2_Property_Detail.py"  # path to your detail page
CARD_COLUMNS       = 3                              # cards per row
SPARKLINE_MONTHS   = 12                             # data points in sparkline

# ──────────────────────────────────────────────────
# DATA MODEL
# ──────────────────────────────────────────────────
@dataclass
class Property:
    id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str          # e.g. "SFR", "Multi-Family", "Commercial"
    current_value: float
    purchase_price: float
    monthly_rent: float
    occupancy_pct: float        # 0-100
    monthly_expenses: float
    value_history: List[float] = field(default_factory=list)   # last N months
    rent_history:  List[float] = field(default_factory=list)

# ──────────────────────────────────────────────────
# MOCK DATA (replace with your DB / Google Sheet fetch)
# ──────────────────────────────────────────────────
def _random_history(base: float, n: int = SPARKLINE_MONTHS,
                    drift: float = 0.008, vol: float = 0.02) -> List[float]:
    """Generate a realistic random walk for demo sparklines."""
    np.random.seed(abs(hash(str(base))) % 2**31)
    vals = [base]
    for _ in range(n - 1):
        vals.append(vals[-1] * (1 + drift + np.random.normal(0, vol)))
    return [round(v, 2) for v in vals]

MOCK_PROPERTIES: List[Property] = [
    Property("prop-001", "Oakwood Estates",   "1420 Oakwood Dr",     "Melissa",   "TX", "75454", "SFR",          425000, 380000, 2850, 100, 620,  _random_history(380000), _random_history(2600)),
    Property("prop-002", "Cedarview Duplex",  "308 Cedar Ln",        "Anna",      "TX", "75409", "Multi-Family", 610000, 540000, 4200,  95, 980,  _random_history(540000), _random_history(3800)),
    Property("prop-003", "Highpoint Commons", "7700 US-75 Ste B",    "McKinney",  "TX", "75071", "Commercial",  1250000,1100000, 9500,  88, 2100, _random_history(1100000),_random_history(8800)),
    Property("prop-004", "Willow Creek Home", "215 Willow Creek Ct", "Melissa",   "TX", "75454", "SFR",          395000, 365000, 2400, 100, 540,  _random_history(365000), _random_history(2200)),
    Property("prop-005", "Prosper Plaza",     "1010 E First St",     "Prosper",   "TX", "75078", "Commercial",   890000, 820000, 7100,  92, 1650, _random_history(820000), _random_history(6500)),
    Property("prop-006", "Bluebonnet Villas", "540 Bluebonnet Way",  "Celina",    "TX", "75009", "Multi-Family", 780000, 710000, 5600,  97, 1320, _random_history(710000), _random_history(5100)),
]

# ──────────────────────────────────────────────────
# SPARKLINE GENERATOR (matplotlib → base64 PNG)
# ──────────────────────────────────────────────────
def generate_sparkline(
    data: List[float],
    width: float = 3.2,
    height: float = 0.7,
    line_color: str = "#4F8CF7",
    fill_color: tuple = (79/255, 140/255, 247/255, 0.12),   # ← FIXED: was CSS rgba()
    neg_color: str = "#EF4444",
    show_endpoint: bool = True,
) -> str:
    """
    Return a base64-encoded PNG sparkline string ready for <img src="...">.
    Automatically colors red when the trend is negative.
    """
    if not data or len(data) < 2:
        return ""
    trend_positive = data[-1] >= data[0]
    lc = line_color if trend_positive else neg_color
    fc = fill_color if trend_positive else (239/255, 68/255, 68/255, 0.10)  # ← FIXED: was CSS rgba()

    fig, ax = plt.subplots(figsize=(width, height), dpi=120)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    x = list(range(len(data)))
    ax.plot(x, data, color=lc, linewidth=1.8, solid_capstyle="round")
    ax.fill_between(x, data, min(data), color=fc)
    if show_endpoint:
        ax.plot(x[-1], data[-1], "o", color=lc, markersize=4, zorder=5)
    ax.set_xlim(x[0], x[-1])
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{b64}"

# ──────────────────────────────────────────────────
# AGGREGATE METRICS
# ──────────────────────────────────────────────────
def compute_portfolio_metrics(properties: List[Property]) -> dict:
    total_value      = sum(p.current_value for p in properties)
    total_purchase   = sum(p.purchase_price for p in properties)
    total_monthly_inc = sum(p.monthly_rent for p in properties)
    total_monthly_exp = sum(p.monthly_expenses for p in properties)
    avg_occupancy    = np.mean([p.occupancy_pct for p in properties]) if properties else 0
    total_appreciation = ((total_value - total_purchase) / total_purchase * 100) if total_purchase else 0
    net_monthly      = total_monthly_inc - total_monthly_exp
    return dict(
        count=len(properties),
        total_value=total_value,
        total_monthly_income=total_monthly_inc,
        total_monthly_expenses=total_monthly_exp,
        net_monthly_income=net_monthly,
        avg_occupancy=avg_occupancy,
        total_appreciation_pct=total_appreciation,
    )

# ──────────────────────────────────────────────────
# CSS — enterprise-grade card styling
# ──────────────────────────────────────────────────
DASHBOARD_CSS = """
<style>
/* ── Summary bar ────────────────────────── */
.summary-bar {
    display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap;
}
.summary-tile {
    flex: 1 1 180px;
    background: linear-gradient(135deg, #1a1f36 0%, #252b48 100%);
    border-radius: 14px; padding: 20px 22px; color: #fff;
    min-width: 170px; box-shadow: 0 4px 20px rgba(0,0,0,0.18);
    position: relative; overflow: hidden;
}
.summary-tile::after {
    content: ""; position: absolute; top: -30px; right: -30px;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.summary-label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px;
    color: #8b92b0; margin-bottom: 6px; font-weight: 600;
}
.summary-value {
    font-size: 26px; font-weight: 700; line-height: 1.15; letter-spacing: -0.5px;
}
.summary-sub { font-size: 12px; color: #6ee7b7; margin-top: 4px; font-weight: 500; }
.summary-sub.neg { color: #f87171; }

/* ── Property card ──────────────────────── */
.prop-card {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
    padding: 0; overflow: hidden;
    transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.25s ease;
    cursor: pointer; height: 100%; display: flex; flex-direction: column;
}
.prop-card:hover {
    box-shadow: 0 8px 32px rgba(79,140,247,0.16);
    transform: translateY(-3px); border-color: #4F8CF7;
}
.card-header { padding: 18px 20px 10px 20px; }
.card-header .prop-name {
    font-size: 17px; font-weight: 700; color: #1a1f36;
    margin: 0 0 2px 0; line-height: 1.3;
}
.card-header .prop-address { font-size: 12.5px; color: #6b7280; margin: 0; }
.card-badge {
    display: inline-block; font-size: 10.5px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.8px;
    padding: 3px 10px; border-radius: 6px; margin-top: 8px;
}
.badge-sfr          { background: #dbeafe; color: #1d4ed8; }
.badge-multi-family { background: #ede9fe; color: #6d28d9; }
.badge-commercial   { background: #fef3c7; color: #b45309; }

.card-sparkline { padding: 6px 20px 2px 20px; }
.card-sparkline img { width: 100%; height: auto; display: block; }
.sparkline-label {
    font-size: 10.5px; color: #9ca3af; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 600; margin-bottom: 2px;
}

.card-metrics {
    padding: 10px 20px 18px 20px;
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px 16px; flex-grow: 1;
}
.metric-item { display: flex; flex-direction: column; }
.metric-label {
    font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.6px;
    color: #9ca3af; font-weight: 600; margin-bottom: 1px;
}
.metric-value { font-size: 16px; font-weight: 700; color: #1a1f36; }
.metric-value.green { color: #059669; }
.metric-value.red   { color: #ef4444; }

.card-footer {
    border-top: 1px solid #f3f4f6; padding: 12px 20px;
    display: flex; justify-content: space-between; align-items: center;
}
.card-footer .view-link {
    font-size: 12.5px; font-weight: 600; color: #4F8CF7;
    text-decoration: none; letter-spacing: 0.3px;
}
.card-footer .occupancy-pill {
    font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
}
.occ-high { background: #d1fae5; color: #065f46; }
.occ-mid  { background: #fef3c7; color: #92400e; }
.occ-low  { background: #fee2e2; color: #991b1b; }

/* ── Section headers ──────────────────── */
.section-title {
    font-size: 13px; text-transform: uppercase; letter-spacing: 1.4px;
    color: #6b7280; font-weight: 700; margin: 32px 0 14px 0;
    padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;
}

/* ── Dark-mode auto-adapt ───────────── */
@media (prefers-color-scheme: dark) {
    .prop-card { background: #1e2130; border-color: #2d3250; }
    .prop-card:hover { border-color: #4F8CF7; box-shadow: 0 8px 32px rgba(79,140,247,0.22); }
    .card-header .prop-name { color: #e5e7eb; }
    .card-header .prop-address { color: #9ca3af; }
    .metric-value { color: #e5e7eb; }
    .metric-label, .sparkline-label { color: #6b7280; }
    .card-footer { border-color: #2d3250; }
    .section-title { color: #9ca3af; border-color: #2d3250; }
}
</style>
"""

# ──────────────────────────────────────────────────
# HELPER FORMATTERS
# ──────────────────────────────────────────────────
def fmt_currency(val: float, compact: bool = False) -> str:
    if compact and abs(val) >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    if compact and abs(val) >= 1_000:
        return f"${val/1_000:,.0f}K"
    return f"${val:,.0f}"

def fmt_pct(val: float) -> str:
    return f"{val:.1f}%"

def badge_class(ptype: str) -> str:
    key = ptype.lower().replace(" ", "-").replace("_", "-")
    return f"badge-{key}" if key in ("sfr", "multi-family", "commercial") else "badge-sfr"

def occ_class(occ: float) -> str:
    if occ >= 95: return "occ-high"
    if occ >= 80: return "occ-mid"
    return "occ-low"

# ──────────────────────────────────────────────────
# RENDER FUNCTIONS
# ──────────────────────────────────────────────────
def render_summary_bar(m: dict) -> None:
    """Top-of-page aggregate KPI tiles."""
    appr_cls = "" if m["total_appreciation_pct"] >= 0 else "neg"
    net_cls  = "" if m["net_monthly_income"] >= 0 else "neg"
    html = f"""
    <div class="summary-bar">
        <div class="summary-tile">
            <div class="summary-label">Total Portfolio Value</div>
            <div class="summary-value">{fmt_currency(m["total_value"], compact=True)}</div>
            <div class="summary-sub {appr_cls}">{"▲" if m["total_appreciation_pct"]>=0 else "▼"} {fmt_pct(abs(m["total_appreciation_pct"]))} since purchase</div>
        </div>
        <div class="summary-tile">
            <div class="summary-label">Monthly Gross Income</div>
            <div class="summary-value">{fmt_currency(m["total_monthly_income"], compact=True)}</div>
            <div class="summary-sub">{m["count"]} properties</div>
        </div>
        <div class="summary-tile">
            <div class="summary-label">Net Monthly Cash Flow</div>
            <div class="summary-value">{fmt_currency(m["net_monthly_income"])}</div>
            <div class="summary-sub {net_cls}">After ${m["total_monthly_expenses"]:,.0f} expenses</div>
        </div>
        <div class="summary-tile">
            <div class="summary-label">Avg Occupancy</div>
            <div class="summary-value">{fmt_pct(m["avg_occupancy"])}</div>
            <div class="summary-sub">Across all units</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_property_card(prop: Property) -> None:
    """Single property card with sparkline and metrics."""
    sparkline_src = generate_sparkline(prop.value_history)
    appreciation = ((prop.current_value - prop.purchase_price) / prop.purchase_price * 100) if prop.purchase_price else 0
    appr_cls = "green" if appreciation >= 0 else "red"
    noi = prop.monthly_rent - prop.monthly_expenses
    noi_cls = "green" if noi >= 0 else "red"

    html = f"""
    <div class="prop-card">
        <div class="card-header">
            <p class="prop-name">{prop.name}</p>
            <p class="prop-address">{prop.address}, {prop.city}, {prop.state} {prop.zip_code}</p>
            <span class="card-badge {badge_class(prop.property_type)}">{prop.property_type}</span>
        </div>
        <div class="card-sparkline">
            <div class="sparkline-label">12-mo value trend</div>
            <img src="{sparkline_src}" alt="sparkline" />
        </div>
        <div class="card-metrics">
            <div class="metric-item">
                <span class="metric-label">Current Value</span>
                <span class="metric-value">{fmt_currency(prop.current_value, compact=True)}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Appreciation</span>
                <span class="metric-value {appr_cls}">{"+" if appreciation>=0 else ""}{fmt_pct(appreciation)}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Monthly Rent</span>
                <span class="metric-value">{fmt_currency(prop.monthly_rent)}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Net Income</span>
                <span class="metric-value {noi_cls}">{fmt_currency(noi)}</span>
            </div>
        </div>
        <div class="card-footer">
            <span class="view-link">View Details →</span>
            <span class="occupancy-pill {occ_class(prop.occupancy_pct)}">{fmt_pct(prop.occupancy_pct)} Occ</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# NAVIGATION HANDLER
# ──────────────────────────────────────────────────
def navigate_to_detail(prop_id: str) -> None:
    """Store selected property and jump to the detail page."""
    st.session_state["selected_property_id"] = prop_id
    try:
        st.switch_page(TARGET_DETAIL_PAGE)
    except Exception:
        # Fallback: set a query-param flag so the detail page can read it
        st.session_state["nav_target"] = "property_detail"
        st.rerun()

# ──────────────────────────────────────────────────
# PAGE ENTRY POINT
# ──────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="Portfolio Dashboard",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Inject CSS once
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    # ── Page header ──
    st.markdown(
        "<h1 style='margin-bottom:4px;font-size:28px;font-weight:800;letter-spacing:-0.5px;'>"
        "Portfolio Dashboard</h1>"
        "<p style='color:#6b7280;font-size:14px;margin-top:0;'>Real-time overview of your property portfolio</p>",
        unsafe_allow_html=True,
    )

    # ── Load data (swap this for your real data loader) ──
    properties = MOCK_PROPERTIES

    # ── Summary bar ──
    metrics = compute_portfolio_metrics(properties)
    render_summary_bar(metrics)

    # ── Section header ──
    st.markdown('<div class="section-title">Properties</div>', unsafe_allow_html=True)

    # ── Card grid ──
    rows = [properties[i:i + CARD_COLUMNS] for i in range(0, len(properties), CARD_COLUMNS)]
    for row in rows:
        cols = st.columns(CARD_COLUMNS, gap="medium")
        for idx, prop in enumerate(row):
            with cols[idx]:
                render_property_card(prop)
                # Navigation button — sits right below the card
                if st.button(
                    f"Open {prop.name}",
                    key=f"nav_{prop.id}",
                    use_container_width=True,
                    type="primary",
                ):
                    navigate_to_detail(prop.id)

    # ── Footer spacer ──
    st.markdown("<br><br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
