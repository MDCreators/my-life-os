import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #f4f6f9; }
        .metric-card { background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
        .sale-card { border-left: 5px solid #c62828; }
        .invoice-box { background: white; padding: 30px; border: 1px solid #eee; }
        @media print { [data-testid="stSidebar"] { display: none; } .invoice-box { position: absolute; top: 0; left: 0; width: 100%; } }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNECTION (FIXED ID) ---
def get_connection():
    if "service_account" not in st.secrets: st.error("Secrets Missing"); st.stop()
    creds = dict(st.secrets["service_account"])
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").replace('\\', '') if creds["private_key"].startswith('\\') else creds["private_key"].replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds, scopes=scope)
    client = gspread.authorize(creds)
    
    # 🔥 CORRECTED SHEET ID (Case Sensitive)
    # Pichli baar 'n' chota tha, ab 'N' bara hai.
    sheet_id = "1SQUMvySccNWz_G3ziZmiFB9Ry2thjxdnNGWvhppv-dE"
    
    return client.open_by_key(sheet_id)

# --- 3. HELPER FUNCTIONS ---
def get_worksheet_safe(client, tab_name):
    try: return client.worksheet(tab_name)
    except: 
        try: return client.worksheet(tab_name + "s") # Try plural
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
        if not ws: st.error(f"Sheet '{tab}' nahi mili (Check Spelling)."); return False
        
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
        st.title("⚖️ Login")
        u = st.text_input("User"); p = st.text_input("Pass", type="password")
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

tabs = ["🟢 Khareedari", "🔴 Farokht", "📒 Closing"]
if st.session_state["user_role"] == "Admin": tabs.append("👥 Users")
menu = st.radio("Menu", tabs, horizontal=True)
st.divider()

if "invoice_data" not in st.session_state: st.session_state.invoice_data = None

# === KHAREEDARI ===
if "Khareedari" in menu:
    st.header("New Purchase")
    with st.form("buy"):
        c1,c2,c3 = st.columns(3)
        party = c1.text_input("Party")
        w_col, u_col = c2.columns([2,1])
        w = w_col.number_input("Weight", format="%.3f"); unit = u_col.selectbox("Unit", ["Kg", "Grams"])
        r = c3.number_input("Rate")
        det = st.text_input("Details")
        fw = w if unit=="Kg" else w/1000
        total = fw*r
        st.markdown(f"### Total: {total:,.0f}")
        if st.form_submit_button("Save"):
            date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            if save_data("Purchase", [date, party, fw, r, total, det]):
                st.success("Saved!"); time.sleep(1); st.rerun()
    
    st.subheader("History")
    df = load_data("Purchase")
    if not df.empty:
        st.dataframe(df)
        c1,c2 = st.columns(2)
        c1.info(f"Total Weight: {df['Weight'].sum():,.3f}")
        c2.info(f"Total Amount: {df['Amount'].sum():,.0f}")
    else: st.warning("No data found.")

# === FAROKHT ===
elif "Farokht" in menu:
    if st.session_state.invoice_data:
        d = st.session_state.invoice_data
        st.button("Back", on_click=lambda: st.session_state.pop("invoice_data"))
        st.markdown(f"""<div class='invoice-box'><center><h2>SI TRADERS</h2></center><hr><p><b>Bill:</b> {d['bill']} | <b>Customer:</b> {d['cust']}</p><table width='100%'><tr><td><b>Item</b></td><td><b>Weight</b></td><td><b>Rate</b></td><td><b>Total</b></td></tr><tr><td>{d['det']}</td><td>{d['w']}</td><td>{d['r']}</td><td>{d['a']}</td></tr></table></div>""", unsafe_allow_html=True)
    else:
        st.header("New Sale")
        with st.form("sell"):
            c1,c2 = st.columns(2); cust=c1.text_input("Customer"); bill=c2.text_input("Bill No")
            c3,c4 = st.columns(2); w_col, u_col = c3.columns([2,1]); w=w_col.number_input("Weight", format="%.3f"); unit=u_col.selectbox("Unit", ["Kg","Grams"]); r=c4.number_input("Rate")
            det = st.text_input("Details")
            fw = w if unit=="Kg" else w/1000
            total = fw*r
            st.markdown(f"### Bill: {total:,.0f}")
            if st.form_submit_button("Save & Print"):
                date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
                if save_data("Sale", [date, cust, bill, fw, r, total, det]):
                    st.session_state.invoice_data = {"date":date, "cust":cust, "bill":bill, "w":fw, "r":r, "a":f"{total:,.0f}", "det":det}
                    st.rerun()
        st.subheader("History")
        df = load_data("Sale")
        if not df.empty: st.dataframe(df)

# === CLOSING ===
elif "Closing" in menu:
    b=load_data("Purchase"); s=load_data("Sale")
    nw = s["Weight"].sum() - b["Weight"].sum() if not s.empty and not b.empty else 0
    np = s["Amount"].sum() - b["Amount"].sum() if not s.empty and not b.empty else 0
    c1,c2=st.columns(2); c1.metric("Stock", f"{nw:,.3f} Kg"); c2.metric("Profit", f"Rs {np:,.0f}")

elif "Users" in menu:
    u=st.text_input("User"); p=st.text_input("Pass")
    if st.button("Create"): 
        client = get_connection()
        get_worksheet_safe(client, "Users").append_row([u,p]); st.success("Done")
    st.dataframe(get_users())
