import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG ---
st.set_page_config(page_title="Yeast Shop Manager", layout="wide")

# --- 2. CONNECTION (Explicitly linking to Secrets) ---
# Yeh line aap k [connections.gsheets] walay secrets dhoonde gi
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # Spreadsheet URL ab Secrets mein hay, is liye yahan likhnay ki zaroorat nahi
        return conn.read(worksheet=worksheet_name, ttl=0)
    except Exception as e:
        return pd.DataFrame()

def update_data(worksheet_name, df):
    try:
        # Direct worksheet update karein, Robot (Service Account) ab active hay
        conn.update(worksheet=worksheet_name, data=df)
        return True
    except Exception as e:
        # Agar ab bhi error aye to woh asli wajah bataye ga
        st.error(f"❌ Connection Error: {e}")
        return False

# --- 3. LOGIN & APP LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "admin123":
            st.session_state["logged_in"] = True
            st.rerun()
    st.stop()

# Dashboard Content
st.title("🏪 Super Admin Dashboard")
menu = st.sidebar.radio("Menu", ["🛠️ Create New Shop"])

if menu == "🛠️ Create New Shop":
    with st.form("new_shop"):
        u = st.text_input("Username")
        p = st.text_input("Password")
        s = st.text_input("Shop Name")
        if st.form_submit_button("Account Create Karein"):
            df = get_data("Users")
            new_row = pd.DataFrame([{"Username": u, "Password": p, "Shop Name": s}])
            if update_data("Users", pd.concat([df, new_row], ignore_index=True)):
                st.success("✅ Success! Sheet update ho gayi hay.")
