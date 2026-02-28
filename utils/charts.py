import altair as alt
import pandas as pd
from utils.formatting import money

def cost_trend_chart(df, property_name):
    df_prop = df[df["Property Name"] == property_name].copy()
    df_prop = df_prop.sort_values("Month")

    chart = (
        alt.Chart(df_prop)
        .mark_line(point=True)
        .encode(
            x="Month:T",
            y=alt.Y("$ Amount:Q", title="Cost ($)"),
            tooltip=["Month", "$ Amount"]
        )
        .properties(height=300)
    )

    return chart
