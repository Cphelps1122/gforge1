import streamlit as st
import pandas as pd

def load_property_ledger():
    uploaded_file = st.session_state.get("uploaded_file_obj", None)
    if uploaded_file is None:
        return None, None

    # ⭐ NEW: inspect sheet names
    xls = pd.ExcelFile(uploaded_file)
    st.write("SHEETS:", xls.sheet_names)

    # STOP HERE FOR NOW — do NOT load a sheet yet
    return None, None

    df = pd.read_excel(uploaded_file)

    # ⭐ Clean column names (this is the real fix)
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("\u00A0", " ", regex=False)
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True)

    # Debug: print cleaned columns
    # st.write("COLUMNS:", df.columns.tolist())

    # Now Billing Date will exist
    if "Billing Date" not in df.columns:
        st.error(f"Billing Date column not found. Columns are: {df.columns.tolist()}")
        return None, None

    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.strftime("%b")

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    return df, month_order

    # -----------------------------
    # LOAD PROPERTY SHEET
    # -----------------------------
    df = pd.read_excel(uploaded_file, sheet_name="Property")

    # -----------------------------
    # DATE FIELDS
    # -----------------------------
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.month_name().str[:3]

    # Month ordering
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

    # -----------------------------
    # METRICS
    # -----------------------------
    df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"]
    df["Cost_per_Occupied_Room"] = df["$ Amount"] / df["Occupied Rooms"]
    df["Cost_per_Available_Room"] = df["$ Amount"] / df["# Units"]
    df["Usage_per_Occupied_Room"] = df["Usage"] / df["Occupied Rooms"]
    df["Usage_per_Available_Room"] = df["Usage"] / df["# Units"]

    # -----------------------------
    # WEATHER NORMALIZATION
    # -----------------------------
    df = add_weather_normalization(df, station_id="GHCND:USW00093721")


    return df, month_order


