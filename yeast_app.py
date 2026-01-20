import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. SETUP ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. LOGIN ---
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
                st.error("❌ Invalid Credentials")

if not st.session_state["logged_in"]:
    login(); st.stop()

# --- 3. CONNECTION WITH DIAGNOSTICS ---
def get_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # 🔥 YOUR NEW KEY
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
        "private_key": raw_key.replace("\\n", "\n"),
        "client_email": "firebase-adminsdk-fbsvc@life-os-d42f0.iam.gserviceaccount.com",
        "client_id": "106111267269346632174",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40life-os-d42f0.iam.gserviceaccount.com"
    }
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # 🕵️ DIAGNOSTIC BLOCK (Yeh check karay ga ke Robot ko kya nazar aa raha hai)
    try:
        # Hum seedha URL se open kar rahay hain (ID copy paste error se bachnay ke liye)
        sheet_url = "https://docs.google.com/spreadsheets/d/14WmPIOtQSTjbx6zcOpGMHF2j27i_-hHkBI-9goLKV3c/edit"
        sheet = client.open_by_url(sheet_url)
        return sheet
    except Exception as e:
        st.error(f"❌ Connection Failed! Error: {e}")
        st.warning("🔍 Robot is checking available sheets...")
        try:
            available_sheets = client.openall()
            if not available_sheets:
                st.error("⚠️ Robot ko KOI bhi sheet nazar nahi aa rahi! Please 'Copy of client yeast' ko 'Unshare' kar ke dobara 'Share' karein.")
            else:
                st.success("✅ Robot ko ye sheets nazar aa rahi hain (Check karein aap ki sheet in mein hai?):")
                for s in available_sheets:
                    st.write(f"- {s.title} (ID: {s.id})")
        except Exception as e2:
            st.error(f"⚠️ Robot list bhi check nahi kar saka: {e2}")
        st.stop()
        return None

# --- 4. DATA FUNCTIONS ---
def get_data(tab_name):
    sh = get_connection()
    try:
        worksheet = sh.worksheet(tab_name)
        return pd.DataFrame(worksheet.get_all_records())
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"⚠️ Tab '{tab_name}' nahi mila! Sheet mein tabs ke naam check karein.")
        return pd.DataFrame()

def save_data(tab_name, row_data):
    sh = get_connection()
    try:
        worksheet = sh.worksheet(tab_name)
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ Save Error: {e}")
        return False

# --- 5. INTERFACE ---
st.sidebar.title(f"👤 {st.session_state['user_email']}")
if st.sidebar.button("Logout"): st.session_state["logged_in"] = False; st.rerun()

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
