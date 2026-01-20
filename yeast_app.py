import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. SETUP ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. USERS & LOGIN SYSTEM ---
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

# --- 3. DIRECT CONNECTION (Auto-Fix Key) ---
def get_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # --- YOUR JSON KEY ---
    creds_dict = {
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

    # 🔥 CRITICAL FIX: Replace text \n with actual newlines
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # Authenticate
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # Connect to the Sheet
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/14WmPIOtQSTjbx6zcOpGMHF2j27i_-hHkBI-9goLKV3c/edit")
    return sheet

# --- 4. DATA FUNCTIONS ---
def get_data(tab_name):
    try:
        sh = get_connection()
        try:
            worksheet = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"⚠️ Error: Tab '{tab_name}' sheet mein nahi mila. Spelling check karein.")
            return pd.DataFrame()
            
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
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

# --- 5. APP INTERFACE ---
st.sidebar.title(f"👤 {st.session_state['user_email']}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.title("🍞 Menu")
menu = st.sidebar.radio("Go to:", ["Inventory", "Customers", "Sales", "Bank", "Expenses"])

st.title(f"📂 {menu} Management")

# --- A. INVENTORY (STOCK) ---
if menu == "Inventory":
    df = get_data("Inventory")
    st.dataframe(df, use_container_width=True)
    with st.form("inv_form"):
        st.subheader("Add New Item")
        c1, c2, c3 = st.columns(3)
        with c1: item = st.text_input("Item Name")
        with c2: qty = st.number_input("Quantity", 0)
        with c3: price = st.number_input("Unit Price", 0)
        
        if st.form_submit_button("Save Stock"):
            if save_data("Inventory", [item, qty, price, str(datetime.now(pk_tz))]):
                st.success("✅ Stock Updated!")
                st.rerun()

# --- B. CUSTOMERS ---
elif menu == "Customers":
    df = get_data("Customers")
    st.dataframe(df, use_container_width=True)
    with st.form("cust_form"):
        st.subheader("Add Customer")
        name = st.text_input("Customer Name")
        balance = st.number_input("Opening Balance", 0)
        if st.form_submit_button("Add Customer"):
            if save_data("Customers", [name, balance, "Active", str(datetime.now(pk_tz))]):
                st.success("✅ Customer Added!")
                st.rerun()

# --- C. SALES ---
elif menu == "Sales":
    cust_df = get_data("Customers")
    cust_list = cust_df["Username"].tolist() if not cust_df.empty and "Username" in cust_df.columns else []
    
    st.subheader("New Sale Invoice")
    with st.form("sale_form"):
        if cust_list:
            c_name = st.selectbox("Select Customer", cust_list)
        else:
            c_name = st.text_input("Customer Name")
        amount = st.number_input("Total Amount", 0)
        paid = st.number_input("Cash Received", 0)
        note = st.text_input("Note / Items")
        
        if st.form_submit_button("Generate Bill"):
            if save_data("Sales", [c_name, amount, paid, note, str(datetime.now(pk_tz))]):
                st.success("✅ Bill Saved!")

# --- D. BANK ---
elif menu == "Bank":
    df = get_data("Bank")
    st.dataframe(df, use_container_width=True)
    with st.form("bank_form"):
        detail = st.text_input("Transaction Detail")
        amount = st.number_input("Amount", 0)
        type_ = st.selectbox("Type", ["Deposit", "Withdrawal"])
        
        if st.form_submit_button("Log Transaction"):
            if save_data("Bank", [detail, amount, type_, str(datetime.now(pk_tz))]):
                st.success("✅ Transaction Logged!")
                st.rerun()

# --- E. EXPENSES ---
elif menu == "Expenses":
    df = get_data("Expenses")
    st.dataframe(df, use_container_width=True)
    with st.form("exp_form"):
        title = st.text_input("Expense Title")
        amt = st.number_input("Amount", 0)
        cat = st.text_input("Category (e.g. Food/Rent)")
        
        if st.form_submit_button("Add Expense"):
            if save_data("Expenses", [title, amt, cat, str(datetime.now(pk_tz))]):
                st.success("✅ Expense Recorded!")
                st.rerun()
