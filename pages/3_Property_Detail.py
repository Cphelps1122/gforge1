import streamlit as st
from utils.load_data import load_property_ledger
from utils.formatting import money

st.title("Property Detail")

# Ensure file is uploaded
uploaded_file = st.session_state.get("uploaded_file_obj")
if uploaded_file is None:
    st.write("Please upload your Excel file using the sidebar.")
    st.stop()

df, month_order = load_property_ledger(uploaded_file)

if df is None or df.empty:
    st.error("Unable to load data. Please check the uploaded file.")
    st.stop()

# -----------------------------
# Property Selector
# -----------------------------
properties = sorted(df["Property Name"].unique())
selected_property = st.selectbox("Select a Property", properties)

df_prop = df[df["Property Name"] == selected_property]

# -----------------------------
# KPIs
# -----------------------------
col1, col2, col3 = st.columns(3)

total_spend = df_prop["$ Amount"].sum()
total_usage = df_prop["Usage"].sum()
avg_cpor = df_prop["CPOR"].mean() if "CPOR" in df_prop.columns else None

col1.metric("Total Spend", money(total_spend))
col2.metric("Total Usage", f"{total_usage:,.0f}")
col3.metric("Average CPOR", money(avg_cpor))

st.write("---")

# -----------------------------
# Property Table
# -----------------------------
st.subheader(f"{selected_property} — Detailed Records")

df_display = df_prop.copy()

money_cols = [
    "$ Amount", "Cost_per_Unit", "Cost_per_Occupied_Room",
    "Cost_per_Available_Room", "CPOR", "CPAR"
]

for col in money_cols:
    if col in df_display.columns:
        df_display[col] = df_display[col].apply(money)

st.dataframe(df_display, use_container_width=True)
