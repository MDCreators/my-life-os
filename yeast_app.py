import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. SETUP ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. USERS ---
USERS = {
    "dawoodmurtaza00@gmail.com": "admin123",
    "client1@gmail.com": "client500"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    
def login():
    st.title("🔐 Secure Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if email in USERS and USERS[email] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.rerun()
            else:
                st.error("❌ Ghalat Email ya Password")

if not st.session_state["logged_in"]:
    login(); st.stop()

# --- 3. CONNECTION (USING SECRETS) ---
def get_connection():
    # Scopes
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Secrets se credentials uthana (Yeh sab se safe tareeqa hai)
    # Streamlit khud hi \n ko handle kar lega
    creds_dict = st.secrets["service_account"]
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # Sheet URL bhi Secrets se ayega (Jo hum ne abhi sahi wala dala hai)
    sheet_url = st.secrets["service_account"]["spreadsheet_url"]
    return client.open_by_url(sheet_url)

# --- 4. DATA LOGIC ---
def get_data(tab):
    try:
        sh = get_connection()
        return pd.DataFrame(sh.worksheet(tab).get_all_records())
    except Exception as e:
        st.error(f"Read Error: {e}")
        return pd.DataFrame()

def save_data(tab, data):
    try:
        sh = get_connection()
        sh.worksheet(tab).append_row(data)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# --- 5. INTERFACE ---
st.sidebar.title("🍞 Menu")
if st.sidebar.button("Logout"): st.session_state["logged_in"] = False; st.rerun()

menu = st.sidebar.radio("Go to:", ["Inventory", "Customers", "Sales", "Bank", "Expenses"])
st.title(f"{menu} Section")

# SIMPLE FORM
df = get_data(menu)
st.dataframe(df, use_container_width=True)

with st.form("entry"):
    c1, c2, c3 = st.columns(3)
    with c1: v1 = st.text_input("Val 1")
    with c2: v2 = st.text_input("Val 2")
    with c3: v3 = st.text_input("Val 3")
    if st.form_submit_button("Save"):
        if save_data(menu, [v1, v2, v3, str(datetime.now(pk_tz))]):
            st.success("Saved!"); st.rerun()
