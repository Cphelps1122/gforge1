import pandas as pd
import streamlit as st
import io
import requests

@st.cache_data(ttl=60)
def load_property_ledger():
    # Correct OneDrive direct-download link
    url = "https://onedrive.live.com/download?resid=9A915530E44251F2!107"

    try:
        r = requests.get(url, timeout=10)

        # If OneDrive returns HTML instead of Excel
        if r.text.startswith("<"):
            st.error("❌ OneDrive returned HTML instead of an Excel file. The file is not shared publicly or the link is not a true download link.")
            return pd.DataFrame(), []

        # Read Excel from bytes
        df = pd.read_excel(io.BytesIO(r.content), sheet_name="Raw Data", engine="openpyxl")

        month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

        return df, month_order

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame(), []
