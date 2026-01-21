import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# --- 🎨 BEHTAR INTERFACE (STYLING) ---
st.markdown("""
    <style>
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        h1, h2, h3, h4, h5, h6, p, div, span, label { color: #000000 !important; font-family: 'Arial', sans-serif; }
        .metric-card { 
            background-color: #f8f9fa; border: 2px solid #2e7d32; padding: 20px; 
            border-radius: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); 
        }
        .total-box {
            background-color: #e8f5e9; padding: 10px; border-radius: 10px;
            border-left: 5px solid #2e7d32; margin: 10px 0; font-weight: bold;
        }
        .stButton>button { border-radius: 10px; font-weight: bold; border: 2px solid #000; height: 3em; }
        .stTextInput input, .stNumberInput input, .stSelectbox div { border: 2px solid #000 !important; }
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
    return gspread.authorize(creds).open("Trade")

# --- 3. HELPER FUNCTIONS ---
def get_ws(client, name):
    try: return client.worksheet(name)
    except: return None

def load_data(tab):
    try:
        ws = get_ws(get_connection(), tab)
        raw = ws.get_all_values()
        if len(raw) < 2: return pd.DataFrame()
        headers = raw.pop(0)
        df = pd.DataFrame(raw, columns=headers)
        for c in ["Weight", "Rate", "Amount"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if st.session_state.get("user_role") != "Admin":
            df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

def save_data(tab, row_data):
    try:
        ws = get_ws(get_connection(), tab)
        ws.append_row([st.session_state["username"]] + row_data)
        return True
    except: return False

def delete_entry(tab, row_index):
    try:
        ws = get_ws(get_connection(), tab)
        ws.delete_rows(row_index + 2)
        return True
    except: return False

# 🔥 MONTHLY RESET & SUMMARY LOGIC
def reset_month_and_log_summary(profit, earning):
    client = get_connection()
    pk_tz = pytz.timezone('Asia/Karachi')
    month_name = datetime.now(pk_tz).strftime("%B_%Y")
    
    # 1. Save Summary to a 'Summary' sheet
    summary_ws = get_ws(client, "Summary")
    if not summary_ws:
        summary_ws = client.add_worksheet(title="Summary", rows="100", cols="5")
        summary_ws.append_row(["Month", "Total Earning", "Net Profit", "Date"])
    summary_ws.append_row([month_name, earning, profit, datetime.now(pk_tz).strftime("%d-%b-%Y")])

    # 2. Archive Current Tabs
    for t in ["Purchase", "Sale", "Expenses"]:
        ws = get_ws(client, t)
        if ws:
            old_data = ws.get_all_values()
            client.add_worksheet(title=f"{t}_{month_name}", rows="1000", cols="10").append_rows(old_data)
            ws.clear()
            ws.append_row(old_data[0]) # Put headers back
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
            ws = get_ws(get_connection(), "Users")
            users_df = pd.DataFrame(ws.get_all_records())
            if not users_df.empty and u in users_df["Username"].values:
                match = users_df[users_df["Username"] == u].iloc[0]
                if str(match["Password"]) == p:
                    st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
            st.error("Invalid Credentials")
    st.stop()

# --- 5. MAIN APP ---
pk_tz = pytz.timezone('Asia/Karachi') #
f_date = datetime.now(pk_tz).strftime("%d-%b-%Y")

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['username']}")
    menu = st.radio("Menu", ["خریداری", "فروخت", "اخراجات", "کلوزنگ", "ایڈمن پینل"] if st.session_state["user_role"] == "Admin" else ["خریداری", "فروخت", "اخراجات", "کلوزنگ"])
    if st.button("🚪 Logout"): st.session_state.clear(); st.rerun()

# === A. PURCHASE (خریداری) ===
if menu == "خریداری":
    st.header("🟢 نئی خریداری")
    with st.form("buy"):
        party = st.text_input("Party Name")
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight (Wazan)", format="%.3f"); r = c2.number_input("Rate")
        if st.form_submit_button("💾 Save Entry"):
            if save_data("Purchase", [f_date, party, w, r, w*r, ""]):
                st.success("Saved!"); st.rerun()
    
    st.divider()
    df = load_data("Purchase")
    if not df.empty:
        # SEARCH & TOTALS
        st.subheader("🔍 تلاش اور تفصیل (Search & Totals)")
        search = st.text_input("Naam likh kar dhoondain (Search Party Name)...")
        if search: df = df[df['Party Name'].str.contains(search, case=False)]
        
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='total-box'>Kul Wazan: {df['Weight'].sum():,.3f} Kg</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='total-box'>Kul Raqam: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True)
        idx = st.selectbox("Select Row to Delete", range(len(df)), format_func=lambda x: f"Delete: {df.iloc[x]['Party Name']}")
        if st.button("🗑️ Delete Selected"):
            if delete_entry("Purchase", idx): st.success("Deleted!"); st.rerun()

# === B. SALE (فروخت) ===
elif menu == "فروخت":
    st.header("🔴 نئی فروخت")
    with st.form("sell"):
        cust = st.text_input("Customer Name"); bill = st.text_input("Bill No")
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight", format="%.3f"); r = c2.number_input("Rate")
        if st.form_submit_button("💾 Save Sale"):
            if save_data("Sale", [f_date, cust, bill, w, r, w*r, ""]):
                st.success("Saved!"); st.rerun()

    st.divider()
    df = load_data("Sale")
    if not df.empty:
        search = st.text_input("Search Customer/Bill No...")
        if search: df = df[df['Customer Name'].str.contains(search, case=False) | df['Bill No'].str.contains(search, case=False)]
        
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='total-box'>Kul Wazan: {df['Weight'].sum():,.3f} Kg</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='total-box'>Kul Bill Amount: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True)
        idx = st.selectbox("Select Row to Delete", range(len(df)), format_func=lambda x: f"Delete: {df.iloc[x]['Customer Name']}")
        if st.button("🗑️ Delete Selected"):
            if delete_entry("Sale", idx): st.success("Deleted!"); st.rerun()

# === C. EXPENSES (اخراجات) ===
elif menu == "اخراجات":
    st.header("💸 روزانہ کے اخراجات")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Shop", "Imran Ali", "Salman Khan"])
        amt = st.number_input("Amount")
        if st.form_submit_button("Save Expense"):
            if save_data("Expenses", [f_date, cat, amt, ""]):
                st.success("Saved!"); st.rerun()
    st.dataframe(load_data("Expenses"), use_container_width=True)

# === D. CLOSING (کلوزنگ) ===
elif menu == "کلوزنگ":
    st.header("📒 ماہانہ رپورٹ (Monthly Report)")
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    tb = b["Amount"].sum() if not b.empty else 0
    ts = s["Amount"].sum() if not s.empty else 0
    te = e["Amount"].sum() if not e.empty else 0
    profit = ts - tb - te
    
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='metric-card'><h3>Kul Earning</h3><h1 style='color:blue'>Rs {ts:,}</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h3>Saaf Munafa (Net Profit)</h3><h1 style='color:green'>Rs {profit:,}</h1></div>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📜 پچھلے مہینوں کا ریکارڈ (Past Month Summary)")
    summary_df = load_data("Summary")
    if not summary_df.empty:
        st.dataframe(summary_df, use_container_width=True)
    else: st.info("Abhi tak koi summary archive nahi hui.")

# === E. ADMIN PANEL ===
elif menu == "ایڈمن پینل":
    st.header("⚙️ ایڈمن پینل")
    st.subheader("ماہانہ ری سیٹ (Monthly Reset)")
    st.warning("⚠️ Yeh button mahinay ke end par dabayen. Purana data archive ho jaye ga aur Summary page par profit/earning save ho jaye gi.")
    
    # Calculate current stats for summary before reset
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    cur_earning = s["Amount"].sum() if not s.empty else 0
    cur_profit = cur_earning - (b["Amount"].sum() if not b.empty else 0) - (e["Amount"].sum() if not e.empty else 0)
    
    if st.button("🔴 Start New Month & Archive Record"):
        if reset_month_and_log_summary(cur_profit, cur_earning):
            st.success("Data Archived! Naya mahina shuru ho gaya."); st.balloons(); time.sleep(1); st.rerun()
