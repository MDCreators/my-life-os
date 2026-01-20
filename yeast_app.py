import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Dry Yeast Business Manager", layout="wide")
pk_tz = pytz.timezone('Asia/Karachi')

# --- 2. LOGIN SECURITY ---
TARGET_EMAIL = "saeedjanarman3@gmail.com"
TARGET_PASS = "saeedjanarman3221"

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Secure Login")
    with st.form("login_form"):
        e = st.text_input("Email Address")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if e == TARGET_EMAIL and p == TARGET_PASS:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Ghalat Email ya Password!")
    st.stop()

# --- 3. CONNECTION ---
# Yeh connection Secrets se [connections.gsheets] uthaye ga
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(tab_name):
    try:
        # Cache khatam karnay ke liye ttl=0 lazmi hay
        return conn.read(worksheet=tab_name, ttl=0)
    except Exception as e:
        st.error(f"Read Error ({tab_name}): {e}")
        return pd.DataFrame()

def save_data(tab_name, df):
    try:
        conn.update(worksheet=tab_name, data=df)
        return True
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return False

# --- 4. NAVIGATION ---
st.sidebar.title("🍞 Business Menu")
menu = st.sidebar.radio("Go to:", ["📦 Stock", "👥 Customers", "🧾 Billing", "🏦 Bank", "💸 Expenses"])
if st.sidebar.button("Logout"):
    st.session_state["auth"] = False
    st.rerun()

st.title(f"Section: {menu}")

# --- 5. ALL FEATURES LOGIC ---

# A. STOCK (Inventory Tab)
if menu == "📦 Stock":
    df = get_data("Inventory") #
    st.dataframe(df, use_container_width=True)
    with st.expander("Update Inventory"):
        with st.form("stock_form"):
            item = st.text_input("Item Name")
            qty = st.number_input("Quantity", 0)
            price = st.number_input("Unit Price", 0)
            if st.form_submit_button("Save Stock"):
                new = pd.DataFrame([{"Username": item, "Password": str(qty), "Shop Name": f"Price: {price}"}])
                # Agar aap ne columns badlay hain to yahan match karein
                if save_data("Inventory", pd.concat([df, new], ignore_index=True)):
                    st.success("Stock Updated!"); st.rerun()

# B. CUSTOMERS
elif menu == "👥 Customers":
    df = get_data("Customers") #
    st.dataframe(df, use_container_width=True)
    with st.form("cust"):
        n = st.text_input("Customer Name")
        b = st.number_input("Opening Balance", 0)
        if st.form_submit_button("Add Customer"):
            new = pd.DataFrame([{"Username": n, "Password": str(b), "Shop Name": "Customer"}])
            if save_data("Customers", pd.concat([df, new], ignore_index=True)):
                st.success("Saved!"); st.rerun()

# C. BILLING (Sales Tab)
elif menu == "🧾 Billing":
    st.subheader("Generate Sale Invoice")
    with st.form("bill"):
        c_name = st.text_input("Customer Name")
        amt = st.number_input("Total Amount", 0)
        paid = st.number_input("Cash Received", 0)
        if st.form_submit_button("Create Bill"):
            df_sales = get_data("Sales") #
            new = pd.DataFrame([{"Username": c_name, "Password": str(amt), "Shop Name": f"Paid: {paid}"}])
            if save_data("Sales", pd.concat([df_sales, new], ignore_index=True)):
                st.success("Bill Recorded!")

# D. BANK
elif menu == "🏦 Bank":
    df = get_data("Bank") #
    st.dataframe(df, use_container_width=True)
    with st.form("bank"):
        det = st.text_input("Transaction Detail")
        amt = st.number_input("Amount", 0)
        if st.form_submit_button("Log Transaction"):
            new = pd.DataFrame([{"Username": det, "Password": str(amt), "Shop Name": "Bank Entry"}])
            if save_data("Bank", pd.concat([df, new], ignore_index=True)):
                st.success("Logged!"); st.rerun()

# E. EXPENSES
elif menu == "💸 Expenses":
    df = get_data("Expenses") #
    st.dataframe(df, use_container_width=True)
    with st.form("exp"):
        t = st.text_input("Expense Title")
        a = st.number_input("Amount", 0)
        if st.form_submit_button("Add Expense"):
            new = pd.DataFrame([{"Username": t, "Password": str(a), "Shop Name": "Expense"}])
            if save_data("Expenses", pd.concat([df, new], ignore_index=True)):
                st.success("Recorded!"); st.rerun()
