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

    # Do NOT force Month into datetime — your restored version uses labels like "Jan"
    if "Month" in df.columns:
        month_order = list(df["Month"].unique())
    else:
        month_order = None

    return df, month_order)

    # -----------------------------
    # LOAD RAW DATA
    # -----------------------------
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Raw Data")
    except Exception as e:
        st.error(f"Could not read 'Raw Data' sheet: {e}")
        return None, None

    # -----------------------------
    # CLEAN COLUMN NAMES
    # -----------------------------
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    # -----------------------------
    # REQUIRED COLUMNS
    # -----------------------------
    required = [
        "Property Name", "Utility", "Billing Date", "Usage", "$ Amount",
        "# Units", "Occupied Rooms", "ZIP Code"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Your Raw Data sheet is missing required columns: {missing}")
        return None, None

    # -----------------------------
    # NUMERIC COERCION
    # -----------------------------
    numeric_cols = ["Usage", "$ Amount", "# Units", "Occupied Rooms"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # DATE PARSING
    # -----------------------------
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
    if df["Billing Date"].isna().all():
        st.error("Billing Date column could not be parsed. Check formatting.")
        return None, None

    # -----------------------------
    # YEAR + MONTH
    # -----------------------------
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.strftime("%b")

    # -----------------------------
    # DERIVED COLUMNS
    # -----------------------------
    df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"].replace(0, pd.NA)
    df["Cost_per_Occupied_Room"] = df["$ Amount"] / df["Occupied Rooms"].replace(0, pd.NA)
    df["Cost_per_Available_Room"] = df["$ Amount"] / df["# Units"].replace(0, pd.NA)

    df["CPOR"] = df["Cost_per_Occupied_Room"]
    df["CPAR"] = df["Cost_per_Available_Room"]

    df["Usage_per_Occupied_Room"] = df["Usage"] / df["Occupied Rooms"].replace(0, pd.NA)
    df["Usage_per_Available_Room"] = df["Usage"] / df["# Units"].replace(0, pd.NA)

    df["Usage_Intensity"] = df["Usage"] / df["# Units"].replace(0, pd.NA)

    # -----------------------------
    # NOAA WEATHER NORMALIZATION
    # -----------------------------
    df["Avg Temp"] = pd.NA
    df["HDD"] = pd.NA
    df["CDD"] = pd.NA

    BASE_HEAT = 65
    BASE_COOL = 65

    for prop, group in df.groupby("Property Name"):
        zip_code = str(group["ZIP Code"].iloc[0]).strip()

        for idx, row in group.iterrows():
            end = row["Billing Date"]
            start = end - pd.Timedelta(days=30)

            wx = get_noaa_daily(
                zip_code,
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d")
            )

            if wx is None:
                continue

            avg_temp = wx["AvgTemp"].mean()
            df.at[idx, "Avg Temp"] = avg_temp
            df.at[idx, "HDD"] = max(BASE_HEAT - avg_temp, 0)
            df.at[idx, "CDD"] = max(avg_temp - BASE_COOL, 0)

    df["Usage_per_HDD"] = df["Usage"] / df["HDD"].replace(0, pd.NA)
    df["Usage_per_CDD"] = df["Usage"] / df["CDD"].replace(0, pd.NA)

    # -----------------------------
    # MONTH ORDER
    # -----------------------------
    month_order = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sept","Oct","Nov","Dec"
    ]

    return df, month_order



