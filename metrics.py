def portfolio_metrics(df):
    return {
        "total_spend": df["$ Amount"].sum(),
        "total_usage": df["Usage"].sum(),
        "avg_cost_per_unit": df["Cost_per_Unit"].mean(),
        "bills_count": len(df),
        "properties": df["Property Name"].nunique(),
        "utilities": df["Utility"].nunique(),
        "years": df["Year"].nunique(),
        "avg_cpor": df["Cost_per_Occupied_Room"].mean(),
        "avg_cpar": df["Cost_per_Available_Room"].mean(),
    }