import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Business Manager", layout="wide")

# 🚨 APNI GOOGLE SHEET KA LINK NEECHAY HAI
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qzkhlZvw7x1QOX9yCiUfS7h1M2_7UfxAb6tzr5dgExk/edit"

# --- 2. CONNECTION SETUP ---
# Hum explicitly 'gsheets' connection ko Secrets se link kar rahay hain
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # Spreadsheet aur Worksheet dono ka batana zaroori hai
        return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    except Exception as e:
        return pd.DataFrame()

def update_data(worksheet_name, df):
    try:
        # 'spreadsheet' link pass karna lazmi hai warna 'Public Spreadsheet' error ata hai
        conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return False

# --- 3. LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["shop_name"] = None
    st.session_state["role"] = None

if not st.session_state["logged_in"]:
    st.title("🔐 Secure Login")
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        btn = st.form_submit_button("Login")
        
        if btn:
            # MASTER ADMIN
            if user == "admin" and pwd == "admin123":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "admin"
                st.session_state["role"] = "admin"
                st.session_state["shop_name"] = "Super Admin"
                st.rerun()
            
            # SHOP USERS
            df_users = get_data("Users")
            if not df_users.empty:
                match = df_users[(df_users["Username"] == user) & (df_users["Password"] == pwd)]
                if not match.empty:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user
                    st.session_state["role"] = "user"
                    st.session_state["shop_name"] = match.iloc[0]["Shop Name"]
                    st.rerun()
                else:
                    st.error("❌ Username ya Password ghalat hai")
            else:
                st.error("❌ Users list khaali hai")
    st.stop()

# --- 4. DASHBOARD ---
owner_id = st.session_state["username"]
shop_title = st.session_state["shop_name"]
st.sidebar.title(f"🏪 {shop_title}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if st.session_state["role"] == "admin":
    menu = st.sidebar.radio("Admin Menu", ["🛠️ Create New Shop", "👀 View All Users"])
else:
    menu = st.sidebar.radio("Menu", ["🛒 New Bill", "📦 Inventory", "👥 Customers", "💸 Expenses", "🏦 Bank/Cash"])

st.title(f"{shop_title} Dashboard")

# --- ADMIN FUNCTIONS ---
if st.session_state["role"] == "admin":
    if menu == "🛠️ Create New Shop":
        st.subheader("Naya Shop Account")
        with st.form("add_user"):
            u = st.text_input("Username")
            p = st.text_input("Password")
            s = st.text_input("Shop Name")
            if st.form_submit_button("Create Account"):
                df = get_data("Users")
                new_row = pd.DataFrame([{"Username": u, "Password": p, "Shop Name": s}])
                if update_data("Users", pd.concat([df, new_row], ignore_index=True)):
                    st.success("✅ Account Created!")

# --- USER FUNCTIONS ---
else:
    def get_my_data(tab):
        df = get_data(tab)
        if not df.empty and "Owner" in df.columns:
            return df[df["Owner"] == owner_id]
        return pd.DataFrame()

    if menu == "📦 Inventory":
        st.subheader("Stock Management")
        df_stock = get_my_data("Inventory")
        st.dataframe(df_stock.drop(columns=["Owner"], errors="ignore"), use_container_width=True)
        with st.form("stock"):
            name = st.text_input("Item")
            qty = st.number_input("Qty", 0)
            price = st.number_input("Price", 0)
            if st.form_submit_button("Save"):
                full = get_data("Inventory")
                new = pd.DataFrame([{"Owner": owner_id, "Item Name": name, "Quantity": qty, "Price": price, "Unit": "Pcs"}])
                if update_data("Inventory", pd.concat([full, new], ignore_index=True)):
                    st.success("Saved!")
                    st.rerun()
    
    elif menu == "🛒 New Bill":
        st.subheader("Billing")
        # Logic same as before...
