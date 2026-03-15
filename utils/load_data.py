import pandas as pd
import streamlit as st

# ----------------------------------------------------
# LIVE-LOADING PROPERTY LEDGER FROM ONEDRIVE EXCEL
# ----------------------------------------------------

@st.cache_data(ttl=60)   # refresh every 60 seconds
def load_property_ledger():
    # OneDrive direct-download link
    url = "https://onedrive.live.com/download?resid=9A915530E44251F2!105&authkey=!QBvbR_78gHRR5gysNas4s4CAf0NsIviLr9XYc2wdLqMDhw"

    # Load Excel
    df = pd.read_excel(url, sheet_name="Raw Data")

    # Month order (if used in charts)
    month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

    return df, month_order
