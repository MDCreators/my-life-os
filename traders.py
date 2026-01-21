import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time
import extra_streamlit_components as stx

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS (ENGLISH INPUTS, URDU TABS) ---
st.markdown("""
    <link rel="apple-touch-icon" href="https://img.icons8.com/color/48/scales.png">
    <link rel="icon" type="image/png" href="https://img.icons8.com/color/48/scales.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    
    <style>
        /* 1. APP BACKGROUND */
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        
        /* 2. TEXT STYLING */
        h1, h2, h3, h4, h5, h6, p, div, span, label, li, button { 
            color: #2c3e50 !important; 
            font-family: 'Arial', sans-serif; 
        }
        
        /* 3. HIDE BRANDING */
        header {visibility: hidden !important; height: 0px !important;}
        footer {visibility: hidden !important; height: 0px !important;}
        #MainMenu {visibility: hidden !important; display: none !important;}
        .stDeployButton {display: none !important;}
        div[data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        div[data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
        
        /* 4. NAVIGATION TABS (Urdu Style) */
        div[data-testid="stRadio"] > div {
            flex-direction: row-reverse; /* Tabs Right to Left */
            justify-content: center;
            background-color: #f8f9fa;
            border-radius: 15px;
            padding: 5px;
            margin-bottom: 20px;
            overflow-x: auto;
        }
        div[data-testid="stRadio"] label {
            background-color: transparent !important;
            padding: 10px 15px !important;
            border-radius: 10px !important;
            margin: 0 2px !important;
            cursor: pointer;
            border: 1px solid transparent;
        }
        div[data-testid="stRadio"] label[data-checked="true"] {
            background-color: #2e7d32 !important;
            color: white !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        div[data-testid="stRadio"] label p { font-size: 16px !important; font-weight: bold !important; }
        div[data-testid="stRadio"] label[data-checked="true"] p { color: white !important; }

        /* 5. INPUT FIELDS (Left Align for English) */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div { 
            text-align: left; /* English typing style */
            background-color: #f0f2f5 !important;
            color: #000000 !important;
            border: 1px solid #ced4da !important;
            border-radius: 8px !important;
        }
        
        /* 6. BUTTONS */
        .stButton>button { 
            width: 100%; border-radius: 8px; height: 3em; font-weight: bold; border: none; 
            background: linear-gradient(to right, #2e7d32, #1b5e20); color: white !important; 
            font-size: 18px !important;
        }
        
        /* 7. CARDS */
        .metric-card { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 12px; border-left: 6px solid #2e7d32; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
        .metric-value { font-size: 26px; font-weight: 800; color: #2e7d32 !important; }
        
        /* 8. PRINT */
        .invoice-box { background: white; padding: 20px; border: 2px solid #333; }
        @media print { .stApp { background: white; } .invoice-box { position: absolute; top: 0; left: 0; width: 100%; border: none; } div[data-testid="stRadio"] {display: none;} }
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets: st.error("Secrets Missing"); st.stop()
    creds = dict(st.secrets["service_account"])
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").replace('\\', '') if creds["private_key"].startswith('\\') else creds["private_key"].replace("\\n", "\n")
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Trade")

# --- 4. HELPER FUNCTIONS ---
def get_worksheet_safe(client, tab_name):
    try: return client.worksheet(tab_name)
    except: 
        try: return client.worksheet(tab_name + "s") 
        except: return None

def get_users():
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, "Users") or get_worksheet_safe(client, "User")
        if not ws: return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        headers = data.pop(0)
        return pd.DataFrame(data, columns=headers)
    except: return pd.DataFrame()

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
        current_user = st.session_state.get("username")
        current_role = st.session_state.get("user_role")
        if not df.empty and "Owner" in df.columns and current_role != "Admin":
            df = df[df["Owner"] == current_user]
        return df
    except Exception as e:
        if "200" in str(e): return pd.DataFrame()
        return pd.DataFrame()

def save_data(tab, row_data):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        if not ws: st.error(f"Sheet '{tab}' nahi mili."); return False
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        if "200" in str(e): return True
        st.error(f"Save Error: {e}")
        return False

# --- 5. COOKIE & LOGIN ---
cookie_manager = stx.CookieManager()
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})

cookie_user = cookie_manager.get(cookie="traders_user")
cookie_role = cookie_manager.get(cookie="traders_role")

if not st.session_state["logged_in"]:
    if cookie_user and cookie_role:
        st.session_state.update({"logged_in": True, "username": cookie_user, "user_role": cookie_role})
        st.rerun()
    else:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("<br><br><h1 style='text-align:center;'>⚖️ SI Traders</h1>", unsafe_allow_html=True)
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("🔐 Login"):
                    if u=="admin" and p=="admin123":
                        st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"})
                        cookie_manager.set("traders_user", "Admin", expires_at=datetime.now() + timedelta(days=30))
                        cookie_manager.set("traders_role", "Admin", expires_at=datetime.now() + timedelta(days=30))
                        st.rerun()
                    users = get_users()
                    if not users.empty:
                        match = users[(users["Username"]==u) & (users["Password"]==p)]
                        if not match.empty:
                            st.session_state.update({"logged_in":True, "username":u, "user_role":"User"})
                            cookie_manager.set("traders_user", u, expires_at=datetime.now() + timedelta(days=30))
                            cookie_manager.set("traders_role", "User", expires_at=datetime.now() + timedelta(days=30))
                            st.rerun()
                        else: st.error("❌ Invalid ID/Pass")
                    else: st.error("❌ User Not Found")
        st.stop()

# --- 6. MAIN APP ---
st.markdown(f"<div style='text-align:center; color:#666; margin-bottom:10px;'>👤 {st.session_state['username']}</div>", unsafe_allow_html=True)

# URDU TABS (As Requested)
tabs = ["🛒 خریداری", "🏷️ فروخت", "💸 اخراجات", "📒 کلوزنگ", "👥 یوزرز"]
if st.session_state["user_role"] != "Admin":
    tabs.remove("👥 یوزرز")

selected_tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed")

if st.button("🚪 Logout", key="logout_top"): 
    cookie_manager.delete("traders_user")
    cookie_manager.delete("traders_role")
    st.session_state["logged_in"]=False
    st.rerun()

st.write("---")

if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === A. KHAREEDARI (HEADING URDU, LABELS ENGLISH) ===
if "خریداری" in selected_tab:
    st.markdown("<h2 style='text-align:center;'>🛒 نئی خریداری</h2>", unsafe_allow_html=True)
    with st.form("buy"):
        c1,c2 = st.columns(2)
        party = c1.text_input("Party Name")
        r = c2.number_input("Rate", min_value=0)
        
        c3, c4 = st.columns(2)
        w = c3.number_input("Weight", format="%.3f")
        unit = c4.selectbox("Unit", ["Kg", "Grams"])
        
        det = st.text_input("Details")
        
        fw = w if unit=="Kg" else w/1000
        total = fw*r
        
        st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>Total: Rs {total:,.0f}</h3>", unsafe_allow_html=True)
        if st.form_submit_button("💾 Save Purchase"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Purchase", [date, party, fw, r, total, det]):
                st.success("Saved Successfully!"); time.sleep(1); st.rerun()
    
    st.subheader("Recent History")
    df = load_data("Purchase")
    if not df.empty:
        search = st.text_input("🔍 Search Party...", key="sb")
        if search: df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
        st.dataframe(df, use_container_width=True)
        c1,c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>Total Weight</div><div class='metric-value'>{df['Weight'].sum():,.3f} Kg</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>Total Amount</div><div class='metric-value'>Rs {df['Amount'].sum():,.0f}</div></div>", unsafe_allow_html=True)

# === B. FAROKHT (HEADING URDU, LABELS ENGLISH) ===
elif "فروخت" in selected_tab:
    if st.session_state.invoice_data:
        d = st.session_state.invoice_data
        st.button("🔙 Back", on_click=lambda: st.session_state.pop("invoice_data"))
        st.markdown(f"""
        <div class='invoice-box'>
            <center><h1>SI TRADERS</h1><p>Deals in all kinds of Scrap</p></center><hr>
            <p><b>Bill No:</b> {d['bill']}<br><b>Customer:</b> {d['cust']}<br><b>Date:</b> {d['date']}</p>
            <table width='100%' style='border-collapse: collapse;'>
                <tr style='background:#eee;'><th style='text-align:left;'>Item</th><th>Weight</th><th>Rate</th><th style='text-align:right;'>Amount</th></tr>
                <tr><td style='padding:8px 0;'>{d['det']}</td><td style='text-align:center;'>{d['w']}</td><td style='text-align:center;'>{d['r']}</td><td style='text-align:right;'>{d['a']}</td></tr>
            </table><br>
            <h3 style='text-align:right;'>Total: Rs {d['a']}</h3>
        </div>""", unsafe_allow_html=True)
        st.info("💡 Print or Screenshot")
    else:
        st.markdown("<h2 style='text-align:center;'>🏷️ نئی فروخت</h2>", unsafe_allow_html=True)
        with st.form("sell"):
            c1,c2 = st.columns(2); cust=c1.text_input("Customer Name"); bill=c2.text_input("Bill No")
            c3,c4 = st.columns(2); w=c3.number_input("Weight", format="%.3f"); unit=c4.selectbox("Unit", ["Kg","Grams"])
            c5,c6 = st.columns(2); r=c5.number_input("Rate"); det=c6.text_input("Details")
            
            fw = w if unit=="Kg" else w/1000
            total = fw*r
            st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>Bill: Rs {total:,.0f}</h3>", unsafe_allow_html=True)
            if st.form_submit_button("🖨️ Save & Print"):
                date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
                if save_data("Sale", [date, cust, bill, fw, r, total, det]):
                    st.session_state.invoice_data = {"date":date, "cust":cust, "bill":bill, "w":fw, "r":r, "a":f"{total:,.0f}", "det":det}
                    st.rerun()
        st.subheader("Recent History")
        df = load_data("Sale")
        if not df.empty:
            search = st.text_input("🔍 Search Bill/Customer...", key="ss")
            if search: df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
            st.dataframe(df, use_container_width=True)

# === C. KHARCHA (HEADING URDU, LABELS ENGLISH) ===
elif "اخراجات" in selected_tab:
    st.markdown("<h2 style='text-align:center;'>💸 روزانہ خرچہ</h2>", unsafe_allow_html=True)
    with st.form("exp"):
        cat = st.selectbox("Category", ["Shop Expense", "Imran Ali (Personal)", "Salman Khan (Personal)"])
        c1, c2 = st.columns(2); amt = c1.number_input("Amount", min_value=0); det = c2.text_input("Details")
        
        if st.form_submit_button("💾 Save Expense"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Expenses", [date, cat, amt, det]):
                st.success("Saved Successfully!"); time.sleep(1); st.rerun()
    st.subheader("Today's Expenses")
    df = load_data("Expenses")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.markdown(f"<div style='background:#fee2e2; color:#b91c1c; padding:10px; border-radius:8px; font-weight:bold; text-align:center;'>Total Expense: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)

# === D. CLOSING (HEADING URDU, LABELS ENGLISH) ===
elif "کلوزنگ" in selected_tab:
    st.markdown("<h2 style='text-align:center;'>📒 کلوزنگ / منافع</h2>", unsafe_allow_html=True)
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    
    buy_sum = b["Amount"].sum() if not b.empty else 0
    sell_sum = s["Amount"].sum() if not s.empty else 0
    buy_w = b["Weight"].sum() if not b.empty else 0
    sell_w = s["Weight"].sum() if not s.empty else 0
    
    # Handle both Urdu/English category names for safety
    shop_exp = e[e["Category"].isin(["Shop Expense", "Dukan (Shop Expense)", "دکان کا خرچہ"])]["Amount"].sum() if not e.empty else 0
    imran = e[e["Category"].isin(["Imran Ali (Personal)", "عمران علی (ذاتی)"])]["Amount"].sum() if not e.empty else 0
    salman = e[e["Category"].isin(["Salman Khan (Personal)", "سلمان خان (ذاتی)"])]["Amount"].sum() if not e.empty else 0
    
    gross = sell_sum - buy_sum
    net = gross - shop_exp
    stock = buy_w - sell_w
    cash = net - (imran + salman)
    
    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><div class='metric-label'>Stock in Hand</div><div class='metric-value'>{stock:,.1f} Kg</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-label'>Gross Profit</div><div class='metric-value'>Rs {gross:,.0f}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='border-left-color:#d32f2f;'><div class='metric-label'>Shop Expense</div><div class='metric-value' style='color:#d32f2f !important;'>- {shop_exp:,.0f}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<h2 style='text-align:center; color:#2e7d32;'>✅ Net Profit: Rs {net:,.0f}</h2>", unsafe_allow_html=True)
    st.markdown("### 👥 Partners Drawings")
    cc1, cc2 = st.columns(2)
    cc1.info(f"Imran Ali: Rs {imran:,.0f}")
    cc2.info(f"Salman Khan: Rs {salman:,.0f}")
    st.success(f"💵 **Net Cash in Hand:** Rs {cash:,.0f}")

elif "یوزرز" in selected_tab:
    st.header("👥 User Management")
    u=st.text_input("New User"); p=st.text_input("Pass")
    if st.button("Create"): 
        try: get_connection().worksheet("Users").append_row([u,p]); st.success("Done")
        except: st.error("Error")
    st.dataframe(get_users())
