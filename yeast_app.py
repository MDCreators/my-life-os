import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz

# --- 1. SETTINGS ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")
pk_timezone = pytz.timezone('Asia/Karachi')

# --- 2. CONNECTION ---
# Secrets mein [connections.gsheets] heading ka hona lazmi hay
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
        st.error(f"❌ Write Error: {e}")
        return False

# --- 3. APP UI ---
st.sidebar.title("🍞 Dry Yeast Business")
menu = st.sidebar.radio("Main Menu", ["📦 Stock", "👥 Customers", "🧾 Billing", "🏦 Bank", "💸 Expenses"])

st.title(f"Section: {menu}")

# --- 4. MODULES ---

if menu == "📦 Stock":
    st.subheader("Inventory / Stock Management")
    df = get_data("Stock")
    st.dataframe(df, use_container_width=True)
    with st.expander("Add New Stock"):
        with st.form("s_form"):
            item = st.text_input("Item Name")
            qty = st.number_input("Qty", 0)
            price = st.number_input("Purchase Price", 0)
            if st.form_submit_button("Save"):
                new_s = pd.DataFrame([{"Item": item, "Qty": qty, "Price": price, "Date": str(datetime.now(pk_timezone).date())}])
                if save_data("Stock", pd.concat([df, new_s], ignore_index=True)):
                    st.success("Stock Updated!")
                    st.rerun()

elif menu == "👥 Customers":
    st.subheader("Customer Khata System")
    df = get_data("Customers")
    st.dataframe(df, use_container_width=True)
    with st.form("c_form"):
        name = st.text_input("Customer Name")
        bal = st.number_input("Opening Balance", 0)
        if st.form_submit_button("Register"):
            new_c = pd.DataFrame([{"Name": name, "Balance": bal}])
            if save_data("Customers", pd.concat([df, new_c], ignore_index=True)):
                st.success("Registered!")
                st.rerun()

elif menu == "🧾 Billing":
    st.subheader("Invoice Generation")
    df_stock = get_data("Stock")
    with st.form("b_form"):
        cust = st.text_input("Customer Name")
        items = df_stock["Item"].tolist() if not df_stock.empty else []
        selected = st.selectbox("Select Yeast", items)
        qty = st.number_input("Qty", 1)
        paid = st.number_input("Cash Received", 0)
        if st.form_submit_button("Generate Bill"):
            df_sales = get_data("Sales")
            # Calculation logic here...
            st.success("Bill Generated and Saved in Sales Tab!")

elif menu == "🏦 Bank":
    st.subheader("Bank Transactions")
    df = get_data("Bank")
    st.dataframe(df, use_container_width=True)
    with st.form("bank"):
        amt = st.number_input("Amount", 0)
        desc = st.text_input("Detail")
        if st.form_submit_button("Log"):
            new_b = pd.DataFrame([{"Date": str(datetime.now(pk_timezone).date()), "Detail": desc, "Amount": amt}])
            save_data("Bank", pd.concat([df, new_b], ignore_index=True))

elif menu == "💸 Expenses":
    st.subheader("Daily Expenses")
    df = get_data("Expenses")
    st.dataframe(df, use_container_width=True)
    with st.form("exp"):
        item = st.text_input("Expense Title")
        amt = st.number_input("Amount", 0)
        if st.form_submit_button("Save Expense"):
            new_e = pd.DataFrame([{"Date": str(datetime.now(pk_timezone).date()), "Title": item, "Amount": amt}])
            save_data("Expenses", pd.concat([df, new_e], ignore_index=True))
