import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")
st.markdown("""<style>.stApp { background-color: #f4f6f9; } .metric-card {background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center;} .sale-card { border-left: 5px solid #c62828; } .metric-value { font-size: 24px; font-weight: bold; } </style>""", unsafe_allow_html=True)

# --- 2. CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets:
        st.error("🚨 Error: Secrets file check karein.")
        st.stop()
    creds_dict = dict(st.secrets["service_account"])
    if "private_key" in creds_dict:
        if creds_dict["private_key"].startswith("\\"): creds_dict["private_key"] = creds_dict["private_key"][1:]
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("SI Traders Data")

# --- 3. HELPER FUNCTIONS (DEBUG MODE) ---
def get_users():
    try:
        ws = get_connection().worksheet("Users")
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

def load_data(tab):
    try:
        ws = get_connection().worksheet(tab)
        # Use get_all_values for safety
        raw = ws.get_all_values()
        if not raw: return pd.DataFrame()
        
        headers = raw.pop(0)
        df = pd.DataFrame(raw, columns=headers)
        
        # --- DEBUGGER: Agar data hay magar show nahi ho raha ---
        # Agar 'Owner' column nahi mila, tu shayed headers ghalat hain
        if "Owner" not in df.columns:
            st.warning(f"⚠️ Sheet '{tab}' mein 'Owner' column nahi mila! (Columns: {headers})")
            return df # Phir bhi dikha do
        
        # Filter Logic
        if st.session_state["user_role"] != "Admin":
            df = df[df["Owner"] == st.session_state["username"]]
            
        # Convert Numbers
        cols = ["Weight", "Amount", "Rate"]
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Load Error: {e}")
        return pd.DataFrame()

def save_data(tab, row_data):
    try:
        ws = get_connection().worksheet(tab)
        full_row = [st.session_state["username"]] + row_data
        ws.append_row(full_row)
        return True
    except Exception as e:
        if "200" in str(e): return True
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
                    st.session_state["logged_in"] = True; st.session_state["username"] = "Admin"; st.session_state["user_role"] = "Admin"; st.rerun()
                users = get_users()
                if not users.empty:
                    match = users[(users["Username"].astype(str) == u) & (users["Password"].astype(str) == p)]
                    if not match.empty:
                        st.session_state["logged_in"] = True; st.session_state["username"] = u; st.session_state["user_role"] = "User"; st.rerun()
                    else: st.error("Wrong ID/Pass")
                else: st.error("User List Empty")
    st.stop()

# --- 5. MAIN APP ---
st.sidebar.markdown(f"### 👤 {st.session_state['username']}")
if st.sidebar.button("Logout"): st.session_state["logged_in"] = False; st.rerun()

st.title("⚖️ SI Traders System")
tabs = ["🟢 Khareedari (Purchase)", "🔴 Farokht (Sale)", "📒 Closing (Profit)"]
if st.session_state["user_role"] == "Admin": tabs.append("👥 Users")
active_tab = st.radio("Menu", tabs, horizontal=True, label_visibility="collapsed")
st.markdown("---")

if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === A. KHAREEDARI ===
if "Khareedari" in active_tab:
    st.header("🟢 Nayi Khareedari")
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
        st.markdown(f"### 💰 Total: Rs {total_amt:,.0f} ({final_weight_kg} Kg)")
        if st.form_submit_button("📥 Save Purchase"):
            pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %H:%M")
            if save_data("Purchase", [pk_time, party, final_weight_kg, rate, total_amt, details]):
                st.success("Saved!"); time.sleep(1); st.rerun()

    st.subheader("📜 History")
    df = load_data("Purchase")
    if not df.empty:
        st.dataframe(df, use_container_width=True) # Full data dikhao
        t_w = df["Weight"].sum() if "Weight" in df.columns else 0
        t_a = df["Amount"].sum() if "Amount" in df.columns else 0
        c1, c2 = st.columns(2)
        c1.info(f"Total Wazan: {t_w:,.3f} Kg")
        c2.info(f"Total Raqam: Rs {t_a:,.0f}")
    else:
        st.info("No data found in Sheet.")
        # Debug helper
        if st.button("🔍 Check Sheet Connection"):
            try:
                ws = get_connection().worksheet("Purchase")
                st.write("Raw Sheet Data:", ws.get_all_values())
            except Exception as e: st.error(f"Connection Error: {e}")

