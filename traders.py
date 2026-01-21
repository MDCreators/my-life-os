import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials
import time

# --- CONFIG ---
st.set_page_config(page_title="SI Traders", page_icon="⚖️", layout="wide")
st.markdown("""<style>.metric-card {background:white; padding:15px; border-radius:10px; border-left:5px solid #2e7d32; box-shadow:2px 2px 5px rgba(0,0,0,0.1); text-align:center;} .sale-card {border-left:5px solid #c62828;} .stApp {background-color:#f4f6f9;}</style>""", unsafe_allow_html=True)

# --- CONNECTION ---
def get_connection():
    if "service_account" not in st.secrets:
        st.error("🚨 Secrets file mein key nahi mili.")
        st.stop()
    creds = dict(st.secrets["service_account"])
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").replace('\\', '') if creds["private_key"].startswith('\\') else creds["private_key"].replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return gspread.authorize(Credentials.from_service_account_info(creds, scopes=scope)).open("SI Traders Data")

# --- LOAD DATA (NO ERROR HIDING) ---
def load_data(tab):
    try:
        ws = get_connection().worksheet(tab)
        data = ws.get_all_values() # Raw data uthao
        
        if not data: return pd.DataFrame() # Agar sheet bilkul khali hay
        
        headers = data.pop(0) # Pehli line headers hain
        df = pd.DataFrame(data, columns=headers)
        
        # Admin Filter
        if "Owner" in df.columns and st.session_state.get("user_role") != "Admin":
            df = df[df["Owner"] == st.session_state["username"]]
            
        # Convert Numbers
        for col in ["Weight", "Rate", "Amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}") # Error chupaana nahi hay
        return pd.DataFrame()

# --- SAVE DATA ---
def save_data(tab, row_data):
    try:
        ws = get_connection().worksheet(tab)
        ws.append_row([st.session_state["username"]] + row_data)
        return True
    except Exception as e:
        st.error(f"Save Failed: {e}")
        return False

# --- LOGIN ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "username": "", "user_role": ""})

if not st.session_state["logged_in"]:
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        st.title("⚖️ Login")
        u = st.text_input("User"); p = st.text_input("Pass", type="password")
        if st.button("Login"):
            if u=="admin" and p=="admin123":
                st.session_state.update({"logged_in":True, "username":"Admin", "user_role":"Admin"}); st.rerun()
            try:
                users_df = load_data("Users") # Sheet se users uthao
                if not users_df.empty:
                    match = users_df[(users_df["Username"]==u) & (users_df["Password"]==p)]
                    if not match.empty:
                        st.session_state.update({"logged_in":True, "username":u, "user_role":"User"}); st.rerun()
                    else: st.error("Wrong Password")
                else: st.error("No Users Found")
            except: st.error("Login Error")
    st.stop()

# --- MAIN APP ---
st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("Logout"): st.session_state.update({"logged_in":False}); st.rerun()

tabs = ["🟢 Khareedari", "🔴 Farokht", "📒 Closing"]
if st.session_state["user_role"] == "Admin": tabs.append("👥 Users")
menu = st.radio("Menu", tabs, horizontal=True)
st.divider()

if "Khareedari" in menu:
    st.subheader("New Purchase")
    c1,c2,c3 = st.columns(3)
    party = c1.text_input("Party")
    w = c2.number_input("Weight (Kg)", format="%.3f")
    r = c3.number_input("Rate")
    if st.button("Save Purchase"):
        date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
        if save_data("Purchase", [date, party, w, r, w*r, ""]):
            st.success("Saved!"); time.sleep(1); st.rerun()
            
    st.subheader("History")
    df = load_data("Purchase")
    if not df.empty:
        st.dataframe(df)
        st.info(f"Total Weight: {df['Weight'].sum():,.3f} | Total Amount: {df['Amount'].sum():,.0f}")
    else:
        st.warning("Sheet is Empty or Data Load Failed.")

elif "Farokht" in menu:
    st.subheader("New Sale")
    c1,c2 = st.columns(2)
    cust = c1.text_input("Customer"); bill = c2.text_input("Bill No")
    c3,c4 = st.columns(2)
    w = c3.number_input("Weight (Kg)", format="%.3f"); r = c4.number_input("Rate")
    if st.button("Save Sale"):
        date = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
        if save_data("Sale", [date, cust, bill, w, r, w*r, ""]):
            st.success("Saved!"); time.sleep(1); st.rerun()
            
    st.subheader("History")
    df = load_data("Sale")
    if not df.empty: st.dataframe(df)

elif "Closing" in menu:
    b = load_data("Purchase"); s = load_data("Sale")
    net_w = s["Weight"].sum() - b["Weight"].sum() if not s.empty and not b.empty else 0
    net_p = s["Amount"].sum() - b["Amount"].sum() if not s.empty and not b.empty else 0
    c1,c2 = st.columns(2)
    c1.metric("Stock", f"{net_w} Kg"); c2.metric("Profit", f"Rs {net_p}")

elif "Users" in menu:
    u = st.text_input("New User"); p = st.text_input("New Pass")
    if st.button("Create"):
        get_connection().worksheet("Users").append_row([u,p]); st.success("Created!")
    st.dataframe(load_data("Users"))
