import streamlit as st
from utils.load_data import load_property_ledger
from utils.formatting import money

st.set_page_config(
    page_title="Utility Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data automatically from newest file in /data
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.title("Utility Analytics Dashboard")
    st.error("No Excel files found in /data. Please add a file and refresh.")
    st.stop()

# Main Title
st.title("Utility Analytics Dashboard")

# KPIs
col1, col2, col3 = st.columns(3)

total_spend = df["$ Amount"].sum()
total_usage = df["Usage"].sum()
avg_cpor = df["CPOR"].mean() if "CPOR" in df.columns else None

col1.metric("Total Spend", money(total_spend))
col2.metric("Total Usage", f"{total_usage:,.0f}")
col3.metric("Average CPOR", money(avg_cpor))

st.write("---")

st.subheader("Portfolio Overview")
st.write("Use the navigation pages on the left to explore property-level details, benchmarking, maps, and forecasting.")


