import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. SETUP ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. USERS & LOGIN ---
USERS = {
    "dawoodmurtaza00@gmail.com": "admin123",
    "client1@gmail.com": "client500"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

def login():
    st.title("🔐 Secure Login")
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if email in USERS and USERS[email] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("❌ Ghalat Email ya Password!")

if not st.session_state["logged_in"]:
    login()
    st.stop()

# --- 3. CONNECTION (JSON FIX METHOD) ---
def get_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 🔥 YAHAN HUM AAP KI JSON KO RAW TEXT KE TOR PAR DAL RAHAY HAIN
    # JSON library isay khud theek kar le gi.
    raw_json_data = """
    {
      "type": "service_account",
      "project_id": "life-os-d42f0",
      "private_key_id": "3c7d952e3096334b04b53356f5b52b1fd86e2f07",
      "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCytOdCkjYRCLzw\\ngo7/HzNcwtEBoZDVR3hAtpFSeNbgc8a8Stt0Fk3BN4Zv7HP9KLtVSNQtXnTz2hVm\\nC7j8iuHtn8qth7iNF2nwg5wPKi23srGmO1ghfyPFYbQEzCyyJPuCNCfUOFVTE1bT\\nwv0OpsrhdJcyT85w/R0Azy6T4h9WouhUS03jr9oA7LWi2IljgOCwC68lip2x0HXQ\\nHEWFcdDGNyEeYLooNcs4/q9yWdkF2ZQDQp5msER4/RZhbbgD+5Zwze1vVP2Lm7Jb\\nov/4YXuqFx1rDkkGG6k0Zq8XMiIuZAo+crCPoZAgH1Y7oRLmRvZq4eOJk7t2e2Yr\\nvYTKjPhZAgMBAAECggEACUVpWgLL20Zgxvl/Aa1UtNNGlJcVNHtoubK/B1BNlYds\\nIAiiKfuePQ/sYZIa0l9ymJIWr+PenWgLBChHiJKL9g/8K9SGtosoa9noFsFRbd5P\\naRhbEiHOcUcIV9df2j4g7jhWeKQTiSPPtVzAVCpDDD9IOMv7IdF/17Ln77QjfBMR\\nO139wC2DZwTY5g1afM3u7Ea6NfyQ0nE2sz/yzUvQeIFHFLLndzq8SEZoYk8aZrTO\\n1Xx/DHyoyH/9ZwqIO+vp3I04sF+gJy/RIi9hTn1oEsNXwCZAkkC3zy/f/VCLDsL/\\n1mF7BXMC1BcZe7NrU17inC41QYDV8pfUjHmoHnv0gQKBgQDs7A3Vh9A0zi6iW5jU\\n/Z4xOqqUzhj87WzHBDn9NYzc8kcy41ZV1Szx9jw06xB39WOFTZH4tK+1llgWJzia\\nLgjZzHaii0PaksLiyQahk21l983vqKVAGj586nvwRu8ENIeZQG/vKx7qlPbh4R4L\\n8ny0XMSpsTv/HYPHoV0sOyPUlQKBgQDBGMm79dSIi981/xkdC4A4oOz2cqRQupk0\\nyPlRjgp3av8FRbvFvrCkBuyX/WLs+aGcsTkKNtfNvnH1dT4013Fl3jxk+SAn4Vt/\\nTxvN/XIVrwRSPXDPqOfcLtW5mpzW82GqttV5MNsr75sVksONXj11oGyg3oKLTHwz\\nmZH+zIs/tQKBgDpSfbFT5pApNVeoXr4H1Npfi8Bn38TbmYyAYNoRRaTaS2aeihFF\\nEfRaXkXUm9A76wzUpJtpt1tnMDX737YsoOckqwumZsS2nhz/yY8a4LJaRyq5BDz8\\neOd9PZdPjuUlHUA/mY5xugGbPA8swJ3GSqaHs63mQFOz603ITkxmHpLlAoGBAKY8\\n1ehIglmvuVG+NXuo3BFkkby2A7owexdTcjkBBQe8CKMcXsSmH2KHR4auMU18t+Kz\\nPD0L7AwHygocjpplZA3kHrB7PXC39dKLY4+ag24hh6HZnVZZvorzkzI/5oizbUDQ\\nOMYmBnozxJr1B/+bw2OR4hM4nMCZ709pBaSLqdIFAoGAd1dUxIUO/Ad3p472sqPX\\nVAKre/0vFQYQWZWb3QXaowuzgwZ0yW3m3c4nbGz1APWg87EXUB0ikVHD7TM0Gyf6\\nDFg8eqw56BJWuaUJ5AiTkIyKDAM1mK6G3Zq1q7gapxU4RHwH7f0qbYdCOa8PwwPK\\nPqVIsUCDYbZaCG+eQnI6p0Q=\\n-----END PRIVATE KEY-----\\n",
      "client_email": "firebase-adminsdk-fbsvc@life-os-d42f0.iam.gserviceaccount.com",
      "client_id": "106111267269346632174",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40life-os-d42f0.iam.gserviceaccount.com"
    }
    """
    
    # Parse the string into a real dictionary
    creds_dict = json.loads(raw_json_data)

    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # Connect to the Sheet
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/14WmPIOtQSTjbx6zcOpGMHF2j27i_-hHkBI-9goLKV3c/edit")
    return sheet

# --- 4. DATA LOGIC ---
def get_data(tab_name):
    try:
        sh = get_connection()
        try:
            worksheet = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"⚠️ Error: Tab '{tab_name}' sheet mein nahi mila.")
            return pd.DataFrame()
        return pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        st.error(f"❌ Read Error: {e}")
        return pd.DataFrame()

