import streamlit as st

def render_header():
    st.markdown(
        """
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <img src="assets/cgs_logo2.png" style="max-width: 60%; height: auto;">
        </div>
        """,
        unsafe_allow_html=True
    )
