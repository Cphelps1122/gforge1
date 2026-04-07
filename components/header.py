import streamlit as st

def render_header(title_text="CGS EnergyGuard"):
    st.markdown(
        f"""
        <div style="
            width: 100%;
            text-align: center;
            padding: 10px 0 25px 0;
        ">
            <h1 style="
                font-size: 34px;
                font-weight: 700;
                color: white;
                margin: 0;
                letter-spacing: 0.5px;
            ">{title_text}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
