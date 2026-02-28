import pandas as pd

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

def property_benchmarks(df):
    # Cost per occupied room
    df["CPOR"] = df["$ Amount"] / df["Occupied Rooms"].replace(0, pd.NA)

    # Utility intensity
    df["Usage_Intensity"] = df["Usage"] / df["# Units"].replace(0, pd.NA)

    # Weather-normalized intensity
    df["HDD_Intensity"] = df["Usage_per_HDD"]
    df["CDD_Intensity"] = df["Usage_per_CDD"]

    # Group by property
    summary = df.groupby("Property Name").agg({
        "$ Amount": "sum",
        "Usage": "sum",
        "CPOR": "mean",
        "Usage_Intensity": "mean",
        "HDD_Intensity": "mean",
        "CDD_Intensity": "mean"
    }).reset_index()

    # Portfolio averages for benchmarking
    portfolio = summary.mean(numeric_only=True)

    # Add benchmark deltas
    summary["CPOR_vs_Portfolio"] = summary["CPOR"] - portfolio["CPOR"]
    summary["Usage_Intensity_vs_Portfolio"] = summary["Usage_Intensity"] - portfolio["Usage_Intensity"]

    return summary  


