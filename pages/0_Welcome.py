import streamlit as st

# -------------------------
# CLIENT PASSCODES
# -------------------------
CLIENT_KEYS = {
    "alpha123": "Company A",
    "bravo456": "Company B",
    "charlie789": "Company C"
}

# -------------------------
# WELCOME PAGE
# -------------------------
def welcome_page():
    st.markdown("<h1 style='text-align:center;'>Welcome</h1>", unsafe_allow_html=True)

    # Logo centered
    st.image("logo.png", width=200)

    st.write("")
    st.write("")

    # Passcode input
    passcode = st.text_input("Enter your access code", type="password")

    if st.button("Enter Dashboard"):
        if passcode in CLIENT_KEYS:
            st.session_state["authenticated"] = True
            st.session_state["company"] = CLIENT_KEYS[passcode]
            st.rerun()
        else:
            st.error("Invalid passcode")

# -------------------------
# MAIN DASHBOARD
# -------------------------
def dashboard():
    company = st.session_state.get("company", None)

    st.markdown(f"### {company} Dashboard")
    st.write("Your custom analytics will load here.")

# -------------------------
# ROUTING LOGIC
# -------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    welcome_page()
else:
    dashboard()
