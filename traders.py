import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders Pro", page_icon="⚖️", layout="wide")

# --- 🎨 PRO STYLING ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; color: #000000 !important; }
        h1, h2, h3 { color: #1a4d2e !important; font-family: 'Arial', sans-serif; font-weight: 800; }
        .total-box {
            background-color: #ffffff; padding: 15px; border-radius: 12px;
            border-left: 8px solid #1a4d2e; margin-bottom: 20px; 
            font-weight: bold; font-size: 20px; color: #1a4d2e;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .stButton>button { 
            background-color: #1a4d2e; color: white; border-radius: 8px; font-weight: bold; 
            border: none; padding: 10px 20px; width: 100%;
        }
        .stButton>button:hover { background-color: #143d23; color: white; }
        div[data-testid="stSelectbox"] > div > div { background-color: #1a4d2e; color: white; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets: st.error("Secrets Missing"); st.stop()
    creds_dict = dict(st.secrets["service_account"])
    # Handle private key formatting issues
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
        client = get_connection()
        ws = get_ws(client, tab)
        raw = ws.get_all_values()
        if len(raw) < 2: return pd.DataFrame()
        headers = raw.pop(0)
        df = pd.DataFrame(raw, columns=headers)
        
        cols = ["Weight", "Rate", "Amount"] if tab in ["Purchase", "Sale"] else ["Amount"]
        for c in cols:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        if st.session_state.get("user_role") != "Admin" and "Owner" in df.columns:
            df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

# 🔥 UPDATE FUNCTION (MANUAL EDIT) 🔥
def update_google_sheet(tab, edited_df):
    try:
        client = get_connection()
        ws = get_ws(client, tab)
        
        # Fill missing system fields
        if "Owner" in edited_df.columns:
            edited_df["Owner"] = edited_df["Owner"].replace("", st.session_state["username"]).fillna(st.session_state["username"])
        if "Date" in edited_df.columns:
             pk_tz = pytz.timezone('Asia/Karachi')
             today = datetime.now(pk_tz).strftime("%d-%b-%Y")
             edited_df["Date"] = edited_df["Date"].replace("", today).fillna(today)

        clean_df = edited_df.fillna("") 
        data_list = [clean_df.columns.values.tolist()] + clean_df.values.tolist()
        ws.clear()
        ws.update(data_list)
        return True
    except Exception as e:
        st.error(f"Update Error: {e}")
        return False

# 🔥 THE RESTORE (RESET) FUNCTION 🔥
def restore_and_reset_month(profit, earning):
    client = get_connection()
    pk_tz = pytz.timezone('Asia/Karachi')
    m_name = datetime.now(pk_tz).strftime("%B_%Y")
    
    # 1. Save Summary
    s_ws = get_ws(client, "Summary")
    if not s_ws: 
        s_ws = client.add_worksheet("Summary", 100, 5)
        s_ws.append_row(["Month", "Earning", "Profit", "Date"])
    s_ws.append_row([m_name, earning, profit, datetime.now(pk_tz).strftime("%d-%b-%Y")])
    
    # 2. Archive & Clear Data
    tabs_to_reset = ["Purchase", "Sale", "Expenses"]
    
    for t in tabs_to_reset:
        ws = get_ws(client, t)
        if ws:
            # Get old data
            old_data = ws.get_all_values()
            
            # Create Backup Sheet (e.g. Purchase_Jan_2026)
            try:
                client.add_worksheet(f"{t}_{m_name}", 1000, 10).append_rows(old_data)
            except:
                # If sheet exists, append random number to avoid crash
                client.add_worksheet(f"{t}_{m_name}_{int(time.time())}", 1000, 10).append_rows(old_data)

            # Clear Main Sheet & Restore Headers
            headers = old_data[0] if old_data else []
            ws.clear()
            if headers: ws.append_row(headers)
            
    return True

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})
if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # Logo Logic
        if os.path.exists("logo.jpeg.jpeg"): st.image("logo.jpeg.jpeg", use_container_width=True)
        elif os.path.exists("logo.jpeg"): st.image("logo.jpeg", use_container_width=True)
        elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        
        st.markdown("<h2 style='text-align: center;'>SI Traders Login</h2>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔐 Login"):
            if u == "admin" and p == "admin123":
                st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
            ws = get_ws(get_connection(), "Users")
            udf = pd.DataFrame(ws.get_all_records())
            if not udf.empty and u in udf["Username"].values:
                match = udf[udf["Username"] == u].iloc[0]
                if str(match["Password"]) == p:
                    st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
            st.error("Invalid Credentials")
    st.stop()

# --- 5. MAIN APP ---
pk_tz = pytz.timezone('Asia/Karachi')
f_date = datetime.now(pk_tz).strftime("%d-%b-%Y")

c1, c2 = st.columns([1,4])
with c1:
    if os.path.exists("logo.jpeg.jpeg"): st.image("logo.jpeg.jpeg", width=120)
    elif os.path.exists("logo.jpeg"): st.image("logo.jpeg", width=120)
    elif os.path.exists("logo.png"): st.image("logo.png", width=120)
with c2:
    st.markdown(f"## {st.session_state['username']}")
    st.caption(f"📅 Date: {f_date}")

opts = ["خریداری (Purchase)", "فروخت (Sale)", "اخراجات (Expenses)", "کلوزنگ (Closing)"]
if st.session_state["user_role"] == "Admin": opts.append("ایڈمن پینل (Admin)")
menu = st.selectbox("", opts, label_visibility="collapsed")
st.divider()

# === PURCHASE ===
if "خریداری" in menu:
    st.markdown("### 🟢 نئی خریداری (New Purchase)")
    with st.form("buy", clear_on_submit=True):
        party = st.text_input("Party Name")
        c1, c2 = st.columns(2)
        w = c1.number_input("Wazan", format="%.3f"); r = c2.number_input("Rate")
        if st.form_submit_button("💾 Save Entry"):
            ws = get_ws(get_connection(), "Purchase")
            ws.append_row([st.session_state["username"], f_date, party, w, r, w*r, ""])
            st.success("Saved!"); time.sleep(0.5); st.rerun()

    df = load_data("Purchase")
    if not df.empty:
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='total-box'>📦 کل وزن: {df['Weight'].sum():,.3f} Kg</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='total-box'>💰 کل رقم: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)
        
        st.info("📝 Neechay table mein edit karein.")
        edited_df = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Amount": st.column_config.NumberColumn(disabled=True),
                "Owner": st.column_config.TextColumn(disabled=True),
                "Date": st.column_config.TextColumn(disabled=True)
            }
        )
        if st.button("💾 Save Changes to Sheet", type="primary"):
            edited_df["Amount"] = edited_df["Weight"] * edited_df["Rate"]
            if update_google_sheet("Purchase", edited_df):
                st.success("Updated Successfully!"); time.sleep(1); st.rerun()

