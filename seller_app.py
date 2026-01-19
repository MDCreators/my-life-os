import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIG ---
st.set_page_config(page_title="E-Com Pro (SaaS)", page_icon="🚀", layout="wide")

# --- 2. FIREBASE CONNECTION ---
if not firebase_admin._apps:
    try:
        key_content = st.secrets["firebase"]["my_key"]
        key_dict = json.loads(key_content)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}")
        st.stop()

db = firestore.client()

# --- 3. SAAS LOGIN SYSTEM ---
def login_system():
    if "user_session" not in st.session_state:
        st.session_state["user_session"] = None
        st.session_state["is_admin"] = False

    if st.session_state["user_session"]:
        return True

    st.markdown("<h1 style='text-align:center; color:#3E64FF;'>🚀 Merchant Login</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                # 1. Check Super Admin (You)
                if email == "admin@owner.com" and password == "boss123":
                    st.session_state["user_session"] = "SUPER_ADMIN"
                    st.session_state["is_admin"] = True
                    st.rerun()
                
                # 2. Check Clients (Dukandaar)
                doc_ref = db.collection("users").document(email)
                doc = doc_ref.get()
                if doc.exists:
                    user_data = doc.to_dict()
                    if user_data.get("password") == password:
                        st.session_state["user_session"] = email # Owner ID
                        st.session_state["is_admin"] = False
                        st.success("Login Successful!")
                        st.rerun()
                    else:
                        st.error("Password Ghalat hai.")
                else:
                    st.error("Account nahi mila. Please contact Support.")
    return False

if not login_system():
    st.stop()

current_owner = st.session_state["user_session"]
is_super_admin = st.session_state["is_admin"]

# --- 4. DATA FUNCTIONS (FILTERED BY OWNER) ---
def get_products(owner_id):
    # Sirf us owner ka data layen
    docs = db.collection("products").where("owner", "==", owner_id).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, sku, owner_id):
    db.collection("products").add({
        "name": name, "price": int(price), "cost": int(cost), 
        "stock": int(stock), "sku": sku,
        "owner": owner_id  # Tagging data with owner
    })

