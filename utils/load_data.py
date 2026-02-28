import pandas as pd
from pathlib import Path

def load_property_ledger():
    data_folder = Path("data")

    excel_files = list(data_folder.glob("*.xlsx"))
    if not excel_files:
        return None, None

    newest_file = max(excel_files, key=lambda f: f.stat().st_mtime)

    # Load ONLY the Raw Data sheet
    df = pd.read_excel(newest_file, sheet_name="Raw Data")

    # Do NOT force Month to datetime – keep as-is (e.g., "Jan", "Feb")
    # If you ever move to full dates, we can add a safe parser here.

    month_order = list(df["Month"].unique()) if "Month" in df.columns else None

    return df, month_order
