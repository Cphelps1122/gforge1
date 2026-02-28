import streamlit as st
from utils.load_data import load_property_ledger
from utils.formatting import money

st.set_page_config(
    page_title="Utility Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Sidebar Upload
# -----------------------------
st.sidebar.title("Upload Data File")

# Persist uploaded file across pages
uploaded_file = st.sidebar.file_uploader(
    "Upload your Excel file",
    type=["xlsx"],
    key="uploaded_file_obj"
)

# If no file uploaded, stop the app
if uploaded_file is None:
    st.title("Utility Analytics Dashboard")
    st.write("Please upload your Excel file using the sidebar.")
    st.stop()

# -----------------------------
# Load Data
# -----------------------------
df, month_order = load_property_ledger(uploaded_file)

if df is None or df.empty:
    st.error("The uploaded file could not be processed. Please check the format.")
    st.stop()

# -----------------------------
# Main Title
# -----------------------------
st.title("Utility Analytics Dashboard")

# -----------------------------
# Portfolio KPIs
# -----------------------------
col1, col2, col3 = st.columns(3)

total_spend = df["$ Amount"].sum()
total_usage = df["Usage"].sum()
avg_cpor = df["CPOR"].mean() if "CPOR" in df.columns else None

col1.metric("Total Spend", money(total_spend))
col2.metric("Total Usage", f"{total_usage:,.0f}")
col3.metric("Average CPOR", money(avg_cpor))

st.write("---")

# -----------------------------
# Overview Section
# -----------------------------
st.subheader("Portfolio Overview")
st.write("Use the navigation pages on the left to explore property-level details, benchmarking, maps, and forecasting.")
