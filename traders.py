import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp { background-color: #f4f6f9; }
        .metric-card {
            background-color: white; padding: 15px; border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center;
            border-left: 5px solid #2e7d32;
        }
        .sale-card { border-left: 5px solid #c62828; }
        .metric-title { font-size: 14px; color: #555; }
        .metric-value { font-size: 24px; font-weight: bold; color: #000; }
        .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets:
        st.error("🚨 Error: Secrets file mein '[service_account]' section nahi mila.")
        st.stop()
    
    # Secrets se data copy karein
    creds_dict = dict(st.secrets["service_account"])
    
    # Key Cleaning (Previous Fix)
    if "private_key" in creds_dict:
        if creds_dict["private_key"].startswith("\\"):
            creds_dict["private_key"] = creds_dict["private_key"][1:]
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("SI Traders Data")

# --- 3. HELPER FUNCTIONS ---
def get_users():
    try:
        return pd.DataFrame(get_connection().worksheet("Users").get_all_records())
    except: return pd.DataFrame()

def load_data(tab):
    try:
        ws = get_connection().worksheet(tab)
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty and "Owner" in df.columns:
            if st.session_state["user_role"] != "Admin":
                df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

# 🔥 UPDATED SAVE FUNCTION (Ignores 200 Error)
def save_data(tab, row_data):
    try:
        ws = get_connection().worksheet(tab)
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        # Agar error message mein '200' hai, tu wo asal mein success hai
        if "200" in str(e):
            return True
        else:
            st.error(f"Save Error: {e}")
            return False

# --- 4. LOGIN SYSTEM ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = "User"

def login_screen():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("## ⚖️ SI Traders Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if u == "admin" and p == "admin123":
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = "Admin"
                    st.session_state["user_role"] = "Admin"
                    st.rerun()
                
                users = get_users()
                if not users.empty:
                    match = users[(users["Username"].astype(str) == u) & (users["Password"].astype(str) == p)]
                    if not match.empty:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = u
                        st.session_state["user_role"] = "User"
                        st.rerun()
                    else: st.error("Wrong ID/Pass")
                else: st.error("User list empty or sheet error")

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# --- 5. MAIN APP ---
st.sidebar.markdown(f"### 👤 {st.session_state['username']}")
if st.session_state["user_role"] == "Admin":
    st.sidebar.info("🔧 Admin Mode")

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

st.title("⚖️ SI Traders System")
tabs = ["🟢 Khareedari (Purchase)", "🔴 Farokht (Sale)", "📒 Closing (Profit)"]
if st.session_state["user_role"] == "Admin":
    tabs.append("👥 Manage Users")

active_tab = st.radio("Menu", tabs, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# === A. KHAREEDARI ===
if "Khareedari" in active_tab:
    st.header("🟢 Nayi Khareedari")
    with st.form("buy_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        party = c1.text_input("Party Name")
        
        w_col, u_col = c2.columns([2,1])
        raw_weight = w_col.number_input("Wazan", min_value=0.0, format="%.3f")
        unit = u_col.selectbox("Unit", ["Kg", "Grams"])
        
        rate = c3.number_input("Rate (Per Kg)", min_value=0)
        details = st.text_input("Tafseel")
        
        final_weight_kg = raw_weight if unit == "Kg" else raw_weight / 1000
        total_amt = final_weight_kg * rate
        
        st.markdown(f"### 💰 Total: Rs {total_amt:,.0f} <span style='font-size:14px; color:grey'>({final_weight_kg} Kg)</span>", unsafe_allow_html=True)
        
        if st.form_submit_button("📥 Save Purchase"):
            pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Purchase", [pk_time, party, final_weight_kg, rate, total_amt, details]):
                st.success("Saved!")
                st.rerun()

    df = load_data("Purchase")
    if not df.empty:
        t_w = df["Weight"].sum() if "Weight" in df.columns else 0
        t_a = df["Amount"].sum() if "Amount" in df.columns else 0
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><div class='metric-title'>Total Wazan (Kg)</div><div class='metric-value'>{t_w:,.3f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-title'>Total Raqam (Rs)</div><div class='metric-value'>{t_a:,.0f}</div></div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)

# === B. FAROKHT ===
elif "Farokht" in active_tab:
    st.header("🔴 Nayi Farokht")
    with st.form("sell_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        cust = c1.text_input("Customer Name")
        bill = c2.text_input("Bill No")
        
        c3, c4 = st.columns(2)
        w_col, u_col = c3.columns([2,1])
        raw_weight = w_col.number_input("Wazan", min_value=0.0, format="%.3f")
        unit = u_col.selectbox("Unit", ["Kg", "Grams"])
        
        rate = c4.number_input("Rate (Per Kg)", min_value=0)
        
        final_weight_kg = raw_weight if unit == "Kg" else raw_weight / 1000
        total_amt = final_weight_kg * rate
        
        st.markdown(f"### 💰 Bill: Rs {total_amt:,.0f}", unsafe_allow_html=True)
        
        if st.form_submit_button("📤 Save Sale"):
            pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Sale", [pk_time, cust, bill, final_weight_kg, rate, total_amt]):
                st.success("Sold!")
                st.rerun()
            
    df = load_data("Sale")
    if not df.empty:
        t_w = df["Weight"].sum() if "Weight" in df.columns else 0
        t_a = df["Amount"].sum() if "Amount" in df.columns else 0
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card sale-card'><div class='metric-title'>Total Farokht (Kg)</div><div class='metric-value'>{t_w:,.3f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card sale-card'><div class='metric-title'>Total Amount (Rs)</div><div class='metric-value'>{t_a:,.0f}</div></div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)

# === C. CLOSING ===
elif "Closing" in active_tab:
    st.header("📒 Munafa / Nuqsan")
    df_b = load_data("Purchase")
    df_s = load_data("Sale")
    b_w = df_b["Weight"].sum() if not df_b.empty and "Weight" in df_b.columns else 0
    b_a = df_b["Amount"].sum() if not df_b.empty and "Amount" in df_b.columns else 0
    s_w = df_s["Weight"].sum() if not df_s.empty and "Weight" in df_s.columns else 0
    s_a = df_s["Amount"].sum() if not df_s.empty and "Amount" in df_s.columns else 0
    
    net_w = s_w - b_w
    net_p = s_a - b_a
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Baqaya Wazan (Stock)", f"{net_w:,.3f} Kg")
    c2.metric("Net Profit", f"Rs {net_p:,.0f}")
    avg = net_p / net_w if net_w != 0 else 0
    c3.metric("Avg Rate", f"{avg:.1f}")

# === D. MANAGE USERS ===
elif "Manage Users" in active_tab:
    st.header("👥 User Management")
    with st.form("add_u"):
        u = st.text_input("New Username")
        p = st.text_input("New Password")
        if st.form_submit_button("Create User"):
            try:
                ws = get_connection().worksheet("Users")
                ws.append_row([u, p])
                st.success(f"User {u} Created!")
            except Exception as e:
                # 🔥 FIX FOR 200 OK ERROR
                if "200" in str(e):
                    st.success(f"User {u} Created!")
                else:
                    st.error(f"Error: {e}")
            
    st.dataframe(get_users(), use_container_width=True)
