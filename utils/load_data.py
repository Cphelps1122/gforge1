import pandas as pd
from pathlib import Path

def load_property_ledger():
    data_folder = Path("data")

    # Find all Excel files in /data
    excel_files = list(data_folder.glob("*.xlsx"))
    if not excel_files:
        return None, None

    # Pick the newest file
    newest_file = max(excel_files, key=lambda f: f.stat().st_mtime)

    # Load ONLY the Raw Data sheet
    df = pd.read_excel(newest_file, sheet_name="Raw Data")

    # -----------------------------
    # DERIVED COLUMNS (restore compatibility)
    # -----------------------------

    # Usage per Occupied Room
    if "Usage" in df.columns and "Occupied Rooms" in df.columns:
        df["Usage_per_Occupied_Room"] = df["Usage"] / df["Occupied Rooms"].replace(0, pd.NA)

    # Usage per Available Room
    if "Usage" in df.columns and "# Units" in df.columns:
        df["Usage_per_Available_Room"] = df["Usage"] / df["# Units"].replace(0, pd.NA)

    # Cost per Unit
    if "Usage" in df.columns and "$ Amount" in df.columns:
        df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"].replace(0, pd.NA)

    # CPOR (Cost per Occupied Room)
    if "Occupied Rooms" in df.columns and "$ Amount" in df.columns:
        df["CPOR"] = df["$ Amount"] / df["Occupied Rooms"].replace(0, pd.NA)

    # CPAR (Cost per Available Room)
    if "# Units" in df.columns and "$ Amount" in df.columns:
        df["CPAR"] = df["$ Amount"] / df["# Units"].replace(0, pd.NA)

    # Month order (no datetime conversion)
    if "Month" in df.columns:
        month_order = list(df["Month"].unique())
    else:
        month_order = None

    return df, month_order

