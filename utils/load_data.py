import streamlit as st
import pandas as pd

def load_property_ledger():
    # ⭐ ALWAYS pull from session_state, never from the uploader
    uploaded_file = st.session_state.get("uploaded_file_obj", None)

    if uploaded_file is None:
        return None, None

    # ⭐ Load Excel file
    df = pd.read_excel(uploaded_file)

    # ⭐ Ensure Billing Date is parsed
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

    # ⭐ Extract Year and Month
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.strftime("%b")  # Jan, Feb, Mar...

    # ⭐ Month order for charts
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