# === B. FAROKHT ===
elif "Farokht" in active_tab:
    if st.session_state.invoice_data:
        data = st.session_state.invoice_data
        st.button("🔙 Back", on_click=lambda: st.session_state.pop("invoice_data"))
        st.markdown(f"""<div style="padding:20px; border:1px solid #ddd; background:white; color:black;">
        <h2 style="text-align:center">SI TRADERS</h2><hr>
        <p><b>Bill:</b> {data['bill']} | <b>Date:</b> {data['date']}</p>
        <p><b>Customer:</b> {data['cust']}</p>
        <table style="width:100%; text-align:left;"><tr><th>Item</th><th>Qty</th><th>Rate</th><th>Amt</th></tr>
        <tr><td>{data['details']}</td><td>{data['weight']}</td><td>{data['rate']}</td><td>{data['amount']}</td></tr></table>
        <h3 style="text-align:right">Total: Rs {data['amount']}</h3></div>""", unsafe_allow_html=True)
    else:
        st.header("🔴 Nayi Farokht")
        with st.form("sell_form"):
            c1, c2 = st.columns(2)
            cust = c1.text_input("Customer Name"); bill = c2.text_input("Bill No")
            c3, c4 = st.columns(2)
            w_col, u_col = c3.columns([2,1])
            raw_weight = w_col.number_input("Wazan", min_value=0.0, format="%.3f")
            unit = u_col.selectbox("Unit", ["Kg", "Grams"])
            rate = c4.number_input("Rate", min_value=0)
            details = st.text_input("Details")
            final_weight_kg = raw_weight if unit == "Kg" else raw_weight / 1000
            total_amt = final_weight_kg * rate
            st.markdown(f"### 💰 Bill: Rs {total_amt:,.0f}")
            if st.form_submit_button("🖨️ Save & Print"):
                pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %H:%M")
                if save_data("Sale", [pk_time, cust, bill, final_weight_kg, rate, total_amt, details]):
                    st.session_state.invoice_data = {"date":pk_time, "cust":cust, "bill":bill, "weight":final_weight_kg, "rate":rate, "amount":f"{total_amt:,.0f}", "details":details}
                    st.rerun()
        
        st.subheader("📜 History")
        df = load_data("Sale")
        if not df.empty: st.dataframe(df, use_container_width=True)

# === C. CLOSING ===
elif "Closing" in active_tab:
    st.header("📒 Closing")
    df_b = load_data("Purchase"); df_s = load_data("Sale")
    b_w = df_b["Weight"].sum() if not df_b.empty and "Weight" in df_b.columns else 0
    b_a = df_b["Amount"].sum() if not df_b.empty and "Amount" in df_b.columns else 0
    s_w = df_s["Weight"].sum() if not df_s.empty and "Weight" in df_s.columns else 0
    s_a = df_s["Amount"].sum() if not df_s.empty and "Amount" in df_s.columns else 0
    net_w = s_w - b_w; net_p = s_a - b_a
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock", f"{net_w:,.3f} Kg"); c2.metric("Profit", f"Rs {net_p:,.0f}"); c3.metric("Avg Rate", f"{(net_p/net_w):.1f}" if net_w!=0 else "0")

elif "Users" in active_tab:
    with st.form("add_u"):
        u = st.text_input("User"); p = st.text_input("Pass")
        if st.form_submit_button("Add"):
            try: get_connection().worksheet("Users").append_row([u, p]); st.success("Added!")
            except: st.success("Added (Cached)")
    st.dataframe(get_users(), use_container_width=True)
