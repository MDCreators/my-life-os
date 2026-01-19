import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIG ---
st.set_page_config(page_title="E-Com Pro", page_icon="🚀", layout="wide")

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

# --- 3. PREMIUM UI STYLING (THE MAGIC) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* Background & Fonts */
    .stApp { background-color: #F3F4F6; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #111827; font-weight: 800; letter-spacing: -0.5px; }
    p, div { color: #374151; }
    
    /* Dashboard Cards */
    .kpi-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-left: 6px solid #4F46E5;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .kpi-title { font-size: 14px; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #111827; margin-top: 8px; }
    .kpi-sub { font-size: 12px; color: #10B981; font-weight: 600; margin-top: 4px; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #1F2937; }
    section[data-testid="stSidebar"] h1 { color: white !important; }
    section[data-testid="stSidebar"] span { color: #D1D5DB !important; }
    
    /* Inputs & Buttons */
    .stTextInput>div>div>input { border-radius: 10px; border: 1px solid #E5E7EB; padding: 10px; }
    .stButton>button {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
        color: white; border: none; padding: 0.5rem 1rem;
        border-radius: 10px; font-weight: 600; transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3);
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 6px 10px rgba(79, 70, 229, 0.4); }
    
    /* Table Styling */
    .stDataFrame { border-radius: 12px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- 4. SAAS LOGIN SYSTEM ---
def login_system():
    if "user_session" not in st.session_state:
        st.session_state["user_session"] = None
        st.session_state["is_admin"] = False

    if st.session_state["user_session"]:
        return True

    # Login Screen Design
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; padding: 30px; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#4F46E5;'>🚀 E-Com Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#6B7280;'>Secure Login for Merchants</p>", unsafe_allow_html=True)
        
        email = st.text_input("Email Address", placeholder="name@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.button("✨ Access Dashboard", use_container_width=True):
            # 1. Super Admin
            if email == "admin@owner.com" and password == "boss123":
                st.session_state["user_session"] = "SUPER_ADMIN"
                st.session_state["is_admin"] = True
                st.rerun()
            
            # 2. Clients
            try:
                doc_ref = db.collection("users").document(email)
                doc = doc_ref.get()
                if doc.exists and doc.to_dict().get("password") == password:
                    st.session_state["user_session"] = email
                    st.session_state["is_admin"] = False
                    st.success("Welcome back!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
            except:
                st.error("Login Error")
                
        st.markdown("</div>", unsafe_allow_html=True)
    return False

if not login_system():
    st.stop()

current_owner = st.session_state["user_session"]
is_super_admin = st.session_state["is_admin"]

# --- 5. DATA FUNCTIONS (Optimized) ---
def get_products(owner_id):
    docs = db.collection("products").where("owner", "==", owner_id).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, sku, owner_id):
    db.collection("products").add({
        "name": name, "price": int(price), "cost": int(cost), 
        "stock": int(stock), "sku": sku, "owner": owner_id
    })

def create_order(customer, phone, address, items, subtotal, delivery, ship_cost, pack_cost, total, source, owner_id):
    tz = pytz.timezone('Asia/Karachi')
    net_profit = total - (sum([i['cost']*i['qty'] for i in items]) + ship_cost + pack_cost)
    db.collection("orders").add({
        "date": str(datetime.now(tz)), "customer": customer, "phone": phone, "address": address,
        "items": items, "subtotal": subtotal, "delivery": delivery,
        "ship_cost": ship_cost, "pack_cost": pack_cost, "total": total,
        "net_profit": net_profit, "source": source, "status": "Pending",
        "owner": owner_id, "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_orders(owner_id):
    docs = db.collection("orders").where("owner", "==", owner_id).stream()
    data = [{"id": d.id, **d.to_dict()} for d in docs]
    data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return data

def log_expense(desc, amount, category, owner_id):
    tz = pytz.timezone('Asia/Karachi')
    db.collection("expenses").add({
        "date": str(datetime.now(tz)), "desc": desc, "amount": int(amount),
        "category": category, "owner": owner_id, "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_expenses(owner_id):
    docs = db.collection("expenses").where("owner", "==", owner_id).stream()
    data = [{"id": d.id, **d.to_dict()} for d in docs]
    data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return data

# --- 6. SUPER ADMIN PANEL ---
if is_super_admin:
    st.sidebar.markdown("## 👑 Super Admin")
    if st.sidebar.button("Logout"):
        st.session_state["user_session"] = None
        st.rerun()
        
    st.title("Admin HQ")
    t1, t2 = st.tabs(["Create Client", "All Clients"])
    
    with t1:
        with st.form("new_client"):
            st.subheader("Onboard New Merchant")
            c_email = st.text_input("Merchant Email")
            c_pass = st.text_input("Set Password")
            c_name = st.text_input("Business Name")
            if st.form_submit_button("Create Account"):
                db.collection("users").document(c_email).set({
                    "password": c_pass, "business_name": c_name, "created_at": firestore.SERVER_TIMESTAMP
                })
                st.success(f"Merchant {c_name} Created!")
    
    with t2:
        users = db.collection("users").stream()
        for u in users:
            d = u.to_dict()
            st.info(f"🏢 {d.get('business_name')} | 📧 {u.id}")
    st.stop()

# --- 7. MERCHANT DASHBOARD (PREMIUM UI) ---
with st.sidebar:
    st.markdown(f"## 🛍️ {current_owner.split('@')[0].capitalize()}")
    st.caption("Pro Dashboard")
    st.write("---")
    menu = st.radio("Navigate", ["📊 Overview", "📝 New Order", "🚚 Orders", "📦 Inventory", "💸 Expenses"])
    st.write("---")
    if st.button("Logout"):
        st.session_state["user_session"] = None
        st.rerun()

# === DASHBOARD ===
if menu == "📊 Overview":
    st.markdown("## Business Pulse ⚡")
    orders = get_orders(current_owner)
    expenses = get_expenses(current_owner)
    
    total_sales = sum([o['total'] for o in orders if o['status'] != 'Cancelled'])
    total_profit = 0
    return_loss = 0
    for o in orders:
        if o['status'] == 'Returned': return_loss += (o.get('ship_cost', 0) + o.get('pack_cost', 0))
        elif o['status'] != 'Cancelled': total_profit += o.get('net_profit', 0)
    total_profit -= return_loss
    total_exp = sum([e['amount'] for e in expenses])
    net_net = total_profit - total_exp
    
    # Custom HTML Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Revenue</div><div class='kpi-value'>Rs {total_sales:,}</div><div class='kpi-sub'>Lifetime Sales</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Gross Profit</div><div class='kpi-value' style='color:#10B981;'>Rs {total_profit:,}</div><div class='kpi-sub'>Before Expenses</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Op. Expenses</div><div class='kpi-value' style='color:#EF4444;'>Rs {total_exp:,}</div><div class='kpi-sub'>Ads & Rent</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Profit</div><div class='kpi-value' style='color:#6366F1;'>Rs {net_net:,}</div><div class='kpi-sub'>Take Home</div></div>", unsafe_allow_html=True)

# === NEW ORDER ===
elif menu == "📝 New Order":
    st.markdown("## 🛒 Create Order")
    products = get_products(current_owner)
    p_names = [p['name'] for p in products if p['stock'] > 0]
    
    c_left, c_right = st.columns([1, 1])
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with c_left:
        with st.container():
            st.markdown("### 📦 Select Items")
            sel_p = st.selectbox("Product", ["Select..."] + p_names)
            if sel_p != "Select...":
                p_obj = next(p for p in products if p['name'] == sel_p)
                qty = st.number_input("Quantity", 1, 100, 1)
                if st.button("Add to Cart"):
                    st.session_state.cart.append({"name": sel_p, "qty": qty, "price": p_obj['price'], "cost": p_obj['cost'], "id": p_obj['id']})
            
            if st.session_state.cart:
                st.markdown("---")
                st.write("**Current Cart:**")
                st.dataframe(pd.DataFrame(st.session_state.cart))
                if st.button("Clear Cart", type="secondary"): st.session_state.cart = []

    with c_right:
        with st.container():
            st.markdown("### 👤 Customer Details")
            with st.form("checkout"):
                cust = st.text_input("Full Name")
                phone = st.text_input("Phone Number")
                addr = st.text_area("Shipping Address")
                src = st.selectbox("Source", ["WhatsApp", "Instagram", "Facebook", "Website"])
                
                st.markdown("---")
                subt = sum([i['price']*i['qty'] for i in st.session_state.cart])
                c1, c2, c3 = st.columns(3)
                dlv = c1.number_input("Delivery Charge", value=200)
                ship = c2.number_input("Courier Cost", value=180)
                pack = c3.number_input("Packing Cost", value=15)
                
                if st.form_submit_button("🚀 Place Order"):
                    if st.session_state.cart and cust:
                        create_order(cust, phone, addr, st.session_state.cart, subt, dlv, ship, pack, subt+dlv, src, current_owner)
                        st.session_state.cart = []
                        st.success("Order Successfully Placed!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Cart is empty or details missing")

# === ORDERS ===
elif menu == "🚚 Orders":
    st.markdown("## 📦 Order Manager")
    orders = get_orders(current_owner)
    if not orders: st.info("No orders found.")
    
    for o in orders:
        status_color = "#F59E0B" # Pending (Orange)
        if o['status'] == 'Shipped': status_color = "#3B82F6" # Blue
        if o['status'] == 'Delivered': status_color = "#10B981" # Green
        if o['status'] == 'Returned': status_color = "#EF4444" # Red
        
        with st.expander(f"{o.get('date','')} | {o.get('customer','Unknown')} | Rs {o['total']}", expanded=False):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**Items:** {[i['name'] + ' x' + str(i['qty']) for i in o['items']]}")
                st.caption(f"Address: {o.get('address')} | Phone: {o.get('phone')}")
            with c2:
                st.markdown(f"<div style='background:{status_color}; color:white; padding:5px; border-radius:5px; text-align:center;'>{o['status']}</div>", unsafe_allow_html=True)
                new_stat = st.selectbox("Update Status", ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], key=o['id'])
                if new_stat != o['status']:
                    db.collection("orders").document(o['id']).update({"status": new_stat})
                    st.rerun()

# === INVENTORY ===
elif menu == "📦 Inventory":
    st.markdown("## 🏭 Inventory")
    with st.expander("➕ Add New Product"):
        with st.form("new_prod"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Product Name")
            sku = c2.text_input("SKU Code")
            price = c1.number_input("Sale Price", min_value=1)
            cost = c2.number_input("Cost Price", min_value=1)
            stock = st.number_input("Stock Qty", min_value=1)
            if st.form_submit_button("Save Product"):
                add_product(name, price, cost, stock, sku, current_owner)
                st.success("Added!")
                st.rerun()
    st.dataframe(pd.DataFrame(get_products(current_owner)), use_container_width=True)

# === EXPENSES ===
elif menu == "💸 Expenses":
    st.markdown("## 📉 Expense Tracker")
    with st.form("add_exp"):
        c1, c2, c3 = st.columns([2, 1, 1])
        desc = c1.text_input("Description")
        amt = c2.number_input("Amount", min_value=1)
        cat = c3.selectbox("Category", ["Ads", "Rent", "Salary", "Utility", "Other"])
        if st.form_submit_button("Log Expense"):
            log_expense(desc, amt, cat, current_owner)
            st.success("Saved!")
            st.rerun()
    st.dataframe(pd.DataFrame(get_expenses(current_owner)), use_container_width=True)
