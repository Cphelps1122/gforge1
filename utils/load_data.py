import streamlit as st
import pandas as pd

def load_property_ledger():
    uploaded_file = st.session_state.get("uploaded_file_obj", None)
    if uploaded_file is None:
        return None, None

    # --- Load the clean Raw Data sheet (exact sheet name!) ---
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Raw Data")
    except Exception as e:
        st.error(f"Could not read 'Raw Data' sheet: {e}")
        return None, None

    # --- Clean column names ---
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    # Compute Cost_per_Unit safely
    df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"].replace(0, pd.NA)

    # --- Required columns ---
    required = ["Property Name", "Billing Date", "Usage", "$ Amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        return None, None

    # --- Parse dates ---
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

    # --- WEATHER NORMALIZATION ---
# You can tune these base temperatures later
BASE_HEAT = 65
BASE_COOL = 65

# Example: if you later add NOAA data, replace these with actual HDD/CDD values
# For now, compute simple HDD/CDD from temperature columns if present
if "Avg Temp" in df.columns:
    df["HDD"] = (BASE_HEAT - df["Avg Temp"]).clip(lower=0)
    df["CDD"] = (df["Avg Temp"] - BASE_COOL).clip(lower=0)
else:
    df["HDD"] = pd.NA
    df["CDD"] = pd.NA

# Normalized usage
df["Usage_per_HDD"] = df["Usage"] / df["HDD"].replace(0, pd.NA)
df["Usage_per_CDD"] = df["Usage"] / df["CDD"].replace(0, pd.NA)

    # --- Add Year + Month ---
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.strftime("%b")

    # --- Month order ---
    month_order = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sept","Oct","Nov","Dec"
    ]

    return df, month_order


