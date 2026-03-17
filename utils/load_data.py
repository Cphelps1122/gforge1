import pandas as pd
import streamlit as st
import io
import requests

@st.cache_data(ttl=60)
def load_property_ledger():
    # OneDrive API direct-content link (always returns the actual file)
    url = "https://api.onedrive.com/v1.0/drive/items/fb1f6d6f-01f2-47d1-9832-b0d6ace2ce02/content"

    try:
        r = requests.get(url, timeout=10)

        # If OneDrive returns HTML instead of Excel
        if r.text.startswith("<"):
            st.error("❌ OneDrive returned HTML instead of the Excel file. The file may not be shared correctly.")
            return pd.DataFrame(), []

        # Read Excel from bytes
        df = pd.read_excel(io.BytesIO(r.content), sheet_name="Raw Data", engine="openpyxl")

        month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

        return df, month_order

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame(), []
