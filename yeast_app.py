import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz

# --- 1. SETTINGS & TIMEZONE ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_timezone = pytz.timezone('Asia/Karachi') #

# --- 2. LOGIN SECURITY ---
# Aap ki di hui credentials
TARGET_EMAIL = "saeedjanarman3@gmail.com"
TARGET_PASS = "saeedjanarman3221"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Yeast Business Portal")
    with st.form("login"):
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if e == TARGET_EMAIL and p == TARGET_PASS:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Ghalat Email ya Password!")
    st.stop()

# --- 3. CONNECTION ---
# Yeh line Secrets se [connections.gsheets] uthaye gi
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(tab):
    try:
        return conn.read(worksheet=tab, ttl=0)
    except Exception:
        return pd.DataFrame()

def save_data(tab, df):
    try:
        conn.update(worksheet=tab, data=df)
        return True
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return False

# --- 4. NAVIGATION ---
st.sidebar.title("🍞 Business Menu")
menu = st.sidebar.radio("Go to:", ["📦 Stock", "👥 Customers", "🧾 Billing", "🏦 Bank", "💸 Expenses"])
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

st.title(f"Section: {menu}")

# --- 5. FEATURES LOGIC ---

# STOCK MANAGEMENT
# Code mein jahan bhi "Stock" likha tha, usay "Inventory" kar dein
if menu == "📦 Stock":
    df = get_data("Inventory") # Sheet ke mutabiq name update
    st.dataframe(df, use_container_width=True)
    with st.expander("Update Inventory"):
        with st.form("stock"):
            item = st.text_input("Item Name")
            qty = st.number_input("Qty", 0)
            pr = st.number_input("Price", 0)
            if st.form_submit_button("Save Stock"):
                new = pd.DataFrame([{"Item": item, "Qty": qty, "Price": pr, "Date": str(datetime.now(pk_timezone).date())}])
                if save_data("Stock", pd.concat([df, new], ignore_index=True)):
                    st.success("Stock Updated!"); st.rerun()

# CUSTOMER KHATA
elif menu == "👥 Customers":
    df = get_data("Customers")
    st.dataframe(df, use_container_width=True)
    with st.form("cust"):
        n = st.text_input("Customer Name")
        b = st.number_input("Opening Balance", 0)
        if st.form_submit_button("Add Customer"):
            new = pd.DataFrame([{"Name": n, "Balance": b}])
            if save_data("Customers", pd.concat([df, new], ignore_index=True)):
                st.success("Saved!"); st.rerun()

# BILLING (SALES)
elif menu == "🧾 Billing":
    df_stock = get_data("Stock")
    with st.form("bill"):
        c_name = st.text_input("Customer Name")
        items_list = df_stock["Item"].tolist() if not df_stock.empty else []
        sel = st.selectbox("Select Yeast", items_list)
        q = st.number_input("Quantity", 1)
        paid = st.number_input("Cash Received", 0)
        if st.form_submit_button("Create Bill"):
            df_sales = get_data("Sales")
            price = df_stock[df_stock["Item"] == sel]["Price"].values[0] if not df_stock.empty else 0
            total = price * q
            new_sale = pd.DataFrame([{
                "Date": str(datetime.now(pk_timezone).date()), "Customer": c_name, 
                "Item": sel, "Total": total, "Paid": paid, "Balance": total - paid
            }])
            if save_data("Sales", pd.concat([df_sales, new_sale], ignore_index=True)):
                st.success(f"Bill Saved! Total: {total}")

# BANK TRANSACTIONS
elif menu == "🏦 Bank":
    df = get_data("Bank")
    st.dataframe(df, use_container_width=True)
    with st.form("bank"):
        desc = st.text_input("Detail")
        amt = st.number_input("Amount", 0)
        if st.form_submit_button("Log Entry"):
            new = pd.DataFrame([{"Date": str(datetime.now(pk_timezone).date()), "Detail": desc, "Amount": amt}])
            if save_data("Bank", pd.concat([df, new], ignore_index=True)):
                st.success("Logged!"); st.rerun()

# EXPENSES
elif menu == "💸 Expenses":
    df = get_data("Expenses")
    st.dataframe(df, use_container_width=True)
    with st.form("exp"):
        title = st.text_input("Expense Title")
        amt = st.number_input("Amount", 0)
        if st.form_submit_button("Add Expense"):
            new = pd.DataFrame([{"Date": str(datetime.now(pk_timezone).date()), "Title": title, "Amount": amt}])
            if save_data("Expenses", pd.concat([df, new], ignore_index=True)):
                st.success("Recorded!"); st.rerun()
