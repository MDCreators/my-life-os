import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Life OS", layout="wide", page_icon="💼")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. CONNECTION (BY SHEET NAME) ---
def get_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # YOUR KEY (Already Fixed)
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

# --- 3. DATABASE FUNCTIONS ---
def get_users():
    try:
        sh = get_connection()
        # Sheet Header: Username | Password | Shop Name
        ws = sh.worksheet("Users")
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

def get_data(tab_name):
    try:
        sh = get_connection()
        ws = sh.worksheet(tab_name)
        df = pd.DataFrame(ws.get_all_records())
        
        # 🔥 SECURITY: Show only logged-in user's data
        current_user = st.session_state["user_username"]
        
        # Admin gets to see everything, others only see their own
        if st.session_state.get("is_admin", False):
            pass # Admin sees all
        elif not df.empty and "Owner" in df.columns:
            df = df[df["Owner"] == current_user]
            
        return df
    except Exception as e:
        # Error chupane ke liye taake UI kharab na ho
        return pd.DataFrame()

def save_data(tab_name, row_data):
    try:
        sh = get_connection()
        ws = sh.worksheet(tab_name)
        # Owner column sab se pehlay
        full_row = [st.session_state["user_username"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        st.error(f"Save Failed: {e}")
        return False

# --- 4. LOGIN SYSTEM ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "user_username" not in st.session_state: st.session_state["user_username"] = ""
if "is_admin" not in st.session_state: st.session_state["is_admin"] = False

def login_screen():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("### 🔐 Login to Life OS")
        with st.form("login"):
            username = st.text_input("Username (Email)").strip()
            password = st.text_input("Password", type="password").strip()
            
            if st.form_submit_button("Login", use_container_width=True):
                # 1. Master Admin Check (Agar sheet khali bhi ho to ye chalay ga)
                if username == "dawoodmurtaza00@gmail.com" and password == "admin123":
                    st.session_state["logged_in"] = True
                    st.session_state["user_username"] = username
                    st.session_state["is_admin"] = True
                    st.success("Welcome Boss!")
                    st.rerun()
                
                # 2. Check in Sheet
                users_df = get_users()
                if not users_df.empty:
                    # Column names match kar lein jo aap ki sheet mein hain
                    # Sheet: Username, Password
                    user_match = users_df[
                        (users_df["Username"].astype(str) == username) & 
                        (users_df["Password"].astype(str) == password)
                    ]
                    
                    if not user_match.empty:
                        st.session_state["logged_in"] = True
                        st.session_state["user_username"] = username
                        # Dawood is Admin, baqi sab Users
                        st.session_state["is_admin"] = (username == "dawoodmurtaza00@gmail.com")
                        st.success(f"Welcome {username}")
                        st.rerun()
                    else:
                        st.error("❌ Wrong Username or Password")
                else:
                    st.error("⚠️ User database empty or not found.")

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# --- 5. MAIN APP ---
# Sidebar
st.sidebar.markdown(f"### 👤 {st.session_state['user_username']}")
if st.session_state["is_admin"]:
    st.sidebar.badge("ADMIN ACCESS")

if st.sidebar.button("Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.divider()
menu_options = ["Inventory", "Customers", "Sales", "Bank", "Expenses"]
if st.session_state["is_admin"]:
    menu_options.insert(0, "Manage Users") # Admin only feature

menu = st.sidebar.radio("Navigate", menu_options)
st.title(f"{menu}")

# --- A. ADMIN: MANAGE USERS ---
if menu == "Manage Users":
    st.info("👋 Yahan se aap naye users bana saktay hain.")
    
    # Add User Form
    with st.expander("➕ Create New User", expanded=True):
        with st.form("new_user"):
            c1, c2 = st.columns(2)
            with c1: new_user = st.text_input("New Username")
            with c2: new_pass = st.text_input("New Password")
            shop_name = st.text_input("Shop Name")
            
            if st.form_submit_button("Create User"):
                try:
                    sh = get_connection()
                    ws = sh.worksheet("Users")
                    # Adding to sheet: Username | Password | Shop Name
                    ws.append_row([new_user, new_pass, shop_name])
                    st.success(f"User '{new_user}' created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.subheader("Existing Users")
    st.dataframe(get_users(), use_container_width=True)

# --- B. INVENTORY ---
elif menu == "Inventory":
    # Form Hidden in Expander
    with st.expander("📦 Add New Item", expanded=False):
        with st.form("inv"):
            c1, c2, c3 = st.columns(3)
            with c1: i = st.text_input("Item Name")
            with c2: q = st.number_input("Qty", 0)
            with c3: p = st.number_input("Price", 0)
            if st.form_submit_button("Save Item"):
                if save_data("Inventory", [i, q, p, str(datetime.now(pk_tz))]):
                    st.success("Item Saved!")
                    st.rerun()
    # Data Table
    st.dataframe(get_data("Inventory"), use_container_width=True)

# --- C. CUSTOMERS ---
elif menu == "Customers":
    with st.expander("bust Add Customer", expanded=False):
        with st.form("cus"):
            n = st.text_input("Customer Name")
            b = st.number_input("Opening Balance", 0)
            if st.form_submit_button("Add Customer"):
                if save_data("Customers", [n, b, "Active", str(datetime.now(pk_tz))]):
                    st.success("Customer Added!")
                    st.rerun()
    st.dataframe(get_data("Customers"), use_container_width=True)

# --- D. SALES ---
elif menu == "Sales":
    cust_df = get_data("Customers")
    # Safe retrieval of customer list
    cust_list = []
    if not cust_df.empty:
        # Check column name spelling from your sheet
        if "Customer" in cust_df.columns: cust_list = cust_df["Customer"].tolist()
        elif "Customer Name" in cust_df.columns: cust_list = cust_df["Customer Name"].tolist()
        elif "Name" in cust_df.columns: cust_list = cust_df["Name"].tolist()

    with st.expander("💰 Create Invoice", expanded=True):
        with st.form("sal"):
            c = st.selectbox("Customer", cust_list) if cust_list else st.text_input("Customer Name")
            c1, c2 = st.columns(2)
            with c1: a = st.number_input("Total Amount", 0)
            with c2: p = st.number_input("Paid", 0)
            n = st.text_input("Items Detail")
            if st.form_submit_button("Save Sale"):
                if save_data("Sales", [c, n, 1, a, p, str(datetime.now(pk_tz))]): # Adjusted order based on typical needs
                    st.success("Sale Recorded!")
                    st.rerun()
    st.dataframe(get_data("Sales"), use_container_width=True)

# --- E. EXPENSES ---
elif menu == "Expenses":
    with st.expander("💸 Add Expense", expanded=False):
        with st.form("exp"):
            t = st.text_input("Title")
            a = st.number_input("Amount", 0)
            c = st.text_input("Category")
            if st.form_submit_button("Save"):
                if save_data("Expenses", [t, a, c, str(datetime.now(pk_tz))]):
                    st.success("Saved!")
                    st.rerun()
    st.dataframe(get_data("Expenses"), use_container_width=True)

# --- F. BANK ---
elif menu == "Bank":
    with st.expander("🏦 Add Transaction", expanded=False):
        with st.form("bnk"):
            d = st.text_input("Detail")
            a = st.number_input("Amount", 0)
            t = st.selectbox("Type", ["Deposit", "Withdrawal"])
            if st.form_submit_button("Save"):
                if save_data("Bank", [d, a, t, str(datetime.now(pk_tz))]):
                    st.success("Saved!")
                    st.rerun()
    st.dataframe(get_data("Bank"), use_container_width=True)
