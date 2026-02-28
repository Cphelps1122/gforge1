import pandas as pd
import os
from pathlib import Path

def load_property_ledger():
    data_folder = Path("data")

    # Find all Excel files in /data
    excel_files = list(data_folder.glob("*.xlsx"))

    if not excel_files:
        return None, None

    # Pick the newest file
    newest_file = max(excel_files, key=lambda f: f.stat().st_mtime)

    df = pd.read_excel(newest_file)

    # Ensure Month column is datetime
    if "Month" in df.columns:
        df["Month"] = pd.to_datetime(df["Month"])

    # Month order for charts
    month_order = sorted(df["Month"].unique()) if "Month" in df.columns else None

    return df, month_order
