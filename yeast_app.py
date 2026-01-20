import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Business Manager", layout="wide")

# 🚨 APNI GOOGLE SHEET KA LINK NEECHAY HAI
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qzkhlZvw7x1QOX9yCiUfS7h1M2_7UfxAb6tzr5dgExk/edit"

# --- 2. CONNECTION ---
# Yeh connection aap k Secrets se keys uthaye ga
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # Har dafa fresh data uthanay k liye ttl=0 rakha hay
        return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    except Exception as e:
        return pd.DataFrame()

def update_data(worksheet_name, df):
    try:
        # Spreadsheet ka URL dena lazmi hay taake permission error na aye
        conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"❌ Error: {e}")
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
            # MASTER ADMIN (Aap k liye)
            if user == "admin" and pwd == "admin123":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "admin"
                st.session_state["role"] = "admin"
                st.session_state["shop_name"] = "Super Admin"
                st.rerun()
            
            # SHOP USERS (Google Sheet se login check)
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
                    st.error("❌ Ghalat Username ya Password")
            else:
                st.error("❌ Users list khaali hay. Pehlay Admin se login kar k User banayen.")
    st.stop()

# --- 4. DASHBOARD SETUP ---
owner_id = st.session_state["username"]
shop_title = st.session_state["shop_name"]

st.sidebar.title(f"🏪 {shop_title}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# --- 5. MENU SELECTION ---
if st.session_state["role"] == "admin":
    menu = st.sidebar.radio("Admin Menu", ["🛠️ Create New Shop", "👀 View All Users"])
else:
    menu = st.sidebar.radio("Main Menu", ["🛒 New Bill", "📦 Inventory", "👥 Customers", "💸 Expenses", "🏦 Bank/Cash"])

st.title(f"{shop_title} Dashboard")

# ==========================
# ADMIN PANEL LOGIC
# ==========================
if st.session_state["role"] == "admin":
    if menu == "🛠️ Create New Shop":
        st.subheader("Nayi Shop ka Account Banayen")
        with st.form("admin_user_form"):
            new_u = st.text_input("Username (e.g. shop1)")
            new_p = st.text_input("Password")
            new_s = st.text_input("Shop Name (e.g. Bismillah Store)")
            if st.form_submit_button("Account Create Karein"):
                df_u = get_data("Users")
                new_row = pd.DataFrame([{"Username": new_u, "Password": new_p, "Shop Name": new_s}])
                if update_data("Users", pd.concat([df_u, new_row], ignore_index=True)):
                    st.success(f"✅ User '{new_u}' ban gaya hay!")

    elif menu == "👀 View All Users":
        st.subheader("Mojooda Users")
        st.dataframe(get_data("Users"), use_container_width=True)

# ==========================
# SHOP USER LOGIC
# ==========================
else:
    def get_my_data(tab):
        df = get_data(tab)
        if not df.empty and "Owner" in df.columns:
            return df[df["Owner"] == owner_id]
        return pd.DataFrame()

    # --- A. INVENTORY ---
    if menu == "📦 Inventory":
        st.subheader("📦 Mera Stock")
        df_stock = get_my_data("Inventory")
        st.dataframe(df_stock.drop(columns=["Owner"], errors="ignore"), use_container_width=True)
        
        with st.expander("Naya Item Add Karein"):
            with st.form("stock_form"):
                name = st.text_input("Item Name")
                qty = st.number_input("Quantity", 0)
                price = st.number_input("Price Per Unit", 0)
                unit = st.selectbox("Unit", ["Pkt", "Kg", "Ctn", "Pcs"])
                if st.form_submit_button("Save Item"):
                    df_full = get_data("Inventory")
                    new_row = pd.DataFrame([{"Owner": owner_id, "Item Name": name, "Quantity": qty, "Price": price, "Unit": unit}])
                    if update_data("Inventory", pd.concat([df_full, new_row], ignore_index=True)):
                        st.success("Item Saved!")
                        st.rerun()

    # --- B. BILLING ---
    elif menu == "🛒 New Bill":
        st.subheader("🧾 Naya Bill Banayen")
        df_stock = get_my_data("Inventory")
        
        with st.form("billing_form"):
            c1, c2 = st.columns(2)
            cust = c1.text_input("Customer Name")
            date = c2.date_input("Date", datetime.today())
            
            items = df_stock["Item Name"].tolist() if not df_stock.empty else []
            item_select = st.selectbox("Select Item", items)
            qty = st.number_input("Quantity", 1)
            
            total_bill = 0
            if item_select and not df_stock.empty:
                unit_p = df_stock[df_stock["Item Name"] == item_select]["Price"].values[0]
                total_bill = unit_p * qty
                st.info(f"💰 Total Bill: Rs {total_bill}")
            
            paid = st.number_input("Paid Amount", 0)
            if st.form_submit_button("Generate Bill"):
                df_s = get_data("Sales")
                new_s = pd.DataFrame([{
                    "Owner": owner_id, "Date": str(date), "Customer": cust, 
                    "Item": item_select, "Qty": qty, "Total": total_bill, 
                    "Paid": paid, "Udhaar": total_bill - paid
                }])
                if update_data("Sales", pd.concat([df_s, new_s], ignore_index=True)):
                    st.success("✅ Sale Saved!")

    # --- C. CUSTOMERS ---
    elif menu == "👥 Customers":
        st.subheader("👥 Khata / Customers")
        df_s = get_my_data("Sales")
        if not df_s.empty:
            khata = df_s.groupby("Customer")[["Total", "Paid", "Udhaar"]].sum().reset_index()
            st.dataframe(khata, use_container_width=True)
        else:
            st.info("Abhi koi sales nahi hain.")

    # --- D. EXPENSES ---
    elif menu == "💸 Expenses":
        st.subheader("💸 Rozana ke Kharchay")
        df_e = get_my_data("Expenses")
        st.dataframe(df_e.drop(columns=["Owner"], errors="ignore"), use_container_width=True)
        with st.form("exp_form"):
            desc = st.text_input("Detail")
            amt = st.number_input("Amount", 0)
            if st.form_submit_button("Add Expense"):
                df_f = get_data("Expenses")
                new_r = pd.DataFrame([{"Owner": owner_id, "Date": str(datetime.now().date()), "Description": desc, "Amount": amt}])
                if update_data("Expenses", pd.concat([df_f, new_r], ignore_index=True)):
                    st.success("Added!")
                    st.rerun()
