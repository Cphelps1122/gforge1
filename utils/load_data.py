import pandas as pd
import streamlit as st
import io
import requests

@st.cache_data(ttl=60)
def load_property_ledger():
    # Google Sheets direct-download link
    url = "https://docs.google.com/spreadsheets/d/1EjTtOs0VqfrubPPZF6tEV8f8p_LWeREn/export?format=xlsx"

    try:
        r = requests.get(url, timeout=10)

        # If Google returns HTML instead of Excel
        if r.text.startswith("<"):
            st.error("❌ Google Sheets returned HTML instead of Excel. Make sure the file is shared as 'Anyone with the link can view'.")
            return pd.DataFrame(), []

        df = pd.read_excel(io.BytesIO(r.content), sheet_name="Raw Data", engine="openpyxl")

        month_order = df["Month"].unique().tolist() if "Month" in df.columns else []

        return df, month_order

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame(), []
