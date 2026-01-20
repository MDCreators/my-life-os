import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Yeast Shop Manager", layout="wide")

# --- 2. CONNECTION (Imports ke baad aana chahiye) ---
# Yeh line ab error nahi degi kyunke import upar mojood hai
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # Secrets se credentials uthaye ga
        return conn.read(worksheet=worksheet_name, ttl=0)
    except Exception as e:
        st.error(f"Read Error: {e}")
        return pd.DataFrame()

def update_data(worksheet_name, df):
    try:
        # Spreadsheet par write karne ke liye
        conn.update(worksheet=worksheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Write Error: {e}")
        return False

# --- 3. LOGIN & DASHBOARD ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Secure Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "admin123":
            st.session_state["logged_in"] = True
            st.rerun()
    st.stop()

# SUPER ADMIN PANEL
st.title("🏪 Super Admin Dashboard")
with st.form("new_shop"):
    st.subheader("Nayi Shop Create Karein")
    u = st.text_input("New Username")
    p = st.text_input("New Password")
    s = st.text_input("Shop Name")
    if st.form_submit_button("Account Create Karein"):
        df_users = get_data("Users")
        new_row = pd.DataFrame([{"Username": u, "Password": p, "Shop Name": s}])
        if update_data("Users", pd.concat([df_users, new_row], ignore_index=True)):
            st.success("✅ Success! Data Sheet mein chala gaya hai.")
