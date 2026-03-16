import pandas as pd
import streamlit as st
import io
import requests

@st.cache_data(ttl=60)
def load_property_ledger():
    # Correct OneDrive direct-download link
    url = "https://onedrive.live.com/download?resid=9A915530E44251F2!106&authkey=!QRvbR_78gHRR5gysNas4s4CARcjkH77vgnOAfspFSGiAc8"

    # Fetch file manually
    r = requests.get(url)

    # If OneDrive returns HTML instead of Excel, stop cleanly
    if r.text.startswith("<"):
        st.error("OneDrive link returned HTML instead of Excel. Check the file permissions.")
        return pd.DataFrame(), []

    # Read Excel from bytes
    df = pd.read_excel(io.BytesIO(r.content), sheet_name="Raw Data", engine="openpyxl")

    # Month order (if used)
    month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

    return df, month_order
