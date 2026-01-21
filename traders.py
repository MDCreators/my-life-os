import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# CSS Styling (Urdu Font Support)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');
        .stApp { background-color: #f4f6f9; font-family: 'Noto Nastaliq Urdu', sans-serif; }
        h1, h2, h3, .stButton button, .stRadio label { font-family: 'Noto Nastaliq Urdu', sans-serif; }
        
        .metric-card { background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
        .expense-card { border-left: 5px solid #d32f2f; }
        .invoice-box { background: white; padding: 30px; border: 1px solid #eee; }
        @media print { [data-testid="stSidebar"] { display: none; } .invoice-box { position: absolute; top: 0; left: 0; width: 100%; } }
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
    # Correct Sheet ID from previous fix
    sheet_id = "1SQUMvySccNWz_G3ziZmiFB9Ry2thjxdnNGWvhppv-dE"
    return client.open_by_key(sheet_id)

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
        st.title("⚖️ SI Traders Login")
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u=="admin" and p=="admin123":
                st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
            users = get_users()
            if not users.empty:
                match = users[(users["Username"]==u) & (users["Password"]==p)]
                if not match.empty:
                    st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
                else: st.error("Invalid Credentials")
            else: st.error("No Users Found")
    st.stop()

# --- 5. MAIN APP ---
st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("Logout"): st.session_state["logged_in"]=False; st.rerun()

# --- URDU MENU ---
tabs = ["🟢 خریداری", "🔴 فروخت", "💸 اخراجات", "📒 کلوزنگ"]
if st.session_state["user_role"] == "Admin": tabs.append("👥 Users")
menu = st.radio("مینو", tabs, horizontal=True, label_visibility="collapsed")
st.divider()

if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === A. KHAREEDARI (PURCHASE) ===
if "خریداری" in menu:
    st.header("🛒 نئی خریداری")
    with st.form("buy"):
        c1,c2,c3 = st.columns(3)
        party = c1.text_input("پارٹی کا نام")
        w_col, u_col = c2.columns([2,1])
        w = w_col.number_input("وزن", format="%.3f"); unit = u_col.selectbox("یونٹ", ["Kg", "Grams"])
        r = c3.number_input("ریٹ")
        det = st.text_input("تفصیل")
        fw = w if unit=="Kg" else w/1000
        total = fw*r
        st.markdown(f"### 💰 کل رقم: {total:,.0f}")
        if st.form_submit_button("📥 خریداری محفوظ کریں"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Purchase", [date, party, fw, r, total, det]):
                st.success("محفوظ ہو گیا!"); time.sleep(1); st.rerun()
    
    st.subheader("📜 خریداری کی ہسٹری")
    df = load_data("Purchase")
    if not df.empty:
        # SEARCH BAR
        search = st.text_input("🔍 پارٹی تلاش کریں...", key="search_buy")
        if search:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
        
        st.dataframe(df, use_container_width=True)
        c1,c2 = st.columns(2)
        c1.info(f"کل وزن: {df['Weight'].sum():,.3f} Kg")
        c2.info(f"کل رقم: Rs {df['Amount'].sum():,.0f}")
    else: st.warning("کوئی ڈیٹا موجود نہیں۔")

# === B. FAROKHT (SALE) ===
elif "فروخت" in menu:
    if st.session_state.invoice_data:
        d = st.session_state.invoice_data
        st.button("🔙 واپس", on_click=lambda: st.session_state.pop("invoice_data"))
        st.markdown(f"""<div class='invoice-box' style='direction: rtl; text-align: right;'><center><h2>SI TRADERS</h2></center><hr><p><b>بل نمبر:</b> {d['bill']} | <b>کسٹمر:</b> {d['cust']}</p><table width='100%' style='text-align: right;'><tr><td><b>آئٹم</b></td><td><b>وزن</b></td><td><b>ریٹ</b></td><td><b>رقم</b></td></tr><tr><td>{d['det']}</td><td>{d['w']}</td><td>{d['r']}</td><td>{d['a']}</td></tr></table></div>""", unsafe_allow_html=True)
    else:
        st.header("🏷️ نئی فروخت")
        with st.form("sell"):
            c1,c2 = st.columns(2); cust=c1.text_input("کسٹمر کا نام"); bill=c2.text_input("بل نمبر")
            c3,c4 = st.columns(2); w_col, u_col = c3.columns([2,1]); w=w_col.number_input("وزن", format="%.3f"); unit=u_col.selectbox("یونٹ", ["Kg","Grams"]); r=c4.number_input("ریٹ")
            det = st.text_input("تفصیل")
            fw = w if unit=="Kg" else w/1000
            total = fw*r
            st.markdown(f"### بل: {total:,.0f}")
            if st.form_submit_button("🖨️ محفوظ کریں اور پرنٹ"):
                date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
                if save_data("Sale", [date, cust, bill, fw, r, total, det]):
                    st.session_state.invoice_data = {"date":date, "cust":cust, "bill":bill, "w":fw, "r":r, "a":f"{total:,.0f}", "det":det}
                    st.rerun()
        
        st.subheader("📜 فروخت کی ہسٹری")
        df = load_data("Sale")
        if not df.empty:
            # SEARCH BAR
            search = st.text_input("🔍 کسٹمر / بل تلاش کریں...", key="search_sell")
            if search:
                df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
            
            st.dataframe(df, use_container_width=True)

# === C. EXPENSES (URDU) ===
elif "اخراجات" in menu:
    st.header("💸 اخراجات کا اندراج")
    with st.form("exp"):
        c1, c2 = st.columns(2)
        # Dropdown in Urdu
        cat = c1.selectbox("خرچہ کی قسم", ["دکان کے اخراجات", "عمران علی (ذاتی)", "سلمان خان (ذاتی)"])
        amt = c2.number_input("رقم", min_value=0)
        det = st.text_input("تفصیل (مثلاً: چائے، بجلی کا بل)", placeholder="تفصیل لکھیں...")
        
        if st.form_submit_button("💾 خرچہ محفوظ کریں"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Expenses", [date, cat, amt, det]):
                st.success("خرچہ محفوظ ہو گیا!"); time.sleep(1); st.rerun()
    
    st.subheader("📜 اخراجات کی فہرست")
    df = load_data("Expenses")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        total_exp = df["Amount"].sum()
        st.error(f"کل اخراجات: Rs {total_exp:,.0f}")

# === D. CLOSING (URDU) ===
elif "کلوزنگ" in menu:
    st.header("📒 منافع اور حساب (Closing)")
    
    # Load All Data
    b = load_data("Purchase")
    s = load_data("Sale")
    e = load_data("Expenses")
    
    # Calculate Basics
    buy_total = b["Amount"].sum() if not b.empty else 0
    sell_total = s["Amount"].sum() if not s.empty else 0
    buy_weight = b["Weight"].sum() if not b.empty else 0
    sell_weight = s["Weight"].sum() if not s.empty else 0
    
    # Gross Profit
    gross_profit = sell_total - buy_total
    stock_in_hand = buy_weight - sell_weight
    
    # Expense Breakdown (Using Urdu Labels)
    shop_exp = 0
    imran_draw = 0
    salman_draw = 0
    
    if not e.empty:
        shop_exp = e[e["Category"] == "دکان کے اخراجات"]["Amount"].sum()
        imran_draw = e[e["Category"] == "عمران علی (ذاتی)"]["Amount"].sum()
        salman_draw = e[e["Category"] == "سلمان خان (ذاتی)"]["Amount"].sum()
    
    # Final Math
    net_profit = gross_profit - shop_exp
    cash_in_hand = net_profit - (imran_draw + salman_draw)

    # --- DISPLAY ---
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 موجودہ اسٹاک", f"{stock_in_hand:,.1f} Kg")
    c2.metric("💰 کاروباری منافع (Gross)", f"Rs {gross_profit:,.0f}")
    c3.metric("📉 دکان کا خرچہ", f"- Rs {shop_exp:,.0f}")
    
    st.divider()
    
    # Net Profit Section
    st.markdown(f"### ✅ صاف منافع (Net Profit): Rs {net_profit:,.0f}")
    
    st.write("---")
    st.subheader("👥 پارٹنرز کا حساب")
    
    # Partners Cards
    pc1, pc2 = st.columns(2)
    pc1.info(f"👤 **عمران علی** نے لیے: Rs {imran_draw:,.0f}")
    pc2.info(f"👤 **سلمان خان** نے لیے: Rs {salman_draw:,.0f}")
    
    st.success(f"💵 **بقایا کیش (Net Cash):** Rs {cash_in_hand:,.0f}")

elif "Users" in menu:
    u=st.text_input("User"); p=st.text_input("Pass")
    if st.button("Create"): 
        try: get_connection().worksheet("Users").append_row([u,p]); st.success("Done")
        except: st.error("Error")
    st.dataframe(get_users())
