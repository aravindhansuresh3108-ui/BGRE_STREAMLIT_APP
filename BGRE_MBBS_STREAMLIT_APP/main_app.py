import streamlit as st
from pathlib import Path

def login():
    st.title("BGRE Dashboard Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if (
            username == "BGRE_CLIENT"
           and password == "BGRE@123"
        ):
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid username or password")


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

st.set_page_config(page_title="BGR Energy POC Dashboards", layout="wide")

BASE_DIR = Path(__file__).parent

page = st.sidebar.radio(
    "Select Dashboard",
    ["ME2J Procurement", "MBBS Inventory", "ZFI Vendor SOA"]
)

if page == "ME2J Procurement":
    exec(open(BASE_DIR / "me2j_app.py", encoding="utf-8").read())

elif page == "MBBS Inventory":
    exec(open(BASE_DIR / "mbbs_app.py", encoding="utf-8").read())

elif page == "ZFI Vendor SOA":
    exec(open(BASE_DIR / "zfi_app.py", encoding="utf-8").read())
