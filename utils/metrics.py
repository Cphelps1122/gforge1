import pandas as pd

def portfolio_metrics(df):
    metrics = {
        "years": df["Year"].nunique() if "Year" in df.columns else None,
        "total_spend": df["$ Amount"].sum() if "$ Amount" in df.columns else None,
        "total_usage": df["Usage"].sum() if "Usage" in df.columns else None,
        "bills_count": len(df),

        # Derived metrics (safe lookups)
        "avg_cost_per_unit": df["Cost_per_Unit"].mean() if "Cost_per_Unit" in df.columns else None,
        "avg_cpor": df["CPOR"].mean() if "CPOR" in df.columns else None,
        "avg_cpar": df["CPAR"].mean() if "CPAR" in df.columns else None,
    }

    return metrics
