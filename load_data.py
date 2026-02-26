import pandas as pd
import streamlit as st
from utils.weather import add_weather_normalization

def load_property_ledger():
    """
    Loads the uploaded Excel file from session_state.
    If no file is uploaded, returns None.
    """

    if "uploaded_file" not in st.session_state or st.session_state["uploaded_file"] is None:
        return None, None

    uploaded_file = st.session_state["uploaded_file"]

    # Read the Property sheet
    df = pd.read_excel(uploaded_file, sheet_name="Property")

    # Dates
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")
    df["Year"] = df["Billing Date"].dt.year
    df["Month"] = df["Billing Date"].dt.month_name().str[:3]

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

    # Base metrics
    df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"]

    # Occupancy metrics
    df["Cost_per_Occupied_Room"] = df["$ Amount"] / df["Occupied Rooms"]
    df["Cost_per_Available_Room"] = df["$ Amount"] / df["# Units"]

    df["Usage_per_Occupied_Room"] = df["Usage"] / df["Occupied Rooms"]
    df["Usage_per_Available_Room"] = df["Usage"] / df["# Units"]

    # Weather normalization
    df = add_weather_normalization(df, station_id="GHCND:USW00093721")

    return df, month_order