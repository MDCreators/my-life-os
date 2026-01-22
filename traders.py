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

# --- 🎨 PRO STYLING & REFINEMENT ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa !important; color: #212529 !important; }
        h1, h2, h3, h4, h5, h6 { color: #1a4d2e !important; font-family: 'Arial', sans-serif; font-weight: 800; }
        p, div, span, label, th, td { color: #212529 !important; font-family: 'Arial', sans-serif; font-weight: 600; }
        
        /* Navigation Box Styling (Top Menu) */
        div[data-testid="stSelectbox"] > div > div {
            background-color: #1a4d2e !important;
            color: white !important;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
        }
        
        /* Cards & Totals */
        .metric-card { 
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border: 2px solid #1a4d2e; padding: 20px; 
            border-radius: 15px; text-align: center; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 15px;
        }
        .metric-value { font-size: 28px; font-weight: 900; color: #1a4d2e !important; }
        .total-box {
            background-color: #ffffff; padding: 15px; border-radius: 12px;
            border-left: 8px solid #1a4d2e; margin-bottom: 20px; 
            font-weight: bold; font-size: 20px; color: #1a4d2e;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* Buttons & Inputs */
        .stButton>button { 
            border-radius: 10px; font-weight: bold; font-size: 16px;
            background-color: #1a4d2e; color: white; border: none;
            padding: 10px 20px; transition: all 0.3s ease;
        }
        .stButton>button:hover { background-color: #143d23; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        
        .stTextInput input, .stNumberInput input, .stSelectbox div { 
            border: 2px solid #1a4d2e !important; border-radius: 8px; color: black !important;
        }

        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
@st.cache_resource
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
        # Convert numeric columns
        cols_to_num = ["Weight", "Rate", "Amount"] if tab in ["Purchase", "Sale"] else ["Amount"]
        for c in cols_to_num:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
        if st.session_state.get("user_role") != "Admin" and "Owner" in df.columns:
            df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

# 🔥 NEW FUNCTION FOR MANUAL EDITING 🔥
def update_whole_sheet(tab, edited_df):
    try:
        client = get_connection()
        ws = get_ws(client, tab)
        # Ensure Owner column is preserved correctly
        if "Owner" not in edited_df.columns:
             edited_df["Owner"] = st.session_state["username"]

        # Recalculate Amounts if Weight/Rate changed
        if tab in ["Purchase", "Sale"]:
             edited_df["Amount"] = edited_df["Weight"] * edited_df["Rate"]

        # Convert DF back to list of lists for GSheets
        data_to_upload = [edited_df.columns.tolist()] + edited_df.values.tolist()
        
        ws.clear() # Clear old data
        ws.update(range_name='A1', values=data_to_upload) # Upload new edited data
        return True
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False

def reset_month_and_archive(profit, earning):
    client = get_connection()
    pk_tz = pytz.timezone('Asia/Karachi')
    month_name = datetime.now(pk_tz).strftime("%B_%Y")
    
    summary_ws = get_ws(client, "Summary")
    if not summary_ws:
        summary_ws = client.add_worksheet(title="Summary", rows="100", cols="5")
        summary_ws.append_row(["Month", "Total Earning", "Net Profit", "Date"])
    summary_ws.append_row([month_name, earning, profit, datetime.now(pk_tz).strftime("%d-%b-%Y")])

    for t in ["Purchase", "Sale", "Expenses"]:
        ws = get_ws(client, t)
        if ws:
            old_data = ws.get_all_values()
            client.add_worksheet(title=f"{t}_{month_name}", rows="1000", cols="10").append_rows(old_data)
            ws.clear()
            ws.append_row(old_data[0])
    return True

# --- 4. LOGIN SYSTEM ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": "User"})
if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # 🖼️ LOGO PLACEHOLDER (Login Screen)
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        st.title("⚖️ SI Traders Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔐 Login"):
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
pk_tz = pytz.timezone('Asia/Karachi')
f_date = datetime.now(pk_tz).strftime("%d-%b-%Y")

# 🖼️ HEADER WITH LOGO & DATE
c_h1, c_h2 = st.columns([1, 3])
with c_h1:
    # Agar logo.png file mojood hogi to yahan show hogi
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
with c_h2:
    st.title("SI Traders Management System")
    st.caption(f"👤 Logged in as: {st.session_state['username']} | 📅 Date: {f_date}")

# 📱 TOP NAVIGATION (MOBILE FIX)
menu_options = ["🛒 خریداری (Purchase)", "🏷️ فروخت (Sale)", "💸 اخراجات (Expenses)", "📒 کلوزنگ (Closing)"]
if st.session_state["user_role"] == "Admin": menu_options.append("⚙️ ایڈمن پینل (Admin)")
menu = st.selectbox("▼ مینیو منتخب کریں (Select Menu)", menu_options)
st.divider()

# === A. PURCHASE (خریداری) ===
if "خریداری" in menu:
    st.header("🛒 خریداری کا ریکارڈ")
    
    # 1. Add New Entry Form (Quick Add)
    with st.expander("➕ نئی خریداری شامل کریں (Add New Purchase)", expanded=False):
        with st.form("buy_quick", clear_on_submit=True):
            party_q = st.text_input("Party Name")
            c1q, c2q = st.columns(2)
            w_q = c1q.number_input("Weight", format="%.3f"); r_q = c2q.number_input("Rate")
            if st.form_submit_button("💾 Save Entry"):
                ws = get_ws(get_connection(), "Purchase")
                ws.append_row([st.session_state["username"], f_date, party_q, w_q, r_q, w_q*r_q, "Quick Add"])
                st.success("Saved!"); time.sleep(0.5); st.rerun()

    # 2. Data Viewer & Editor
    df = load_data("Purchase")
    if not df.empty:
        # Totals Section
        c_t1, c_t2 = st.columns(2)
        c_t1.markdown(f"<div class='total-box'>📦 کل وزن: {df['Weight'].sum():,.3f} Kg</div>", unsafe_allow_html=True)
        c_t2.markdown(f"<div class='total-box'>💰 کل رقم: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)

        st.subheader("📝 ریکارڈ میں تبدیلی کریں (Edit Record)")
        st.info("💡 Tip: آپ نیچے دیے گئے ٹیبل میں براہ راست کلک کر کے ڈیٹا تبدیل کر سکتے ہیں۔ تبدیلی کے بعد 'Save Changes' کا بٹن دبائیں۔")
        
        # 🔥 THE MAGIC EDITOR 🔥
        edited_df = st.data_editor(
            df,
            num_rows="dynamic", # Allows adding/deleting rows in grid
            use_container_width=True,
            key="purchase_editor",
            column_config={
                "Amount": st.column_config.NumberColumn(disabled=True), # Amount auto-calculates
                "Owner": st.column_config.TextColumn(disabled=True),
                "Date": st.column_config.TextColumn(disabled=True)
            }
        )

        if st.button("💾 Save Changes to Google Sheet", type="primary"):
            with st.spinner("Saving changes to cloud..."):
                if update_whole_sheet("Purchase", edited_df):
                    st.success("✅ تمام تبدیلیاں محفوظ کر لی گئی ہیں!"); time.sleep(1); st.rerun()

# === B. SALE (فروخت) ===
elif "فروخت" in menu:
    st.header("🏷️ فروخت کا ریکارڈ")
    
    # 1. Add New Entry
    with st.expander("➕ نئی فروخت شامل کریں (Add New Sale)", expanded=False):
        with st.form("sell_quick", clear_on_submit=True):
            cust_q = st.text_input("Customer Name"); bill_q = st.text_input("Bill No")
            c1q, c2q = st.columns(2)
            w_q = c1q.number_input("Weight", format="%.3f"); r_q = c2q.number_input("Rate")
            if st.form_submit_button("💾 Save Sale"):
                ws = get_ws(get_connection(), "Sale")
                ws.append_row([st.session_state["username"], f_date, cust_q, bill_q, w_q, r_q, w_q*r_q, "Quick Add"])
                st.success("Saved!"); time.sleep(0.5); st.rerun()

    # 2. Data Editor
    df = load_data("Sale")
    if not df.empty:
        c_t1, c_t2 = st.columns(2)
        c_t1.markdown(f"<div class='total-box'>📦 کل وزن: {df['Weight'].sum():,.3f} Kg</div>", unsafe_allow_html=True)
        c_t2.markdown(f"<div class='total-box'>💰 کل بل: Rs {df['Amount'].sum():,.0f}</div>", unsafe_allow_html=True)

        st.subheader("📝 ریکارڈ میں تبدیلی کریں (Edit Record)")
        st.info("💡 Tip: ٹیبل میں براہ راست تبدیلی کریں اور نیچے سیو کا بٹن دبائیں۔")

        edited_df_s = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="sale_editor",
            column_config={
                "Amount": st.column_config.NumberColumn(disabled=True),
                "Owner": st.column_config.TextColumn(disabled=True),
                "Date": st.column_config.TextColumn(disabled=True)
            }
        )
        if st.button("💾 Save Changes to Google Sheet", key="save_sale", type="primary"):
             with st.spinner("Updating cloud records..."):
                if update_whole_sheet("Sale", edited_df_s):
                    st.success("✅ فروخت کا ریکارڈ اپ ڈیٹ ہو گیا!"); time.sleep(1); st.rerun()

# === C. EXPENSES (اخراجات) ===
elif "اخراجات" in menu:
    st.header("💸 اخراجات کا ریکارڈ")
    
    with st.form("exp_quick", clear_on_submit=True):
        c1, c2 = st.columns(2)
        cat_q = c1.selectbox("Category", ["Shop", "Imran Ali", "Salman Khan", "Other"])
        amt_q = c2.number_input("Amount")
        det_q = st.text_input("Details")
        if st.form_submit_button("Save Expense"):
             ws = get_ws(get_connection(), "Expenses")
             ws.append_row([st.session_state["username"], f_date, cat_q, amt_q, det_q])
             st.rerun()

    df = load_data("Expenses")
    if not df.empty:
         st.subheader("📝 اخراجات میں تبدیلی کریں (Edit Expenses)")
         edited_df_e = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="exp_editor", column_config={"Owner": st.column_config.TextColumn(disabled=True), "Date": st.column_config.TextColumn(disabled=True)})
         if st.button("💾 Save Changes", key="save_exp", type="primary"):
             if update_whole_sheet("Expenses", edited_df_e):
                 st.success("✅ خرچہ اپ ڈیٹ ہو گیا!"); time.sleep(1); st.rerun()

# === D. CLOSING (کلوزنگ) ===
elif "کلوزنگ" in menu:
    st.header("📒 ماہانہ رپورٹ (Monthly Financials)")
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    tb = b["Amount"].sum() if not b.empty else 0
    ts = s["Amount"].sum() if not s.empty else 0
    te = e["Amount"].sum() if not e.empty else 0
    profit = ts - tb - te
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h4>Total Purchase</h4><div class='metric-value' style='color:#d32f2f !important'>Rs {tb:,.0f}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h4>Total Sales (Earning)</h4><div class='metric-value' style='color:#1976d2 !important'>Rs {ts:,.0f}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h4>Net Profit (صاف منافع)</h4><div class='metric-value' style='color:#2e7d32 !important'>Rs {profit:,.0f}</div></div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📜 پچھلے مہینوں کا خلاصہ (Past Month Summary)")
    sum_df = load_data("Summary")
    if not sum_df.empty: st.dataframe(sum_df, use_container_width=True)
    else: st.info("No past records found.")

# === E. ADMIN PANEL ===
elif "ایڈمن پینل" in menu:
    st.header("⚙️ ایڈمن کنٹرول پینل")
    st.subheader("🔴 نیا مہینہ شروع کریں (Start New Month)")
    st.warning("⚠️ انتباہ: یہ بٹن دبانے سے خریداری، فروخت اور اخراجات کا تمام موجودہ ڈیٹا آرکائیو (Archive) ہو جائے گا اور نئی شیٹس بالکل خالی ہو جائیں گی۔ یہ کام صرف مہینے کے آخر میں کریں۔")
    
    b = load_data("Purchase"); s = load_data("Sale"); e = load_data("Expenses")
    earn = s["Amount"].sum() if not s.empty else 0
    prof = earn - (b["Amount"].sum() if not b.empty else 0) - (e["Amount"].sum() if not e.empty else 0)
    
    if st.button("⚠️ ڈیٹا آرکائیو کریں اور نیا مہینہ شروع کریں", type="primary"):
        with st.spinner("Processing Monthly Closing..."):
            if reset_month_and_archive(prof, earn):
                st.balloons()
                st.success("✅ مبارک ہو! پچھلا ریکارڈ محفوظ ہو گیا ہے اور نئے مہینے کی شیٹس تیار ہیں۔")
                time.sleep(2)
                st.rerun()

st.divider()
c_f1, c_f2 = st.columns([3,1])
c_f1.caption("© 2026 SI Traders System | Developed for Refined Business Operations.")
if st.button("🚪 Logout", key="footer_logout"): st.session_state.clear(); st.rerun()
