import pandas as pd
import glob
import os

def load_property_ledger():
    files = glob.glob("data/*.xlsx")
    if not files:
        return None, None

    df = pd.read_excel(files[0], sheet_name="Raw Data")
    df.columns = df.columns.str.strip()

    # Clean Month ordering
    month_order = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sept","Oct","Nov","Dec"
    ]

    return df, month_order
