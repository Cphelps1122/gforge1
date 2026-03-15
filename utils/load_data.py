import pandas as pd
import streamlit as st

@st.cache_data(ttl=60)   # refresh every 60 seconds
def load_property_ledger():
    # OneDrive direct-download link
    url = "https://onedrive.live.com/download?resid=9A915530E44251F2!105&authkey=!QBvbR_78gHRR5gysNas4s4CAf0NsIviLr9XYc2wdLqMDhw"

    # Load Excel with explicit engine
    df = pd.read_excel(url, sheet_name="Raw Data", engine="openpyxl")

    # Month order (if used)
    month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

    return df, month_order