def save_data(tab_name, row_data):
    try:
        sh = get_connection()
        worksheet = sh.worksheet(tab_name)
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ Save Error: {e}")
        return False

# --- 5. INTERFACE ---
st.sidebar.title(f"👤 {st.session_state['user_email']}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.title("🍞 Menu")
menu = st.sidebar.radio("Go to:", ["Inventory", "Customers", "Sales", "Bank", "Expenses"])
st.title(f"📂 {menu} Management")

# A. INVENTORY
if menu == "Inventory":
    df = get_data("Inventory")
    st.dataframe(df, use_container_width=True)
    with st.form("inv"):
        c1, c2, c3 = st.columns(3)
        with c1: i = st.text_input("Item Name")
        with c2: q = st.number_input("Qty", 0)
        with c3: p = st.number_input("Price", 0)
        if st.form_submit_button("Save Stock"):
            if save_data("Inventory", [i, q, p, str(datetime.now(pk_tz))]):
                st.success("✅ Saved!"); st.rerun()

# B. CUSTOMERS
elif menu == "Customers":
    df = get_data("Customers")
    st.dataframe(df, use_container_width=True)
    with st.form("cus"):
        n = st.text_input("Name")
        b = st.number_input("Opening Balance", 0)
        if st.form_submit_button("Add Customer"):
            if save_data("Customers", [n, b, "Active", str(datetime.now(pk_tz))]):
                st.success("✅ Saved!"); st.rerun()

# C. SALES
elif menu == "Sales":
    d = get_data("Customers")
    cl = d["Username"].tolist() if not d.empty and "Username" in d.columns else []
    with st.form("sal"):
        c = st.selectbox("Customer", cl) if cl else st.text_input("Customer Name")
        a = st.number_input("Amount", 0)
        p = st.number_input("Paid", 0)
        n = st.text_input("Items")
        if st.form_submit_button("Generate Bill"):
            if save_data("Sales", [c, a, p, n, str(datetime.now(pk_tz))]):
                st.success("✅ Saved!")

# D. BANK
elif menu == "Bank":
    df = get_data("Bank")
    st.dataframe(df, use_container_width=True)
    with st.form("bnk"):
        d = st.text_input("Detail")
        a = st.number_input("Amount", 0)
        t = st.selectbox("Type", ["Deposit", "Withdrawal"])
        if st.form_submit_button("Log"):
            if save_data("Bank", [d, a, t, str(datetime.now(pk_tz))]):
                st.success("✅ Saved!"); st.rerun()

# E. EXPENSES
elif menu == "Expenses":
    df = get_data("Expenses")
    st.dataframe(df, use_container_width=True)
    with st.form("exp"):
        t = st.text_input("Title")
        a = st.number_input("Amount", 0)
        c = st.text_input("Category")
        if st.form_submit_button("Add"):
            if save_data("Expenses", [t, a, c, str(datetime.now(pk_tz))]):
                st.success("✅ Saved!"); st.rerun()
