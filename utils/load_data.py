import streamlit as st
import pandas as pd

def load_property_ledger():
    uploaded_file = st.session_state.get("uploaded_file_obj", None)
    if uploaded_file is None:
        return None, None

    # --- Load the clean Raw Data sheet ---
    df = pd.read_excel(uploaded_file, sheet_name="Raw Data")

    # --- Clean column names ---
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    # --- Required columns check ---
    required_cols = [
        "Property Name", "Utility", "Billing Date", "Usage", "$ Amount"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        return None, None

    # --- Parse dates ---
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

    # --- Add Year + Month ---
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.strftime("%b")

    # --- Month order for charts ---
    month_order = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sept","Oct","Nov","Dec"
    ]

    return df, month_order
