import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Business Manager", layout="wide")

# --- GOOGLE SHEET CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- HELPER FUNCTIONS ---
def get_data(worksheet):
    try:
        df = conn.read(worksheet=worksheet, ttl=0)
        return df
    except:
        return pd.DataFrame()

def update_data(worksheet, df):
    conn.update(worksheet=worksheet, data=df)

# --- 1. LOGIN SYSTEM ---
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
            # Admin Hardcoded (Safety k liye)
            if user == "admin" and pwd == "admin123":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "admin"
                st.session_state["role"] = "admin"
                st.session_state["shop_name"] = "Super Admin"
                st.success("Welcome Admin!")
                st.rerun()
            
            # Check Users from Google Sheet
            df_users = get_data("Users")
            if not df_users.empty:
                # Find user
                match = df_users[(df_users["Username"] == user) & (df_users["Password"] == pwd)]
                if not match.empty:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user
                    st.session_state["role"] = "user"
                    st.session_state["shop_name"] = match.iloc[0]["Shop Name"]
                    st.success(f"Welcome to {match.iloc[0]['Shop Name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")
            else:
                st.error("❌ User Database Empty or Not Connected")

    st.stop()  # Stop app here if not logged in

# --- 2. SIDEBAR & LOGOUT ---
owner_id = st.session_state["username"] # Current User
shop_title = st.session_state["shop_name"]

st.sidebar.title(f"🏪 {shop_title}")
st.sidebar.caption(f"Logged in as: {owner_id}")

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# --- 3. MENU ---
if st.session_state["role"] == "admin":
    menu = st.sidebar.radio("Admin Menu", ["🛠️ Create New Shop/User", "👀 View All Data"])
else:
    menu = st.sidebar.radio("Menu", ["🛒 New Bill", "📦 Inventory", "👥 Customers", "💸 Expenses", "🏦 Bank/Cash"])

st.title(f"{shop_title} Dashboard")

# ==========================
# ADMIN PANEL (Create Users)
# ==========================
if st.session_state["role"] == "admin":
    if menu == "🛠️ Create New Shop/User":
        st.header("🛠️ Create New Client Account")
        with st.form("new_user"):
            new_user = st.text_input("New Username (e.g. shop1)")
            new_pass = st.text_input("New Password")
            new_shop = st.text_input("Shop Name (e.g. Bismillah General Store)")
            if st.form_submit_button("Create User"):
                df_users = get_data("Users")
                # Check duplicate
                if not df_users.empty and new_user in df_users["Username"].values:
                    st.error("Username already exists!")
                else:
                    new_row = pd.DataFrame([{"Username": new_user, "Password": new_pass, "Shop Name": new_shop}])
                    update_data("Users", pd.concat([df_users, new_row], ignore_index=True))
                    st.success(f"User '{new_user}' Created Successfully!")

    elif menu == "👀 View All Data":
        st.write("Admin can see Master Data here...")
        st.dataframe(get_data("Users"))

# ==========================
# USER PANEL (Shopkeeper)
# ==========================
else:
    # --- AUTO FILTER FUNCTION (Magic Logic) ---
    # Yeh function sirf wohi data laye ga jo 'Owner' column mai match karay ga
    def get_my_data(sheet_name):
        df = get_data(sheet_name)
        if not df.empty and "Owner" in df.columns:
            return df[df["Owner"] == owner_id]
        return pd.DataFrame()

    # ==========================
    # A. INVENTORY
    # ==========================
    if menu == "📦 Inventory":
        st.header("📦 My Stock")
        df_stock = get_my_data("Inventory")
        st.dataframe(df_stock.drop(columns=["Owner"], errors="ignore"), use_container_width=True)

        with st.expander("Add New Item"):
            with st.form("add_item"):
                name = st.text_input("Item Name")
                qty = st.number_input("Quantity", 0)
                price = st.number_input("Price", 0)
                unit = st.selectbox("Unit", ["Pkt", "Kg", "Ctn", "Pcs"])
                if st.form_submit_button("Add Stock"):
                    # Load FULL data first to append
                    df_full = get_data("Inventory")
                    new_row = pd.DataFrame([{
                        "Owner": owner_id,  # <--- Important: Tagging owner
                        "Item Name": name, 
                        "Quantity": qty, 
                        "Price": price,
                        "Unit": unit
                    }])
                    update_data("Inventory", pd.concat([df_full, new_row], ignore_index=True))
                    st.success("Item Added!")
                    st.rerun()

    # ==========================
    # B. BILLING
    # ==========================
    elif menu == "🛒 New Bill":
        st.header("🧾 New Sale")
        df_stock = get_my_data("Inventory")
        
        with st.form("bill_form"):
            c1, c2 = st.columns(2)
            cust = c1.text_input("Customer Name")
            date = c2.date_input("Date", datetime.today())
            
            # Select only MY items
            items_list = df_stock["Item Name"].tolist() if not df_stock.empty else []
            item = st.selectbox("Select Item", items_list)
            qty = st.number_input("Quantity", 1)
            
            price = 0
            if item and not df_stock.empty:
                row = df_stock[df_stock["Item Name"] == item]
                if not row.empty:
                    price = row.iloc[0]["Price"] * qty
                    st.info(f"Total: {price}")
            
            paid = st.number_input("Paid Amount", 0)
            if st.form_submit_button("Save Bill"):
                udhaar = price - paid
                df_sales_full = get_data("Sales")
                new_sale = pd.DataFrame([{
                    "Owner": owner_id,
                    "Date": str(date), "Customer": cust, "Item": item, 
                    "Qty": qty, "Total": price, "Paid": paid, "Udhaar": udhaar
                }])
                update_data("Sales", pd.concat([df_sales_full, new_sale], ignore_index=True))
                st.success("Bill Saved!")

    # ==========================
    # C. CUSTOMERS
    # ==========================
    elif menu == "👥 Customers":
        st.header("👥 My Customers")
        df_sales = get_my_data("Sales")
        if not df_sales.empty:
            # Calculate Udhaar for this shop only
            khata = df_sales.groupby("Customer")[["Total", "Paid", "Udhaar"]].sum().reset_index()
            st.dataframe(khata, use_container_width=True)
        else:
            st.info("No sales yet.")

    # ==========================
    # D. EXPENSES & BANK
    # ==========================
    elif menu == "💸 Expenses":
        st.header("💸 My Expenses")
        df_exp = get_my_data("Expenses")
        st.dataframe(df_exp.drop(columns=["Owner"], errors="ignore"), use_container_width=True)
        with st.form("exp"):
            desc = st.text_input("Description")
            amt = st.number_input("Amount", 0)
            if st.form_submit_button("Add"):
                df_full = get_data("Expenses")
                new_row = pd.DataFrame([{"Owner": owner_id, "Date": str(datetime.now().date()), "Description": desc, "Amount": amt}])
                update_data("Expenses", pd.concat([df_full, new_row], ignore_index=True))
                st.success("Added")
                st.rerun()

    elif menu == "🏦 Bank/Cash":
        st.header("🏦 Bank & Cash")
        df_bank = get_my_data("Bank")
        st.dataframe(df_bank.drop(columns=["Owner"], errors="ignore"), use_container_width=True)
        # Add form logic similarly...
