import altair as alt
import pandas as pd

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
