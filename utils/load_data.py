import pandas as pd
import streamlit as st
from utils.weather import add_weather_normalization

def load_property_ledger():
    # ⭐ Use the persistent key, not the widget key
    uploaded_file = st.session_state.get("uploaded_file_obj", None)

    if uploaded_file is None:
        return None, None

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