# === SALE ===
elif "فروخت" in menu:
    st.markdown("### 🔴 نئی فروخت (New Sale)")
    with st.form("sell", clear_on_submit=True):
        cust = st.text_input("Customer"); bill = st.text_input("Bill No")
        c1, c2 = st.columns(2)
        w = c1.number_input("Wazan", format="%.3f"); r = c2.number_input("Rate")
        if st.form_submit_button("💾 Save Entry"):
            ws = get_ws(get_connection(), "Sale")
            ws.append_row([st.session_state["username"], f_date, cust, bill, w, r, w*r, ""])
            st.success("Saved!"); time.sleep(0.5); st.rerun()

    df = load_data("Sale")
    if not df.empty:
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='total-box'>📦 کل وزن: {df['Weight'].sum():,.3f} Kg</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='total-box'>💰 کل رقم: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)
        
        edited_df = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Amount": st.column_config.NumberColumn(disabled=True),
                "Owner": st.column_config.TextColumn(disabled=True),
                "Date": st.column_config.TextColumn(disabled=True)
            }
        )
        if st.button("💾 Save Changes to Sheet", type="primary"):
            edited_df["Amount"] = edited_df["Weight"] * edited_df["Rate"]
            if update_google_sheet("Sale", edited_df):
                st.success("Updated!"); time.sleep(1); st.rerun()

# === EXPENSES ===
elif "اخراجات" in menu:
    st.markdown("### 💸 اخراجات (Expenses)")
    with st.form("exp", clear_on_submit=True):
        cat = st.selectbox("Category", ["Shop", "Imran Ali", "Salman Khan"])
        amt = st.number_input("Amount"); det = st.text_input("Details")
        if st.form_submit_button("Save"):
            ws = get_ws(get_connection(), "Expenses")
            ws.append_row([st.session_state["username"], f_date, cat, amt, det])
            st.rerun()
            
    df = load_data("Expenses")
    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, column_config={"Owner": st.column_config.TextColumn(disabled=True)})
        if st.button("💾 Save Changes", type="primary"):
            if update_google_sheet("Expenses", edited_df): st.success("Updated!"); st.rerun()

# === CLOSING ===
elif "کلوزنگ" in menu:
    st.markdown("### 📒 ماہانہ رپورٹ")
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    tb = b["Amount"].sum() if not b.empty else 0
    ts = s["Amount"].sum() if not s.empty else 0
    te = e["Amount"].sum() if not e.empty else 0
    net = ts - tb - te
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Purchase", f"{tb:,.0f}")
    col2.metric("Total Sale", f"{ts:,.0f}")
    col3.metric("Shop Expense", f"{te:,.0f}")
    st.markdown(f"<div style='text-align:center; padding:20px; background:#c8e6c9; border-radius:10px;'><h1 style='color:green; margin:0;'>Net Profit: Rs {net:,.0f}</h1></div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📜 پچھلے مہینوں کا ریکارڈ")
    sdf = load_data("Summary")
    if not sdf.empty: st.dataframe(sdf, use_container_width=True)

# === ADMIN (RESTORE FEATURE) ===
elif "ایڈمن" in menu:
    st.header("⚙️ Admin Panel")
    st.subheader("🔴 Restore / Start New Month")
    st.info("Yeh option dabane se purana data Archive mein chala jaye ga aur aap ki app bilkul nayi ho jaye gi taake aap dubara likhna shuru kar saken.")
    st.warning("⚠️ Warning: Main sheets (Purchase/Sale) saaf ho jayen gi.")
    
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    earn = s["Amount"].sum() if not s.empty else 0
    prof = earn - (b["Amount"].sum() if not b.empty else 0) - (e["Amount"].sum() if not e.empty else 0)
    
    if st.button("🔴 Restore App & Start New Month", type="primary"):
        with st.spinner("Restoring... Please wait"):
            if restore_and_reset_month(prof, earn):
                st.success("App Restored! Purana data save ho gaya aur sheets saaf ho gayin."); 
                st.balloons(); time.sleep(2); st.rerun()

if st.button("🚪 Logout"): st.session_state.clear(); st.rerun()
