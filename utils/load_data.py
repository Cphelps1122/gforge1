import pandas as pd
import glob
import os

def load_property_ledger():
    # Look specifically for database_.xlsx inside /data
    file_path = "data/Database_.xlsx"

    if not os.path.exists(file_path):
        return None, None

    # Load the Raw Data sheet
    df = pd.read_excel(file_path, sheet_name="Raw Data")
    df.columns = df.columns.str.strip()

    # Month ordering for charts
    month_order = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sept","Oct","Nov","Dec"
    ]

    return df, month_order
