import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# --- 🎨 HIGH CONTRAST STYLING (BLACK TEXT ON WHITE) ---
st.markdown("""
    <style>
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        h1, h2, h3, h4, h5, h6, p, div, span, label { color: #000000 !important; font-family: 'Arial', sans-serif; font-weight: bold; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; border: 2px solid #000; }
        .stTextInput input, .stNumberInput input, .stSelectbox div { border: 2px solid #000 !important; color: black !important; }
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
        ws = get_worksheet_safe(get_connection(), "Users")
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

def load_data(tab):
    try:
        ws = get_worksheet_safe(get_connection(), tab)
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
        ws = get_worksheet_safe(get_connection(), tab)
        ws.append_row([st.session_state["username"]] + row_data)
        return True
    except: return False

def delete_entry(tab, row_index):
    try:
        ws = get_worksheet_safe(get_connection(), tab)
        ws.delete_rows(row_index + 2) # +2 because of 0-index and header row
        return True
    except: return False

def reset_monthly_data():
    client = get_connection()
    suffix = datetime.now(pytz.timezone('Asia/Karachi')).strftime("_%b_%Y")
    for t in ["Purchase", "Sale", "Expenses"]:
        ws = get_worksheet_safe(client, t)
        if ws:
            # Rename for Restore/Backup
            ws.update_title(f"{t}{suffix}")
            # Create fresh sheet
            new_ws = client.add_worksheet(title=t, rows="1000", cols="20")
            headers = ["Owner", "Date", "Party Name", "Weight", "Rate", "Amount", "Details"] if t=="Purchase" else \
                      ["Owner", "Date", "Customer Name", "Bill No", "Weight", "Rate", "Amount", "Details"] if t=="Sale" else \
                      ["Owner", "Date", "Category", "Amount", "Details"]
            new_ws.append_row(headers)
    return True

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})

if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("⚖️ SI Traders Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
            users_df = get_users_from_sheet() #
            if not users_df.empty and u in users_df["Username"].values:
                match = users_df[users_df["Username"] == u].iloc[0]
                if str(match["Password"]) == p:
                    st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
            st.error("Invalid Credentials")
    st.stop()

# --- 5. MAIN APP ---
pk_tz = pytz.timezone('Asia/Karachi') #
# DATE FORMAT FIX: 21-Jan-2026
formatted_date = datetime.now(pk_tz).strftime("%d-%b-%Y")

# Sidebar Menu (Proper Urdu)
with st.sidebar:
    st.title(f"👤 {st.session_state['username']}")
    menu_options = ["خریداری", "فروخت", "اخراجات", "کلوزنگ"]
    if st.session_state["user_role"] == "Admin": menu_options.append("ایڈمن پینل")
    menu = st.radio("Menu", menu_options)
    if st.button("Logout"): st.session_state["logged_in"]=False; st.rerun()

# === A. KHAREEDARI ===
if menu == "خریداری":
    st.header("نئی خریداری")
    with st.form("buy"):
        party = st.text_input("Party Name")
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight", format="%.3f"); r = c2.number_input("Rate")
        if st.form_submit_button("Save Purchase"):
            if save_data("Purchase", [formatted_date, party, w, r, w*r, ""]):
                st.success(f"Saved: {formatted_date}"); time.sleep(1); st.rerun()
    
    st.subheader("Purchase History")
    df = load_data("Purchase")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        # MANUAL RESET/DELETE OPTION
        row_to_del = st.selectbox("Select Row to Delete (Ghalat entry khatam karein)", range(len(df)), format_func=lambda x: f"Row {x+1}: {df.iloc[x]['Party Name']}")
        if st.button("🗑️ Delete Selected Entry"):
            if delete_entry("Purchase", row_index=row_to_del):
                st.success("Entry Deleted!"); time.sleep(1); st.rerun()

# === B. FAROKHT ===
elif menu == "فروخت":
    st.header("نئی فروخت")
    with st.form("sell"):
        cust = st.text_input("Customer Name"); bill = st.text_input("Bill No")
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight", format="%.3f"); r = c2.number_input("Rate")
        if st.form_submit_button("Save Sale"):
            if save_data("Sale", [formatted_date, cust, bill, w, r, w*r, ""]):
                st.success("Sale Saved!"); time.sleep(1); st.rerun()
    
    st.subheader("Sale History")
    df = load_data("Sale")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        row_to_del = st.selectbox("Select Row to Delete", range(len(df)), format_func=lambda x: f"Row {x+1}: {df.iloc[x]['Customer Name']}")
        if st.button("🗑️ Delete Selected Entry"):
            if delete_entry("Sale", row_index=row_to_del):
                st.success("Deleted!"); time.sleep(1); st.rerun()

# === C. EXPENDITURE ===
elif menu == "اخراجات":
    st.header("Daily Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Shop", "Imran Ali", "Salman Khan"])
        amt = st.number_input("Amount")
        if st.form_submit_button("Save"):
            if save_data("Expenses", [formatted_date, cat, amt, ""]):
                st.success("Saved!"); time.sleep(1); st.rerun()

# === D. CLOSING ===
elif menu == "کلوزنگ":
    st.header("Monthly Closing")
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    tb = b["Amount"].sum() if not b.empty else 0
    ts = s["Amount"].sum() if not s.empty else 0
    te = e["Amount"].sum() if not e.empty else 0
    st.metric("Net Profit", f"Rs {ts - tb - te:,}")

# === E. ADMIN (ONLY VISIBLE TO ADMIN) ===
elif menu == "ایڈمن پینل":
    st.header("Admin Control HQ")
    st.subheader("Monthly Restore / Reset")
    st.warning("⚠️ Yeh button dabane se sara purana data Archive ho jaye ga aur nayi sheets ban jayen gi.")
    if st.button("🔴 Reset Month & Restore Fresh Sheets"):
        if reset_monthly_data(): st.success("Data Restored! Nayi sheets ban gayi hain."); st.balloons()
