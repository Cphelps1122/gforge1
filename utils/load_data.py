import pandas as pd
import streamlit as st
import io
import requests

@st.cache_data(ttl=60)
def load_property_ledger():
    url = "https://onedrive.live.com/download?resid=9A915530E44251F2!106&authkey=!QRvbR_78gHRR5gysNas4s4CARcjkH77vgnOAfspFSGiAc8"

    try:
        r = requests.get(url, timeout=10)

        # If OneDrive returns HTML instead of Excel
        if r.text.startswith("<"):
            st.error("❌ OneDrive is not returning the Excel file. Check file permissions or share settings.")
            return pd.DataFrame(), []

        # Try reading Excel
        df = pd.read_excel(io.BytesIO(r.content), sheet_name="Raw Data", engine="openpyxl")

        month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

        return df, month_order

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame(), []
