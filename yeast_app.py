import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="Life OS - Pro", layout="wide", page_icon="🏢")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. ROBUST CONNECTION ---
def get_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # 🔥 SAME KEY (Jo abhi chal rahi hay)
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
    return client.open("Copy of client yeast")

# --- 3. CORE FUNCTIONS ---
def get_users():
    try:
        sh = get_connection()
        ws = sh.worksheet("Users")
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

def get_data(tab_name):
    try:
        sh = get_connection()
        ws = sh.worksheet(tab_name)
        df = pd.DataFrame(ws.get_all_records())
        # 🔥 Filter: Sirf apna data dikhaye
        if not df.empty and "Owner" in df.columns:
            df = df[df["Owner"] == st.session_state["user_email"]]
        return df
    except Exception as e:
        st.error(f"Error reading {tab_name}: {e}")
        return pd.DataFrame()

def save_data(tab_name, row_data):
    try:
        sh = get_connection()
        ws = sh.worksheet(tab_name)
        # 🔥 Auto-add Owner Email at the start
        full_row = [st.session_state["user_email"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        st.error(f"Error saving: {e}")
        return False

# --- 4. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "user_role" not in st.session_state: st.session_state["user_role"] = "User"

def login_screen():
    st.markdown("## 🔐 Life OS Login")
    with st.form("login"):
        email = st.text_input("Email").strip()
        password = st.text_input("Password", type="password").strip()
        if st.form_submit_button("Login"):
            users_df = get_users()
            if not users_df.empty:
                # Check User
                user = users_df[(users_df["Email"] == email) & (users_df["Password"] == password)]
                if not user.empty:
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = email
                    st.session_state["user_role"] = user.iloc[0]["Role"]
                    st.success(f"Welcome {email}!")
                    st.rerun()
                else:
                    st.error("Invalid Email or Password")
            else:
                st.error("User Database connection failed! Please check 'Users' tab.")

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# --- 5. MAIN DASHBOARD ---
st.sidebar.title(f"👤 {st.session_state['user_email']}")
st.sidebar.caption(f"Role: {st.session_state['user_role']}")

if st.sidebar.button("Logout", type="primary"):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("Navigation")

# Dynamic Menu
options = ["Inventory", "Customers", "Sales", "Bank", "Expenses"]
if st.session_state["user_role"] == "Admin":
    options.append("Manage Users") # Sirf Admin ke liye

menu = st.sidebar.radio("Go to:", options)

st.title(f"📂 {menu}")

# --- A. ADMIN PANEL (MANAGE USERS) ---
if menu == "Manage Users":
    st.warning("⚠️ Admin Area: Add new users here")
    users = get_users()
    st.dataframe(users, use_container_width=True)
    
    with st.form("add_user"):
        st.subheader("Create New User")
        c1, c2, c3 = st.columns(3)
        with c1: new_email = st.text_input("New Email")
        with c2: new_pass = st.text_input("Password")
        with c3: new_role = st.selectbox("Role", ["User", "Admin"])
        
        if st.form_submit_button("Create User"):
            try:
                sh = get_connection()
                ws = sh.worksheet("Users")
                ws.append_row([new_email, new_pass, new_role])
                st.success(f"User {new_email} created!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

# --- B. INVENTORY ---
elif menu == "Inventory":
    df = get_data("Inventory")
    # Organized View (Table upar, Form neechay)
    with st.expander("➕ Add New Stock", expanded=False):
        with st.form("inv"):
            c1, c2, c3 = st.columns(3)
            with c1: i = st.text_input("Item Name")
            with c2: q = st.number_input("Qty", 0)
            with c3: p = st.number_input("Price", 0)
            if st.form_submit_button("Add Item"):
                if save_data("Inventory", [i, q, p, str(datetime.now(pk_tz))]):
                    st.success("Item Added!")
                    st.rerun()
    st.dataframe(df, use_container_width=True)

# --- C. CUSTOMERS ---
elif menu == "Customers":
    df = get_data("Customers")
    with st.expander("➕ Add New Customer", expanded=False):
        with st.form("cus"):
            n = st.text_input("Customer Name")
            b = st.number_input("Opening Balance", 0)
            if st.form_submit_button("Add Customer"):
                if save_data("Customers", [n, b, "Active", str(datetime.now(pk_tz))]):
                    st.success("Customer Added!")
                    st.rerun()
    st.dataframe(df, use_container_width=True)

# --- D. SALES ---
elif menu == "Sales":
    df = get_data("Sales")
    # Customer Dropdown
    cust_df = get_data("Customers")
    cust_list = cust_df["Customer Name"].tolist() if not cust_df.empty and "Customer Name" in cust_df.columns else []
    
    with st.expander("➕ New Invoice", expanded=True):
        with st.form("sal"):
            c = st.selectbox("Select Customer", cust_list) if cust_list else st.text_input("Customer Name")
            c1, c2 = st.columns(2)
            with c1: a = st.number_input("Total Amount", 0)
            with c2: p = st.number_input("Cash Received", 0)
            n = st.text_input("Items / Details")
            if st.form_submit_button("Generate Bill"):
                if save_data("Sales", [c, a, p, n, str(datetime.now(pk_tz))]):
                    st.success("Bill Saved!")
                    st.rerun()
    st.dataframe(df, use_container_width=True)

# --- E. BANK ---
elif menu == "Bank":
    df = get_data("Bank")
    with st.expander("➕ New Transaction", expanded=False):
        with st.form("bnk"):
            d = st.text_input("Detail")
            a = st.number_input("Amount", 0)
            t = st.selectbox("Type", ["Deposit", "Withdrawal"])
            if st.form_submit_button("Log"):
                if save_data("Bank", [d, a, t, str(datetime.now(pk_tz))]):
                    st.success("Saved!")
                    st.rerun()
    st.dataframe(df, use_container_width=True)

# --- F. EXPENSES ---
elif menu == "Expenses":
    df = get_data("Expenses")
    with st.expander("➕ New Expense", expanded=False):
        with st.form("exp"):
            t = st.text_input("Title")
            a = st.number_input("Amount", 0)
            c = st.text_input("Category")
            if st.form_submit_button("Add"):
                if save_data("Expenses", [t, a, c, str(datetime.now(pk_tz))]):
                    st.success("Saved!")
                    st.rerun()
