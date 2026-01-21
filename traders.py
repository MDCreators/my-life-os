import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# --- 🎨 STYLING ---
st.markdown("""
    <style>
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        
        /* Urdu Font for Headers */
        h1, h2, h3 { font-family: 'Jameel Noori Nastaleeq', 'Arial', sans-serif; text-align: right; }
        
        /* English Font for Body */
        p, div, span, label, button, input, th, td { font-family: 'Arial', sans-serif; }
        
        .metric-card { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 12px; border-left: 6px solid #2e7d32; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
        .metric-value { font-size: 26px; font-weight: 800; color: #2e7d32 !important; }
        .metric-label { font-size: 14px; color: #666 !important; text-transform: uppercase; }
        
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div { background-color: #f0f2f5 !important; color: #000000 !important; border: 1px solid #ced4da !important; border-radius: 8px !important; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        
        /* HIDE BRANDING */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} [data-testid="stToolbar"] {visibility: hidden;} .stDeployButton {display:none;}
        
        /* PRINT */
        .invoice-box { background: white; padding: 20px; border: 2px solid #333; }
        @media print { [data-testid="stSidebar"] { display: none; } .stApp { background: white; } .invoice-box { position: absolute; top: 0; left: 0; width: 100%; border: none; } }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION (FIXED) ---
def get_connection():
    if "service_account" not in st.secrets: st.error("Secrets Missing"); st.stop()
    creds_dict = dict(st.secrets["service_account"])
    
    # Fix Key Formatting
    if "private_key" in creds_dict:
        key = creds_dict["private_key"]
        if key.startswith("\\"): key = key[1:]
        creds_dict["private_key"] = key.replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # 🔥 FIXED LINE: info=creds_dict (Yeh pehlay ghalat tha)
    creds = Credentials.from_service_account_info(info=creds_dict, scopes=scope)
    
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
        return pd.DataFrame()

def save_data(tab, row_data):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# 🔥 EDIT & UPDATE FUNCTION
def update_sheet_data(tab, edited_df):
    try:
        client = get_connection()
        ws = get_worksheet_safe(client, tab)
        ws.clear()
        edited_df = edited_df.fillna("")
        data_to_write = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
        ws.update(data_to_write)
        return True
    except Exception as e:
        st.error(f"Update Error: {e}")
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
                    match = users[(users["Username"].astype(str)==u) & (users["Password"].astype(str)==p)]
                    if not match.empty:
                        st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
                    else: st.error("❌ Invalid ID/Pass")
                else: st.warning("⚠️ No users found. Login with 'admin' / 'admin123'")
    st.stop()

# --- 5. MAIN APP ---
with st.sidebar:
    st.title(f"👤 {st.session_state['username']}")
    st.write("---")
    
    # 🔥 URDU TABS (Right to Left)
    tabs = ["خریداری", "فروخت", "اخراجات", "منافع / حساب"]
    if st.session_state["user_role"] == "Admin": tabs.append("Users")
    
    menu = st.radio("Menu", tabs)
    st.write("---")
    if st.button("🚪 Logout"): st.session_state["logged_in"]=False; st.rerun()

if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === A. KHAREEDARI ===
if menu == "خریداری":
    # Urdu Header
    st.markdown("<h2>🛒 نئی خریداری</h2>", unsafe_allow_html=True)
    
    # English Form
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
        st.info(f"💰 Total Amount: **Rs {total:,.0f}**")
        
        if st.form_submit_button("📥 Save Purchase"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Purchase", [date, party, fw, r, total, det]):
                st.success("✅ Saved Successfully!"); time.sleep(1); st.rerun()
    
    st.subheader("📜 Edit History")
    df = load_data("Purchase")
    if not df.empty:
        search = st.text_input("🔍 Search Party...", key="sb")
        if search: df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
        
        # 🔥 EDITABLE GRID
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="edit_buy")
        
        # 🔥 AUTO-CALCULATION
        edited_df["Amount"] = edited_df["Weight"] * edited_df["Rate"]
        
        # Show updated totals
        c1,c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>Total Weight</div><div class='metric-value'>{edited_df['Weight'].sum():,.3f} Kg</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>Total Amount</div><div class='metric-value'>Rs {edited_df['Amount'].sum():,.0f}</div></div>", unsafe_allow_html=True)
        
        if st.button("💾 Update Google Sheet", key="upd_buy"):
            if update_sheet_data("Purchase", edited_df):
                st.success("✅ Sheet Updated!"); time.sleep(1); st.rerun()

# === B. FAROKHT ===
elif menu == "فروخت":
    if st.session_state.invoice_data:
        d = st.session_state.invoice_data
        st.button("🔙 Back", on_click=lambda: st.session_state.pop("invoice_data"))
        st.markdown(f"""<div class='invoice-box'><center><h1>SI TRADERS</h1><p>Deals in all kinds of Scrap</p></center><hr><p><b>Bill No:</b> {d['bill']}<br><b>Customer:</b> {d['cust']}<br><b>Date:</b> {d['date']}</p><table width='100%' style='border-collapse: collapse;'><tr><th style='text-align:left; border-bottom:1px solid #ddd;'>Item</th><th style='border-bottom:1px solid #ddd;'>Weight</th><th style='border-bottom:1px solid #ddd;'>Rate</th><th style='text-align:right; border-bottom:1px solid #ddd;'>Amount</th></tr><tr><td style='padding:8px 0;'>{d['det']}</td><td style='text-align:center;'>{d['w']}</td><td style='text-align:center;'>{d['r']}</td><td style='text-align:right;'>{d['a']}</td></tr></table><br><h3 style='text-align:right;'>Total: Rs {d['a']}</h3></div>""", unsafe_allow_html=True)
    else:
        st.markdown("<h2>🏷️ نئی فروخت</h2>", unsafe_allow_html=True)
        with st.form("sell"):
            c1,c2 = st.columns(2); cust=c1.text_input("Customer Name"); bill=c2.text_input("Bill No")
            c3,c4 = st.columns(2); w=c3.number_input("Weight", format="%.3f"); unit=c4.selectbox("Unit", ["Kg","Grams"])
            c5,c6 = st.columns(2); r=c5.number_input("Rate"); det=c6.text_input("Details")
            
            fw = w if unit=="Kg" else w/1000
            total = fw*r
            st.info(f"💰 Bill Amount: **Rs {total:,.0f}**")
            
            if st.form_submit_button("🖨️ Save & Print"):
                date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
                if save_data("Sale", [date, cust, bill, fw, r, total, det]):
                    st.session_state.invoice_data = {"date":date, "cust":cust, "bill":bill, "w":fw, "r":r, "a":f"{total:,.0f}", "det":det}
                    st.rerun()
        
        st.subheader("📜 Edit History")
        df = load_data("Sale")
        if not df.empty:
            search = st.text_input("🔍 Search Bill...", key="ss")
            if search: df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
            
            edited_df_sale = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="edit_sale")
            edited_df_sale["Amount"] = edited_df_sale["Weight"] * edited_df_sale["Rate"]
            
            st.markdown(f"<div style='text-align:right; font-weight:bold;'>Updated Total: Rs {edited_df_sale['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)
            
            if st.button("💾 Update Google Sheet", key="upd_sale"):
                if update_sheet_data("Sale", edited_df_sale):
                    st.success("✅ Sheet Updated!"); time.sleep(1); st.rerun()

# === C. EXPENSES ===
elif menu == "اخراجات":
    st.markdown("<h2>💸 روزنامچہ اخراجات</h2>", unsafe_allow_html=True)
    with st.form("exp"):
        cat = st.selectbox("Category", ["Dukan (Shop Expense)", "Imran Ali (Personal)", "Salman Khan (Personal)"])
        c1, c2 = st.columns(2)
        amt = c1.number_input("Amount", min_value=0)
        det = c2.text_input("Details")
        if st.form_submit_button("💾 Save Expense"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Expenses", [date, cat, amt, det]):
                st.success("Saved!"); time.sleep(1); st.rerun()
    
    st.subheader("📜 Edit Expenses")
    df = load_data("Expenses")
    if not df.empty:
        edited_df_exp = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="edit_exp")
        
        if st.button("💾 Update Google Sheet", key="upd_exp"):
            if update_sheet_data("Expenses", edited_df_exp):
                st.success("Updated!"); time.sleep(1); st.rerun()
        
        st.markdown(f"<div style='background:#fee2e2; color:#b91c1c; padding:10px; border-radius:8px; font-weight:bold; text-align:center;'>Total Expense: Rs {edited_df_exp['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)

# === D. CLOSING ===
elif menu == "منافع / حساب":
    st.markdown("<h2>📒 کاروباری حساب</h2>", unsafe_allow_html=True)
    
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
    c2.markdown(f"<div class='metric-card'><div class='metric-label'>Net Profit</div><div class='metric-value'>Rs {net:,.0f}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='border-left-color:#d32f2f;'><div class='metric-label'>Shop Expense</div><div class='metric-value' style='color:#d32f2f !important;'>- {shop_exp:,.0f}</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 👥 Partners Drawings")
    cc1, cc2 = st.columns(2)
    cc1.info(f"👤 Imran Ali: Rs {imran:,.0f}")
    cc2.info(f"👤 Salman Khan: Rs {salman:,.0f}")
    st.success(f"💵 **Net Cash in Hand:** Rs {cash:,.0f}")

elif menu == "Users":
    st.header("👥 Users Management")
    u=st.text_input("New Username"); p=st.text_input("New Password")
    if st.button("Create User"): 
        try: get_connection().worksheet("Users").append_row([u,p]); st.success("Done")
        except: st.error("Error")
    st.dataframe(get_users())
