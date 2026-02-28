def portfolio_metrics(df):
    return {
        "properties": df["Property Name"].nunique(),
        "utilities": df["Utility"].nunique(),
        "years": df["Year"].nunique(),
        "total_spend": df["$ Amount"].sum(),
        "total_usage": df["Usage"].sum(),
        "avg_cost_per_unit": df["Cost_per_Unit"].mean(),
        "bills_count": len(df),
        "avg_cpor": (df["$ Amount"] / df["Usage"].replace(0, pd.NA)).mean()
    }
