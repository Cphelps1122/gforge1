import streamlit as st
import pandas as pd

def load_property_ledger():
    uploaded_file = st.session_state.get("uploaded_file_obj", None)
    if uploaded_file is None:
        return None, None

    # --- Load Raw Data sheet ---
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Raw Data")
    except Exception as e:
        st.error(f"Could not read 'Raw Data' sheet: {e}")
        return None, None

    # --- Clean column names ---
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    # --- Required columns ---
    required = [
        "Property Name", "Utility", "Billing Date", "Usage", "$ Amount",
        "# Units", "Occupied Rooms"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Your Raw Data sheet is missing required columns: {missing}")
        return None, None

    # --- Numeric coercion ---
    numeric_cols = ["Usage", "$ Amount", "# Units", "Occupied Rooms"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Parse dates ---
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
    if df["Billing Date"].isna().all():
        st.error("Billing Date column could not be parsed. Check formatting.")
        return None, None

    # --- Add Year + Month ---
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.strftime("%b")

    # --- Derived columns used across the app ---
    df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"].replace(0, pd.NA)
    df["Cost_per_Occupied_Room"] = df["$ Amount"] / df["Occupied Rooms"].replace(0, pd.NA)
    df["CPOR"] = df["Cost_per_Occupied_Room"]
    df["Usage_Intensity"] = df["Usage"] / df["# Units"].replace(0, pd.NA)

    # --- WEATHER NORMALIZATION ---
    BASE_HEAT = 65
    BASE_COOL = 65

    if "Avg Temp" in df.columns:
        df["HDD"] = (BASE_HEAT - df["Avg Temp"]).clip(lower=0)
        df["CDD"] = (df["Avg Temp"] - BASE_COOL).clip(lower=0)
    else:
        df["HDD"] = pd.NA
        df["CDD"] = pd.NA

    df["Usage_per_HDD"] = df["Usage"] / df["HDD"].replace(0, pd.NA)
    df["Usage_per_CDD"] = df["Usage"] / df["CDD"].replace(0, pd.NA)

    # --- Month order ---
    month_order = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sept","Oct","Nov","Dec"
    ]

    return df, month_order
