import streamlit as st
import pandas as pd

def load_property_ledger():
    uploaded_file = st.session_state.get("uploaded_file_obj", None)
    if uploaded_file is None:
        return None, None

    xls = pd.ExcelFile(uploaded_file)

    # Prefer Sheet1 if it exists
    if "Sheet1" in xls.sheet_names:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    else:
        # Fallback to Property
        df = pd.read_excel(uploaded_file, sheet_name="Property")

    # Clean column names
    df.columns = df.columns.str.strip().str.replace("\u00A0", " ", regex=False)
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True)

    # Now Billing Date will exist
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



