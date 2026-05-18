import streamlit as st

st.set_page_config(page_title="BGR Energy POC Dashboards", layout="wide")

page = st.sidebar.radio(
    "Select Dashboard",
    ["ME2J Procurement", "MBBS Inventory", "ZFI Vendor SOA"]
)

if page == "ME2J Procurement":
    exec(open("me2j_app.py", encoding="utf-8").read())

elif page == "MBBS Inventory":
    exec(open("mbbs_app.py", encoding="utf-8").read())

elif page == "ZFI Vendor SOA":
    exec(open("zfi_app.py", encoding="utf-8").read())