def create_order(customer, phone, address, items, subtotal, delivery, ship_cost, pack_cost, total, source, owner_id):
    tz = pytz.timezone('Asia/Karachi')
    net_profit = total - (sum([i['cost']*i['qty'] for i in items]) + ship_cost + pack_cost)
    
    db.collection("orders").add({
        "date": str(datetime.now(tz)),
        "customer": customer, "phone": phone, "address": address,
        "items": items, "subtotal": subtotal, "delivery": delivery,
        "ship_cost": ship_cost, "pack_cost": pack_cost, "total": total,
        "net_profit": net_profit, "source": source, "status": "Pending",
        "owner": owner_id, # Tagging
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_orders(owner_id):
    docs = db.collection("orders").where("owner", "==", owner_id).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def log_expense(desc, amount, category, owner_id):
    tz = pytz.timezone('Asia/Karachi')
    db.collection("expenses").add({
        "date": str(datetime.now(tz)), "desc": desc, "amount": int(amount),
        "category": category, "owner": owner_id,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_expenses(owner_id):
    docs = db.collection("expenses").where("owner", "==", owner_id).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# --- 5. SUPER ADMIN PANEL (ONLY FOR YOU) ---
if is_super_admin:
    st.sidebar.title("👑 Boss Menu")
    if st.sidebar.button("Logout"):
        st.session_state["user_session"] = None
        st.rerun()
        
    st.title("Software Management Panel")
    st.info("Yahan se aap naye Clients (Dukandaar) add karein.")
    
    with st.form("new_client"):
        st.subheader("Add New Client")
        c_email = st.text_input("Client Email")
        c_pass = st.text_input("Assign Password")
        c_name = st.text_input("Business Name")
        
        if st.form_submit_button("Create Account"):
            db.collection("users").document(c_email).set({
                "password": c_pass,
                "business_name": c_name,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Client {c_name} created! Email: {c_email}")
    
    st.divider()
    st.write("### Active Clients")
    users = db.collection("users").stream()
    for u in users:
        d = u.to_dict()
        st.text(f"🏢 {d.get('business_name', 'Unknown')} | 📧 {u.id}")
        
    st.stop() # Admin yahin ruk jaye

# --- 6. CLIENT DASHBOARD (DUKANDAARON KE LIYE) ---
# Ye hissa 50 alag alag logon ko unka apna data dikhaye ga

with st.sidebar:
    st.title("🚀 E-Com Dashboard")
    st.caption(f"ID: {current_owner}")
    menu = st.radio("Menu", ["📊 Dashboard", "📝 New Order", "🚚 Order Manager", "📦 Inventory", "💸 Expenses"])
    st.write("---")
    if st.button("Logout"):
        st.session_state["user_session"] = None
        st.rerun()

# === DASHBOARD ===
if menu == "📊 Dashboard":
    st.subheader("Business Overview")
    orders = get_orders(current_owner)
    expenses = get_expenses(current_owner)
    
    total_sales = sum([o['total'] for o in orders if o['status'] != 'Cancelled'])
    total_profit = sum([o.get('net_profit',0) for o in orders if o['status'] not in ['Returned', 'Cancelled']])
    
    # Return Loss Logic
    return_loss = sum([o.get('ship_cost',0) + o.get('pack_cost',0) for o in orders if o['status'] == 'Returned'])
    total_profit -= return_loss # Deduct loss
    
    total_exp = sum([e['amount'] for e in expenses])
    net_net = total_profit - total_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales", f"Rs {total_sales:,}")
    c2.metric("Gross Profit", f"Rs {total_profit:,}")
    c3.metric("Expenses", f"Rs {total_exp:,}")
    c4.metric("Net Profit", f"Rs {net_net:,}", delta_color="normal")

# === NEW ORDER ===
elif menu == "📝 New Order":
    st.subheader("Create New Order")
    products = get_products(current_owner)
    p_names = [p['name'] for p in products if p['stock'] > 0]
    
    col1, col2 = st.columns(2)
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with col1:
        sel_p = st.selectbox("Product", ["Select..."] + p_names)
        if sel_p != "Select...":
            p_obj = next(p for p in products if p['name'] == sel_p)
            qty = st.number_input("Qty", 1, 100, 1)
            if st.button("Add to Cart"):
                st.session_state.cart.append({"name": sel_p, "qty": qty, "price": p_obj['price'], "cost": p_obj['cost'], "id": p_obj['id']})
        
        if st.session_state.cart:
            st.dataframe(pd.DataFrame(st.session_state.cart))
            if st.button("Clear"): st.session_state.cart = []

    with col2:
        with st.form("checkout"):
            cust = st.text_input("Customer Name")
            phone = st.text_input("Phone")
            addr = st.text_input("Address")
            src = st.selectbox("Source", ["WhatsApp", "Insta", "Web"])
            
            subt = sum([i['price']*i['qty'] for i in st.session_state.cart])
            dlv = st.number_input("Delivery Charge (from Cust)", value=200)
            ship = st.number_input("Actual Courier Cost", value=180)
            pack = st.number_input("Packing Cost", value=15)
            
            if st.form_submit_button("Place Order"):
                if st.session_state.cart and cust:
                    create_order(cust, phone, addr, st.session_state.cart, subt, dlv, ship, pack, subt+dlv, src, current_owner)
                    st.session_state.cart = []
                    st.success("Order Placed!")
                    time.sleep(1)
                    st.rerun()

# === ORDER MANAGER ===
elif menu == "🚚 Order Manager":
    st.subheader("Manage Orders")
    orders = get_orders(current_owner)
    for o in orders:
        with st.expander(f"{o['date']} - {o['customer']} ({o['status']})"):
            st.write(o['items'])
            new_stat = st.selectbox("Status", ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], key=o['id'])
            if new_stat != o['status']:
                db.collection("orders").document(o['id']).update({"status": new_stat})
                st.rerun()

# === INVENTORY ===
elif menu == "📦 Inventory":
    st.subheader("My Inventory")
    with st.form("new_prod"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        sku = c2.text_input("SKU")
        price = c1.number_input("Sale Price", min_value=1)
        cost = c2.number_input("Cost Price", min_value=1)
        stock = st.number_input("Stock", min_value=1)
        if st.form_submit_button("Add Product"):
            add_product(name, price, cost, stock, sku, current_owner)
            st.success("Added!")
            st.rerun()
            
    st.dataframe(pd.DataFrame(get_products(current_owner)))

# === EXPENSES ===
elif menu == "💸 Expenses":
    st.subheader("Expense Tracker")
    with st.form("add_exp"):
        desc = st.text_input("Description")
        amt = st.number_input("Amount", min_value=1)
        cat = st.selectbox("Category", ["Ads", "Rent", "Salary", "Other"])
        if st.form_submit_button("Add"):
            log_expense(desc, amt, cat, current_owner)
            st.success("Saved!")
            st.rerun()
    st.dataframe(pd.DataFrame(get_expenses(current_owner)))
