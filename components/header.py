import streamlit as st

def render_header(title):
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("assets/cgs_logo.png", width=55)
    with col2:
        st.markdown(
            f"<h1 style='margin-top: 10px;'>{title}</h1>",
            unsafe_allow_html=True
        )