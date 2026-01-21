import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# --- 🎨 HIGH CONTRAST STYLING (MOBILE FRIENDLY) ---
st.markdown("""
    <style>
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        h1, h2, h3, h4, h5, h6, p, div, span, label { color: #2c3e50 !important; font-family: 'Arial', sans-serif; }
        .metric-card { 
            background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; 
            border-radius: 12px; border-left: 6px solid #2e7d32; text-align: center; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; 
        }
        .metric-value { font-size: 26px; font-weight: 800; color: #2e7d32 !important; }
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div { 
            background-color: #f0f2f5 !important; color: #000000 !important; 
            border: 1px solid #ced4da !important; border-radius: 8px !important; 
        }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .invoice-box { background: white; padding: 20px; border: 2px solid #333; color: black; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets: st.error("Secrets Missing"); st.stop()
    creds_dict = dict(st.secrets["service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").replace('\\', '') if creds_dict["private_key"].startswith('\\') else creds_dict["private_key"].replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    # Sheet Name: Trade
    return client.open("Trade")

# --- 3. HELPER FUNCTIONS ---
def get_worksheet_safe(client, tab_name):
    try: return client.worksheet(tab_name)
    except: 
        try: return client.worksheet(tab_name + "s") 
        except: return None

def load_data(tab):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        if not ws: return pd.DataFrame()
        raw_data = ws.get_all_values()
        if not raw_data: return pd.DataFrame()
        headers = raw_data.pop(0)
        df = pd.DataFrame(raw_data, columns=headers)
        for c in ["Weight", "Rate", "Amount"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if not df.empty and "Owner" in df.columns and st.session_state.get("user_role") != "Admin":
            df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

def save_data(tab, row_data):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        if not ws: st.error(f"Sheet '{tab}' nahi mili."); return False
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except: return False

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})

if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("⚖️ SI Traders Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            # Check for Admin or fetch from Users sheet
            if u == "admin" and p == "admin123":
                st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop()

# --- 5. MAIN APP ---
menu = st.sidebar.radio("Menu", ["🟢 Khareedari", "🔴 Farokht", "💸 Kharcha", "📒 Closing"])
if st.sidebar.button("Logout"): st.session_state["logged_in"]=False; st.rerun()

# Date Formatting Logic (Karachi Time)
pk_tz = pytz.timezone('Asia/Karachi')
current_date = datetime.now(pk_tz).strftime("%Y-%m-%d")

# === A. KHAREEDARI ===
if menu == "🟢 Khareedari":
    st.header("🛒 Nayi Khareedari")
    with st.form("buy"):
        party = st.text_input("Party Name")
        c1, c2 = st.columns(2)
        w = c1.number_input("Wazan", format="%.3f")
        r = c2.number_input("Rate")
        if st.form_submit_button("Save"):
            total = w * r
            # FORMAT: Owner, Date, Party, Weight, Rate, Amount, Details
            if save_data("Purchase", [current_date, party, w, r, total, ""]):
                st.success(f"Saved for date: {current_date}"); time.sleep(1); st.rerun()
    
    df = load_data("Purchase")
    if not df.empty:
        st.subheader("History")
        st.dataframe(df, use_container_width=True)

# === B. FAROKHT ===
elif menu == "🔴 Farokht":
    st.header("🏷️ Nayi Farokht")
    with st.form("sell"):
        cust = st.text_input("Customer Name")
        bill = st.text_input("Bill No")
        c1, c2 = st.columns(2)
        w = c1.number_input("Wazan", format="%.3f")
        r = c2.number_input("Rate")
        if st.form_submit_button("Save & Bill"):
            total = w * r
            if save_data("Sale", [current_date, cust, bill, w, r, total, ""]):
                st.success("Sale Saved!"); time.sleep(1); st.rerun()

# === C. KHARCHA ===
elif menu == "💸 Kharcha":
    st.header("💸 Rozana Kharcha")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Dukan", "Imran Ali", "Salman Khan"])
        amt = st.number_input("Amount")
        if st.form_submit_button("Save Expense"):
            if save_data("Expenses", [current_date, cat, amt, ""]):
                st.success("Expense Recorded!"); time.sleep(1); st.rerun()

# === D. CLOSING ===
elif menu == "📒 Closing":
    st.header("📒 Mahana Closing")
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    
    t_buy = b["Amount"].sum() if not b.empty else 0
    t_sell = s["Amount"].sum() if not s.empty else 0
    t_exp = e["Amount"].sum() if not e.empty else 0
    
    net = t_sell - t_buy - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Purchases", f"Rs {t_buy:,}")
    c2.metric("Total Sales", f"Rs {t_sell:,}")
    c3.metric("Net Profit", f"Rs {net:,}")
