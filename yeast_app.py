import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz

# --- SETTINGS ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("l"):
        u = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "saeedjanarman3@gmail.com" and p == "saeedjanarman3221":
                st.session_state["auth"] = True; st.rerun()
            else: st.error("Ghalat credentials!")
    st.stop()

# --- CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(t): return conn.read(worksheet=t, ttl=0)
def save_data(t, d): return conn.update(worksheet=t, data=d)

# --- MENU ---
st.sidebar.title("🍞 Menu")
m = st.sidebar.radio("Go to:", ["📦 Stock", "🧾 Billing", "💸 Expenses"])

if m == "📦 Stock":
    st.subheader("Inventory Stock")
    # Sheet ke tab 'Inventory' se data uthayen ge
    df = get_data("Inventory")
    st.dataframe(df, use_container_width=True)
    with st.form("s"):
        item = st.text_input("Item Name")
        q = st.number_input("Qty", 0)
        if st.form_submit_button("Save Stock"):
            new = pd.DataFrame([{"Username": item, "Password": str(q), "Shop Name": "Stock Update"}])
            if save_data("Users", pd.concat([get_data("Users"), new], ignore_index=True)):
                st.success("Saved!"); st.rerun()

elif m == "💸 Expenses":
    st.subheader("Expenses")
    df = get_data("Expenses")
    st.dataframe(df, use_container_width=True)
    with st.form("e"):
        t = st.text_input("Expense Title")
        a = st.number_input("Amount", 0)
        if st.form_submit_button("Add Expense"):
            new = pd.DataFrame([{"Date": str(datetime.now(pk_tz).date()), "Title": t, "Amount": a}])
            if save_data("Expenses", pd.concat([df, new], ignore_index=True)):
                st.success("Recorded!"); st.rerun()
