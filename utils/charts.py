import altair as alt
import pandas as pd

# -----------------------------
# COST TREND CHART
# -----------------------------
def cost_trend_chart(df):
    if df.empty:
        return alt.Chart(pd.DataFrame({"Billing Date": [], "$ Amount": [], "Year": []})).mark_line()

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Billing Date:T", title="Billing Date"),
            y=alt.Y("$ Amount:Q", title="Spend ($)"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Billing Date", "Year", "$ Amount"]
        )
        .properties(height=300)
    )

    return chart


# -----------------------------
# USAGE TREND CHART
# -----------------------------
def usage_trend_chart(df):
    if df.empty:
        return alt.Chart(pd.DataFrame({"Billing Date": [], "Usage": [], "Year": []})).mark_line()

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Billing Date:T", title="Billing Date"),
            y=alt.Y("Usage:Q", title="Usage"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Billing Date", "Year", "Usage"]
        )
        .properties(height=300)
    )

    return chart


# -----------------------------
# SPEND BY UTILITY CHART
# -----------------------------
def spend_by_utility_chart(df):
    if df.empty:
        return alt.Chart(pd.DataFrame({"Utility": [], "$ Amount": []})).mark_bar()

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Utility:N", title="Utility"),
            y=alt.Y("$ Amount:Q", title="Spend ($)"),
            color=alt.Color("Utility:N", legend=None),
            tooltip=["Utility", "$ Amount"]
        )
        .properties(height=300)
    )

    return chart

