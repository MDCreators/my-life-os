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
        h1, h2, h3, h4, h5, h6, p, div, span, label { color: #000000 !important; font-family: 'Arial', sans-serif; font-weight: bold; }
        .metric-card { 
            background-color: #f0f2f5; border: 2px solid #2e7d32; padding: 15px; 
            border-radius: 12px; text-align: center; margin-bottom: 10px; 
        }
        .metric-value { font-size: 28px; font-weight: 800; color: #2e7d32 !important; }
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div { 
            background-color: #ffffff !important; color: #000000 !important; 
            border: 2px solid #000000 !important; border-radius: 8px !important; 
        }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
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
    return client.open("Trade") #

# --- 3. HELPER FUNCTIONS ---
def get_worksheet_safe(client, tab_name):
    try: return client.worksheet(tab_name)
    except: return None

def get_users_from_sheet():
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, "Users") #
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except: return pd.DataFrame()

def load_data(tab):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        if not ws: return pd.DataFrame()
        raw_data = ws.get_all_values()
        if len(raw_data) < 2: return pd.DataFrame()
        headers = raw_data.pop(0)
        df = pd.DataFrame(raw_data, columns=headers)
        for c in ["Weight", "Rate", "Amount"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if st.session_state.get("user_role") != "Admin":
            df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

def save_data(tab, row_data):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except: return False

def archive_reset():
    client = get_connection()
    suffix = datetime.now(pytz.timezone('Asia/Karachi')).strftime("_%b_%y_%H%M")
    tabs = ["Purchase", "Sale", "Expenses"]
    for t in tabs:
        ws = get_worksheet_safe(client, t)
        if ws:
            old_data = ws.get_all_values()
            client.add_worksheet(title=f"{t}{suffix}", rows="100", cols="20").append_rows(old_data)
            ws.clear()
            ws.append_row(old_data[0]) # Restore headers
    return True

# --- 4. LOGIN SYSTEM ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})

if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("⚖️ SI Traders Login")
        u = st.text_input("Username (Email)")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
            
            users_df = get_users_from_sheet() #
            if not users_df.empty:
                # Check matching user and password from Google Sheet
                match = users_df[(users_df["Username"] == u) & (users_df["Password"].astype(str) == p)]
                if not match.empty:
                    st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
                else: st.error("❌ Galat Password ya Username")
            else: st.error("❌ Sheet mein koi User nahi mila")
    st.stop()

# --- 5. MAIN APP ---
pk_tz = pytz.timezone('Asia/Karachi') #
current_date = datetime.now(pk_tz).strftime("%Y-%m-%d")

menu = st.sidebar.radio("Main Menu", ["🟢 Khareedari", "🔴 Farokht", "💸 Kharcha", "📒 Closing", "⚙️ Admin"])
if st.sidebar.button("Logout"): st.session_state["logged_in"]=False; st.rerun()

# === A. KHAREEDARI ===
if menu == "🟢 Khareedari":
    st.header("🛒 Nayi Khareedari")
    with st.form("buy"):
        party = st.text_input("Party Name")
        c1, c2 = st.columns(2)
        w = c1.number_input("Wazan", format="%.3f")
        r = c2.number_input("Rate")
        if st.form_submit_button("Save"):
            if save_data("Purchase", [current_date, party, w, r, w*r, ""]):
                st.success("Record Saved!"); time.sleep(1); st.rerun()
    
    st.subheader("📜 History")
    df = load_data("Purchase")
    if not df.empty:
        search = st.text_input("🔍 Search Party Name...", key="s1") #
        if search: df = df[df['Party Name'].str.contains(search, case=False)]
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
            if save_data("Sale", [current_date, cust, bill, w, r, w*r, ""]):
                st.success("Sale Saved!"); time.sleep(1); st.rerun()
    
    df = load_data("Sale")
    if not df.empty:
        search = st.text_input("🔍 Search Customer/Bill...", key="s2")
        if search: df = df[df['Customer Name'].str.contains(search, case=False) | df['Bill No'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True)

# === C. KHARCHA ===
elif menu == "💸 Kharcha":
    st.header("💸 Daily Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Dukan", "Imran Ali", "Salman Khan"]) #
        amt = st.number_input("Amount", min_value=0)
        if st.form_submit_button("Save Expense"):
            if save_data("Expenses", [current_date, cat, amt, ""]):
                st.success("Expense Recorded!"); time.sleep(1); st.rerun()

# === D. CLOSING ===
elif menu == "📒 Closing":
    st.header("📒 Mahana Hisaab")
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    t_buy = b["Amount"].sum() if not b.empty else 0
    t_sell = s["Amount"].sum() if not s.empty else 0
    t_exp = e["Amount"].sum() if not e.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><div class='metric-value'>Rs {t_buy:,}</div><p>Total Purchase</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-value'>Rs {t_sell:,}</div><p>Total Sales</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><div class='metric-value'>Rs {t_sell - t_buy - t_exp:,}</div><p>Net Profit</p></div>", unsafe_allow_html=True)

# === E. ADMIN ===
elif menu == "⚙️ Admin":
    if st.session_state["user_role"] != "Admin":
        st.error("Sirf Admin yeh page dekh sakta hay.")
    else:
        st.header("⚙️ Admin Controls")
        if st.button("🔴 Start New Month (Backup & Reset)"): #
            if archive_reset(): st.success("Data Archived! Nayi Sheets tayyar hain."); st.balloons()
