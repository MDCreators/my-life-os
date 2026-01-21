import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# --- 🎨 PRO STYLING (MOBILE OPTIMIZED) ---
st.markdown("""
    <style>
        /* 1. Force Light Background & Dark Text (Fix for Mobile Dark Mode) */
        .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        
        /* 2. All Text Black */
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #2c3e50 !important;
            font-family: 'Arial', sans-serif;
        }
        
        /* 3. Metrics & Cards styling */
        .metric-card {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 15px;
            border-radius: 12px;
            border-left: 6px solid #2e7d32;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 26px;
            font-weight: 800;
            color: #2e7d32 !important;
        }
        .metric-label {
            font-size: 14px;
            color: #666 !important;
            text-transform: uppercase;
        }
        
        /* 4. Input Fields Styling (High Contrast) */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: #f0f2f5 !important;
            color: #000000 !important;
            border: 1px solid #ced4da !important;
            border-radius: 8px !important;
        }
        /* Labels above inputs */
        .stTextInput label, .stNumberInput label, .stSelectbox label {
            font-weight: bold;
            color: #333333 !important;
        }
        
        /* 5. Buttons Styling */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            font-weight: bold;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        /* 6. HIDE STREAMLIT BRANDING (Clean Look) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Print Styles */
        .invoice-box { background: white; padding: 20px; border: 2px solid #333; }
        @media print { 
            [data-testid="stSidebar"] { display: none; } 
            .stApp { background: white; }
            .invoice-box { position: absolute; top: 0; left: 0; width: 100%; border: none; } 
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets: st.error("Secrets Missing"); st.stop()
    creds = dict(st.secrets["service_account"])
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").replace('\\', '') if creds["private_key"].startswith('\\') else creds["private_key"].replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Trade")

# --- 3. HELPER FUNCTIONS ---
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
        
        # Numeric Conversion
        for c in ["Weight", "Rate", "Amount"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        if not df.empty and "Owner" in df.columns and st.session_state.get("user_role") != "Admin":
            df = df[df["Owner"] == st.session_state["username"]]
            
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

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})

if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚖️ SI Traders")
        st.caption("Secure Login System")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("🔐 Login"):
                if u=="admin" and p=="admin123":
                    st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
                users = get_users()
                if not users.empty:
                    match = users[(users["Username"]==u) & (users["Password"]==p)]
                    if not match.empty:
                        st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
                    else: st.error("❌ Invalid ID/Pass")
                else: st.error("❌ User Not Found")
    st.stop()

# --- 5. MAIN APP ---
with st.sidebar:
    st.title(f"👤 {st.session_state['username']}")
    st.write("---")
    tabs = ["🟢 Khareedari", "🔴 Farokht", "💸 Kharcha", "📒 Closing"]
    if st.session_state["user_role"] == "Admin": tabs.append("👥 Users")
    menu = st.radio("Main Menu", tabs)
    st.write("---")
    if st.button("🚪 Logout"): st.session_state["logged_in"]=False; st.rerun()

if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === A. KHAREEDARI ===
if "Khareedari" in menu:
    st.header("🛒 Khareedari Entry")
    with st.form("buy"):
        c1,c2 = st.columns(2)
        party = c1.text_input("Party Name")
        r = c2.number_input("Rate (Bhaao)", min_value=0)
        
        c3, c4 = st.columns(2)
        w = c3.number_input("Wazan (Weight)", format="%.3f")
        unit = c4.selectbox("Unit", ["Kg", "Grams"])
        
        det = st.text_input("Tafseel")
        
        fw = w if unit=="Kg" else w/1000
        total = fw*r
        
        st.info(f"💰 Total: **Rs {total:,.0f}**")
        
        if st.form_submit_button("📥 Save Record"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Purchase", [date, party, fw, r, total, det]):
                st.success("Saved!"); time.sleep(1); st.rerun()
    
    st.subheader("Recent History")
    df = load_data("Purchase")
    if not df.empty:
        search = st.text_input("🔍 Search Party...", key="sb")
        if search: df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
        st.dataframe(df, use_container_width=True)
        
        # Totals
        c1,c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>Total Weight</div><div class='metric-value'>{df['Weight'].sum():,.3f} Kg</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>Total Amount</div><div class='metric-value'>Rs {df['Amount'].sum():,.0f}</div></div>", unsafe_allow_html=True)

# === B. FAROKHT ===
elif "Farokht" in menu:
    if st.session_state.invoice_data:
        d = st.session_state.invoice_data
        st.button("🔙 Back", on_click=lambda: st.session_state.pop("invoice_data"))
        st.markdown(f"""<div class='invoice-box'><center><h1>SI TRADERS</h1><p>Deals in all kinds of Scrap</p></center><hr><p><b>Bill No:</b> {d['bill']}<br><b>Customer:</b> {d['cust']}<br><b>Date:</b> {d['date']}</p><table width='100%' style='border-collapse: collapse;'><tr><th style='text-align:left; border-bottom:1px solid #ddd;'>Item</th><th style='border-bottom:1px solid #ddd;'>Weight</th><th style='border-bottom:1px solid #ddd;'>Rate</th><th style='text-align:right; border-bottom:1px solid #ddd;'>Amount</th></tr><tr><td style='padding:8px 0;'>{d['det']}</td><td style='text-align:center;'>{d['w']}</td><td style='text-align:center;'>{d['r']}</td><td style='text-align:right;'>{d['a']}</td></tr></table><br><h3 style='text-align:right;'>Total: Rs {d['a']}</h3></div>""", unsafe_allow_html=True)
        st.info("💡 Screenshot le lein ya Ctrl+P daba kar print karein")
    else:
        st.header("🏷️ Farokht Entry")
        with st.form("sell"):
            c1,c2 = st.columns(2); cust=c1.text_input("Customer Name"); bill=c2.text_input("Bill No")
            c3,c4 = st.columns(2); w=c3.number_input("Wazan", format="%.3f"); unit=c4.selectbox("Unit", ["Kg","Grams"])
            c5,c6 = st.columns(2); r=c5.number_input("Rate"); det=c6.text_input("Tafseel")
            
            fw = w if unit=="Kg" else w/1000
            total = fw*r
            st.info(f"💰 Bill Amount: **Rs {total:,.0f}**")
            
            if st.form_submit_button("🖨️ Save & Bill"):
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

# === C. KHARCHA ===
elif "Kharcha" in menu:
    st.header("💸 Daily Kharcha")
    with st.form("exp"):
        cat = st.selectbox("Kharcha Type", ["Dukan (Shop Expense)", "Imran Ali (Personal)", "Salman Khan (Personal)"])
        c1, c2 = st.columns(2)
        amt = c1.number_input("Amount", min_value=0)
        det = c2.text_input("Details")
        
        if st.form_submit_button("💾 Save Expense"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Expenses", [date, cat, amt, det]):
                st.success("Saved!"); time.sleep(1); st.rerun()
    
    st.subheader("📜 Today's Expenses")
    df = load_data("Expenses")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.markdown(f"<div style='background:#fee2e2; color:#b91c1c; padding:10px; border-radius:8px; font-weight:bold; text-align:center;'>Total Kharcha: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)

# === D. CLOSING ===
elif "Closing" in menu:
    st.header("📒 Munafa & Hisaab")
    
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    
    buy_sum = b["Amount"].sum() if not b.empty else 0
    sell_sum = s["Amount"].sum() if not s.empty else 0
    buy_w = b["Weight"].sum() if not b.empty else 0
    sell_w = s["Weight"].sum() if not s.empty else 0
    
    shop_exp = e[e["Category"] == "Dukan (Shop Expense)"]["Amount"].sum() if not e.empty else 0
    imran = e[e["Category"] == "Imran Ali (Personal)"]["Amount"].sum() if not e.empty else 0
    salman = e[e["Category"] == "Salman Khan (Personal)"]["Amount"].sum() if not e.empty else 0
    
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

elif "Users" in menu:
    u=st.text_input("New User"); p=st.text_input("Pass")
    if st.button("Create"): 
        try: get_connection().worksheet("Users").append_row([u,p]); st.success("Done")
        except: st.error("Error")
    st.dataframe(get_users())
