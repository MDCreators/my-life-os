import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. SETUP ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. LOGIN SYSTEM ---
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

# --- 3. ROBUST CONNECTION ---
def get_connection():
    # Scopes define karna lazmi hay (Drive + Sheets)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 🔥 AAP KI LATEST KEY (Jo aap nay abhi generate ki thi)
    raw_key = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDnsArBr1SbGOLR
wZqkGBhfpKywZMe6HU9wGXGeLJhPmLTY/qN7OouK0Mdp60SWcbqhDh5UUA74RVhm
p9LoQr+3V9zNboLM2CZozlqZfbYCjbrVgoLmwB4CAddFUiknXRWmh571Gn2VxMvZ
Kqvqz9tD8aZsc4goFBXyZcGh3YggKSQ3bEiO9/qoLeJXN59qWSlG6+GsxVZm6XjA
AtXV3g2O8oJ6zg95Wo5yKVaIXP+Jr4+wFBch3UVdtvcLkRnq7v4YRQhhlPqpxixU
lZ4J1kzaH85BH4h95DUwb8As05hpOJyDzaIZxMUrnPUGa10ZPPaFXlEGtdmz9Mhm
UGH9NC5bAgMBAAECggEADipmTfdRXfZEj/ydXuEWRGrGIDbZO1jlbX4wwzII0f0N
OaNADZ3DwGYJe0FmPSiQ953sXs1STP24bPZf39GM9UHK/0h9eNbSamALjAzynu9Z
eAp1xHQEoazJI7TlTUHUvAzYvDW1bf3NVObWAhJZXqscuM7LiV/JA7wS/bmUxBqC
ExYSry2jP2VadCfQ+FmnVXNu78DBxMSFE9rGMn+duU1vMP3pC1l0qbb7DWwD88oa
vjfkdxy+3tz8CSJ0DD9T4VtUtTs8Zb142zSmLKBteaDopk/17sV3fwiWUKjRBEqX
leGSIsuUaN7hKcu77qeZE6oYs7+zOSWMG14/hEFUeQKBgQD1w+SgEgcbRfVNNHzX
jKs/zcnXfp3Hk9hQNiyTgGEo5wbZDVqoWItjg/GRu0qwlTXn1VCHcf6CSsFyuWIj
ihh8kr+ShNm/5l07Q1HUE4efBlODEcpGyeXUdod0++PQmFhjAM8eCKBLfE2fTz/b
ZgAv0rYlbcvPLRGYyN9Riv9DTQKBgQDxVhFqb8JmDs78J6G6gK6ijPQD+KLD0XOO
Wi+STfYC0P2VNi5WX3OdeJ9YrS/dX83DLZYX1Rp/ohPvIm1/T079rS6yM14KVmzM
/b8h+4H5iACJVX/KYIe4aaiTLWoVTi+EjNKv/6fAosTzaY1mljLDS4fBbM5AZPo7
wliqk4CURwKBgDEYZP+lGk5Ud2Bo79ePflZModmurY5E9p1vdRAyQTaOkEuj40xm
A9JpdUSLiawk4pPhhSjJmPImRObKKdS3rZSVLDf02hr/xfgkxp/7Fsip1t0EHMhv
ZL5Av2abOzNce6urabSyPHNX7Zm5lyQZCEiFa2WmvWQxuKYw2ovLnJqxAoGAdOzG
M1NCVEAIeJKbAMkn0wmHkAT+lvD7k5SOR8wNzP+EXK6LdL16PmkaitQdxJuODWog
thtBY2UbU1jSxEOgebdWUHAit893lzm5SLWaG1ORLviFmX97QhWu3t+57eibjRTN
Xwf2Npal5WjWYUWUApqtg0E8DGbf9eQLIVmlijECgYBowkk20Q59qshEABdFvZRj
Z3biq09cRR23B9Dkhq/o4en6SObiQKh9DEpiXpv9GfeRq7SpeMOR8egVi0j2f7PD
sbZPelnzq3j3RmtPua2lYbBvbpvR34/wN15uGIfN6TenOX2dNvz8UYRkNU3puXGS
NUYEnGUT+Iu/we6Mo4Qh4Q==
-----END PRIVATE KEY-----"""

    creds_dict = {
        "type": "service_account",
        "project_id": "life-os-d42f0",
        "private_key_id": "52a7bb9994f831138ebfc1ae8473470f50ac06a5",
        "private_key": raw_key.replace("\\n", "\n"), # Format Fix
        "client_email": "firebase-adminsdk-fbsvc@life-os-d42f0.iam.gserviceaccount.com",
        "client_id": "106111267269346632174",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40life-os-d42f0.iam.gserviceaccount.com"
    }
    
    # Authorize
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # 🔥 OPEN BY KEY (URL ki bajaye ID use kar rahay hain - Yeh safe hay)
    # Sheet ID: 14WmPIOtQSTjbx6zcOpGMHF2j27i_-hHkBI-9goLKV3c
    sheet = client.open_by_key("14WmPIOtQSTjbx6zcOpGMHF2j27i_-hHkBI-9goLKV3c")
    return sheet

# --- 4. DATA FUNCTIONS ---
def get_data(tab_name):
    try:
        sh = get_connection()
        try:
            worksheet = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"⚠️ Tab '{tab_name}' nahi mila. Sheet mein check karein ke ye naam mojood hay?")
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

# --- 5. USER INTERFACE ---
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
        st.subheader("Add Stock")
        c1, c2, c3 = st.columns(3)
        with c1: i = st.text_input("Item Name")
        with c2: q = st.number_input("Quantity", 0)
        with c3: p = st.number_input("Unit Price", 0)
        if st.form_submit_button("Save Stock"):
            if save_data("Inventory", [i, q, p, str(datetime.now(pk_tz))]):
                st.success("✅ Stock Updated!")
                st.rerun()

# B. CUSTOMERS
elif menu == "Customers":
    df = get_data("Customers")
    st.dataframe(df, use_container_width=True)
    with st.form("cus"):
        st.subheader("New Customer")
        n = st.text_input("Customer Name")
        b = st.number_input("Opening Balance", 0)
        if st.form_submit_button("Add Customer"):
            if save_data("Customers", [n, b, "Active", str(datetime.now(pk_tz))]):
                st.success("✅ Customer Added!")
                st.rerun()

# C. SALES
elif menu == "Sales":
    d = get_data("Customers")
    cl = d["Username"].tolist() if not d.empty and "Username" in d.columns else []
    
    st.subheader("New Invoice")
    with st.form("sal"):
        c = st.selectbox("Customer", cl) if cl else st.text_input("Customer Name")
        c1, c2 = st.columns(2)
        with c1: a = st.number_input("Total Amount", 0)
        with c2: p = st.number_input("Cash Received", 0)
        n = st.text_input("Items / Note")
        
        if st.form_submit_button("Generate Bill"):
            if save_data("Sales", [c, a, p, n, str(datetime.now(pk_tz))]):
                st.success("✅ Bill Saved!")
                st.rerun()

# D. BANK
elif menu == "Bank":
    df = get_data("Bank")
    st.dataframe(df, use_container_width=True)
    with st.form("bnk"):
        st.subheader("Bank Transaction")
        d = st.text_input("Detail")
        a = st.number_input("Amount", 0)
        t = st.selectbox("Type", ["Deposit", "Withdrawal"])
        if st.form_submit_button("Log Transaction"):
            if save_data("Bank", [d, a, t, str(datetime.now(pk_tz))]):
                st.success("✅ Saved!")
                st.rerun()

# E. EXPENSES
elif menu == "Expenses":
    df = get_data("Expenses")
    st.dataframe(df, use_container_width=True)
    with st.form("exp"):
        st.subheader("New Expense")
        t = st.text_input("Title")
        a = st.number_input("Amount", 0)
        c = st.text_input("Category")
        if st.form_submit_button("Add Expense"):
            if save_data("Expenses", [t, a, c, str(datetime.now(pk_tz))]):
                st.success("✅ Expense Recorded!")
                st.rerun()
