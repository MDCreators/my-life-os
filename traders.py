import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

# CSS for Print & Styling
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp { background-color: #f4f6f9; }
        
        /* Metric Cards */
        .metric-card {
            background-color: white; padding: 15px; border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center;
            border-left: 5px solid #2e7d32;
        }
        .sale-card { border-left: 5px solid #c62828; }
        .metric-title { font-size: 14px; color: #555; }
        .metric-value { font-size: 24px; font-weight: bold; color: #000; }
        
        /* Print Styles - Sirf Invoice Print Hoga */
        @media print {
            body * { visibility: hidden; }
            .invoice-box, .invoice-box * { visibility: visible; }
            .invoice-box { position: absolute; left: 0; top: 0; width: 100%; }
            [data-testid="stSidebar"] { display: none; }
        }
        
        .invoice-box {
            max-width: 800px; margin: auto; padding: 30px; border: 1px solid #eee;
            box-shadow: 0 0 10px rgba(0, 0, 0, .15); font-size: 16px;
            line-height: 24px; font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
            color: #555; background-color: white;
        }
        .invoice-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .invoice-title { font-size: 32px; font-weight: bold; color: #333; }
        .invoice-details { text-align: right; }
        .invoice-table { width: 100%; line-height: inherit; text-align: left; border-collapse: collapse; }
        .invoice-table td { padding: 5px; vertical-align: top; }
        .invoice-table tr.heading td { background: #eee; border-bottom: 1px solid #ddd; font-weight: bold; }
        .invoice-table tr.item td { border-bottom: 1px solid #eee; }
        .invoice-table tr.total td { border-top: 2px solid #eee; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets:
        st.error("🚨 Error: Secrets file check karein.")
        st.stop()
    
    creds_dict = dict(st.secrets["service_account"])
    # Key Cleaning
    if "private_key" in creds_dict:
        if creds_dict["private_key"].startswith("\\"):
            creds_dict["private_key"] = creds_dict["private_key"][1:]
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("SI Traders Data")

# --- 3. HELPER FUNCTIONS ---
def get_users():
    try: return pd.DataFrame(get_connection().worksheet("Users").get_all_records())
    except: return pd.DataFrame()

def load_data(tab):
    try:
        ws = get_connection().worksheet(tab)
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty and "Owner" in df.columns:
            if st.session_state["user_role"] != "Admin":
                df = df[df["Owner"] == st.session_state["username"]]
        return df
    except: return pd.DataFrame()

def save_data(tab, row_data):
    try:
        ws = get_connection().worksheet(tab)
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        if "200" in str(e): return True # Ignore fake error
        st.error(f"Save Error: {e}")
        return False

# --- 4. LOGIN SYSTEM ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = "User"

if not st.session_state["logged_in"]:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("## ⚖️ SI Traders Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if u == "admin" and p == "admin123":
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = "Admin"
                    st.session_state["user_role"] = "Admin"
                    st.rerun()
                
                users = get_users()
                if not users.empty:
                    match = users[(users["Username"].astype(str) == u) & (users["Password"].astype(str) == p)]
                    if not match.empty:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = u
                        st.session_state["user_role"] = "User"
                        st.rerun()
                    else: st.error("Wrong ID/Pass")
                else: st.error("User list empty")
    st.stop()

# --- 5. MAIN APP ---
st.sidebar.markdown(f"### 👤 {st.session_state['username']}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

st.title("⚖️ SI Traders System")
tabs = ["🟢 Khareedari (Purchase)", "🔴 Farokht (Sale)", "📒 Closing (Profit)"]
if st.session_state["user_role"] == "Admin": tabs.append("👥 Manage Users")

active_tab = st.radio("Menu", tabs, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# Session State for Invoice
if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === A. KHAREEDARI ===
if "Khareedari" in active_tab:
    st.header("🟢 Nayi Khareedari")
    
    # Input Form
    with st.form("buy_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        party = c1.text_input("Party Name")
        w_col, u_col = c2.columns([2,1])
        raw_weight = w_col.number_input("Wazan", min_value=0.0, format="%.3f")
        unit = u_col.selectbox("Unit", ["Kg", "Grams"])
        rate = c3.number_input("Rate (Per Kg)", min_value=0)
        details = st.text_input("Tafseel")
        
        final_weight_kg = raw_weight if unit == "Kg" else raw_weight / 1000
        total_amt = final_weight_kg * rate
        st.markdown(f"### 💰 Total: Rs {total_amt:,.0f} <span style='font-size:14px; color:grey'>({final_weight_kg} Kg)</span>", unsafe_allow_html=True)
        
        if st.form_submit_button("📥 Save Purchase"):
            pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %H:%M")
            if save_data("Purchase", [pk_time, party, final_weight_kg, rate, total_amt, details]):
                st.success("Saved Successfully!")
                time.sleep(1) # Thora wait karein
                st.rerun()

    # History Table (Ab data nazar aye ga)
    st.subheader("📜 Aaj ki Khareedari (History)")
    df = load_data("Purchase")
    if not df.empty:
        # Show last 5 records
        st.dataframe(df.tail(10), use_container_width=True)
        t_w = df["Weight"].sum()
        t_a = df["Amount"].sum()
        c1, c2 = st.columns(2)
        c1.info(f"Total Wazan: {t_w:,.3f} Kg")
        c2.info(f"Total Raqam: Rs {t_a:,.0f}")

# === B. FAROKHT (INVOICE PRINTING) ===
elif "Farokht" in active_tab:
    # Agar Invoice Bani hui hai, tu woh dikhao
    if st.session_state.invoice_data:
        data = st.session_state.invoice_data
        st.button("🔙 Back to Form", on_click=lambda: st.session_state.pop("invoice_data"))
        
        # HTML Invoice Template
        inv_html = f"""
        <div class="invoice-box">
            <div class="invoice-header">
                <div class="invoice-title">SI TRADERS</div>
                <div class="invoice-details">
                    Bill No: {data['bill']}<br>
                    Date: {data['date']}<br>
                    Customer: {data['cust']}
                </div>
            </div>
            <hr>
            <table class="invoice-table">
                <tr class="heading"><td>Item / Details</td><td>Weight (Kg)</td><td>Rate</td><td>Amount</td></tr>
                <tr class="item"><td>{data['details']}</td><td>{data['weight']}</td><td>{data['rate']}</td><td>{data['amount']}</td></tr>
                <tr class="total"><td></td><td></td><td>Total:</td><td>Rs {data['amount']}</td></tr>
            </table>
            <br><br>
            <center><i>Thank you for your business!</i></center>
        </div>
        """
        st.markdown(inv_html, unsafe_allow_html=True)
        st.info("💡 Invoice print karnay ke liye keyboard par **Ctrl + P** dabayen.")
    
    else:
        st.header("🔴 Nayi Farokht (Sale)")
        with st.form("sell_form"):
            c1, c2 = st.columns(2)
            cust = c1.text_input("Customer Name")
            bill = c2.text_input("Bill No")
            
            c3, c4 = st.columns(2)
            w_col, u_col = c3.columns([2,1])
            raw_weight = w_col.number_input("Wazan", min_value=0.0, format="%.3f")
            unit = u_col.selectbox("Unit", ["Kg", "Grams"])
            rate = c4.number_input("Rate (Per Kg)", min_value=0)
            details = st.text_input("Details (Optional)")
            
            final_weight_kg = raw_weight if unit == "Kg" else raw_weight / 1000
            total_amt = final_weight_kg * rate
            st.markdown(f"### 💰 Bill: Rs {total_amt:,.0f}", unsafe_allow_html=True)
            
            if st.form_submit_button("🖨️ Save & Print Invoice"):
                pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %H:%M")
                if save_data("Sale", [pk_time, cust, bill, final_weight_kg, rate, total_amt, details]):
                    # Store data for invoice view
                    st.session_state.invoice_data = {
                        "date": pk_time, "cust": cust, "bill": bill,
                        "weight": final_weight_kg, "rate": rate,
                        "amount": f"{total_amt:,.0f}", "details": details or "General Item"
                    }
                    st.rerun()

        # History
        st.subheader("📜 Aaj ki Farokht")
        df = load_data("Sale")
        if not df.empty:
            st.dataframe(df.tail(10), use_container_width=True)

# === C. CLOSING ===
elif "Closing" in active_tab:
    st.header("📒 Profit / Loss Report")
    df_b = load_data("Purchase")
    df_s = load_data("Sale")
    
    b_w = df_b["Weight"].sum() if not df_b.empty and "Weight" in df_b.columns else 0
    b_a = df_b["Amount"].sum() if not df_b.empty and "Amount" in df_b.columns else 0
    s_w = df_s["Weight"].sum() if not df_s.empty and "Weight" in df_s.columns else 0
    s_a = df_s["Amount"].sum() if not df_s.empty and "Amount" in df_s.columns else 0
    
    net_w = s_w - b_w
    net_p = s_a - b_a
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock in Hand", f"{net_w:,.3f} Kg")
    c2.metric("Net Profit", f"Rs {net_p:,.0f}")
    c3.metric("Avg Rate", f"{(net_p/net_w):.1f}" if net_w!=0 else "0")

# === D. USERS ===
elif "Manage Users" in active_tab:
    st.header("👥 User Management")
    with st.form("add_u"):
        u = st.text_input("New Username")
        p = st.text_input("New Password")
        if st.form_submit_button("Create User"):
            try:
                ws = get_connection().worksheet("Users")
                ws.append_row([u, p])
                st.success("User Created!")
            except: st.success("User Created (Cached)")
    st.dataframe(get_users(), use_container_width=True)
