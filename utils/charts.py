import altair as alt
import pandas as pd

def cost_trend_chart(df, month_order):
    cost_trend = (
        df.groupby(["Year", "Month"], as_index=False)["$ Amount"].sum()
    )
    return (
        alt.Chart(cost_trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month", sort=month_order),
            y="$ Amount",
            color="Year:N",
            tooltip=["Year", "Month", "$ Amount"]
        )
    )

def usage_trend_chart(df, month_order):
    usage_trend = (
        df.groupby(["Year", "Month"], as_index=False)["Usage"].sum()
    )
    return (
        alt.Chart(usage_trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month", sort=month_order),
            y="Usage",
            color="Year:N",
            tooltip=["Year", "Month", "Usage"]
        )
    )

def spend_by_property_chart(df):
    prop_breakdown = (
        df.groupby("Property Name", as_index=False)["$ Amount"].sum()
        .sort_values("$ Amount", ascending=False)
    )
    return (
        alt.Chart(prop_breakdown)
        .mark_bar()
        .encode(
            x="Property Name:N",
            y="$ Amount:Q",
            tooltip=["Property Name", "$ Amount"]
        )
    )