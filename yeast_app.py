import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. PAGE CONFIG (Sab se pehlay) ---
st.set_page_config(page_title="Yeast Shop Manager", layout="wide")

# --- 2. AUTHENTICATION (Login System) ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["role"] = None

    if not st.session_state["logged_in"]:
        st.header("🔒 Login Required")
        
        # Login Form
        col1, col2 = st.columns([1, 2])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            btn = st.button("Login")

        if btn:
            # --- USER LIST (Yahan naye users add kar saktay hain) ---
            users = {
                "admin": "admin123",  # Malik (Full Access)
                "staff": "staff123",  # Worker (Limited Access)
            }

            if username in users and users[username] == password:
                st.session_state["logged_in"] = True
                # Role assign karein (Admin ya Staff)
                st.session_state["role"] = "admin" if username == "admin" else "staff"
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("❌ Wrong Username or Password")
        return False
    return True

# Agar login nahi hai to yahi rook do
if not check_login():
    st.stop()

# --- 3. LOGOUT BUTTON & ROLE ---
st.sidebar.info(f"👤 Logged in as: {st.session_state['role'].upper()}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# --- 4. GOOGLE SHEET CONNECTION ---
# Secrets wahi puranay walay use hon ge
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet):
    try:
        return conn.read(worksheet=worksheet, ttl=0)
    except:
        return pd.DataFrame() # Agar sheet khali ho to error na aye

def update_data(worksheet, df):
    conn.update(worksheet=worksheet, data=df)

# --- 5. MENU SELECTION (Based on Role) ---
st.title("🍞 Dry Yeast Business System")

if st.session_state["role"] == "admin":
    # Admin ko sab nazar aye ga
    menu = st.sidebar.radio("Menu", ["🛒 New Bill", "📦 Inventory", "👥 Customers", "💸 Expenses", "🏦 Bank/Cash", "🛠️ Admin Users"])
else:
    # Staff ko sirf Billing nazar aye gi
    menu = st.sidebar.radio("Menu", ["🛒 New Bill", "👥 Customers"])

# ==========================
# A. INVENTORY (STOCK)
# ==========================
if menu == "📦 Inventory":
    st.header("📦 Stock Management")
    df = get_data("Inventory")
    st.dataframe(df, use_container_width=True)

    with st.expander("Add New Stock"):
        with st.form("stock_form"):
            name = st.text_input("Item Name")
            qty = st.number_input("Quantity", 0)
            price = st.number_input("Price Per Unit", 0)
            if st.form_submit_button("Add Item"):
                new_row = pd.DataFrame([{"Item Name": name, "Quantity": qty, "Price": price}])
                update_data("Inventory", pd.concat([df, new_row], ignore_index=True))
                st.success("Added!")
                st.rerun()

# ==========================
# B. NEW BILL (SALES)
# ==========================
elif menu == "🛒 New Bill":
    st.header("🧾 Create Invoice")
    df_stock = get_data("Inventory")
    
    with st.form("bill_form"):
        c1, c2 = st.columns(2)
        cust_name = c1.text_input("Customer Name")
        date = c2.date_input("Date", datetime.now())
        
        # Item Select
        items_list = df_stock["Item Name"].tolist() if not df_stock.empty else []
        item = st.selectbox("Select Item", items_list)
        qty = st.number_input("Quantity", 1)
        
        # Price Auto-Fetch
        price = 0
        if item and not df_stock.empty:
            row = df_stock[df_stock["Item Name"] == item]
            if not row.empty:
                unit_price = row.iloc[0]["Price"]
                price = unit_price * qty
                st.info(f"💰 Total Amount: Rs {price}")

        paid = st.number_input("Paid Amount", 0)
        
        if st.form_submit_button("Save Bill"):
            udhaar = price - paid
            df_sales = get_data("Sales")
            new_sale = pd.DataFrame([{
                "Date": str(date), "Customer": cust_name, "Item": item, 
                "Qty": qty, "Total": price, "Paid": paid, "Udhaar": udhaar
            }])
            update_data("Sales", pd.concat([df_sales, new_sale], ignore_index=True))
            
            # Simple Stock Minus Logic (Optional for now)
            st.success("Bill Saved Successfully!")

# ==========================
# C. CUSTOMERS (KHATA)
# ==========================
elif menu == "👥 Customers":
    st.header("👥 Customer Udhaar List")
    # Yahan hum Sales data se customer ka total udhaar nikal saktay hain
    df_sales = get_data("Sales")
    if not df_sales.empty:
        # Group by Customer and sum Udhaar
        khata = df_sales.groupby("Customer")[["Total", "Paid", "Udhaar"]].sum().reset_index()
        st.dataframe(khata, use_container_width=True)
    else:
        st.info("No sales data yet.")

# ==========================
# D. EXPENSES & BANK (Admin Only)
# ==========================
elif menu == "💸 Expenses":
    st.header("💸 Daily Expenses")
    df_exp = get_data("Expenses")
    st.dataframe(df_exp, use_container_width=True)
    
    with st.form("exp_form"):
        desc = st.text_input("Expense Name")
        amt = st.number_input("Amount", 0)
        if st.form_submit_button("Add Expense"):
            new_row = pd.DataFrame([{"Date": str(datetime.now().date()), "Description": desc, "Amount": amt}])
            update_data("Expenses", pd.concat([df_exp, new_row], ignore_index=True))
            st.success("Saved!")
            st.rerun()

elif menu == "🏦 Bank/Cash":
    st.header("🏦 Cash Flow")
    df_bank = get_data("Bank")
    st.dataframe(df_bank, use_container_width=True)
    # Simple form same as above...
    
# ==========================
# E. ADMIN USERS
# ==========================
elif menu == "🛠️ Admin Users":
    st.header("🔑 Manage Access")
    st.write("Current Users (Code based):")
    st.code("Admin: admin\nStaff: staff")
    st.warning("To add more users, edit the 'users' list in the code.")
