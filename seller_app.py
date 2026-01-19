import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM ---
def check_password():
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            st.session_state["logged_in_user"] = st.session_state["username"]
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align:center; color:#3E64FF;'>📦 E-Com Manager</h1>", unsafe_allow_html=True)
        st.text_input("Admin ID", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Admin ID", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("🔒 Access Denied")
        return False
    else:
        return True

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="E-Com Dashboard", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

if not check_password():
    st.stop()

current_user = st.session_state["logged_in_user"]

# --- 2. FIREBASE CONNECTION ---
if not firebase_admin._apps:
    try:
        key_content = st.secrets["firebase"]["my_key"]
        key_dict = json.loads(key_content)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"🚨 DB Error: {e}")
        st.stop()

db = firestore.client()

# --- 3. DATABASE FUNCTIONS (ECOMMERCE LOGIC) ---
def get_products():
    docs = db.collection("products").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, sku):
    db.collection("products").add({
        "name": name, "price": int(price), "cost": int(cost), 
        "stock": int(stock), "sku": sku
    })

def create_order(customer_name, phone, address, items, subtotal, delivery_fee, total, source, status="Pending"):
    tz = pytz.timezone('Asia/Karachi')
    # Calculate total cost for profit tracking
    total_cost = sum([item['cost'] * item['qty'] for item in items])
    estimated_profit = subtotal - total_cost
    
    db.collection("orders").add({
        "date": str(datetime.now(tz)),
        "customer": customer_name,
        "phone": phone,
        "address": address,
        "items": items,
        "subtotal": int(subtotal),
        "delivery_fee": int(delivery_fee),
        "total": int(total),
        "total_cost": int(total_cost),
        "profit": int(estimated_profit),
        "source": source, # WhatsApp, Insta, Web
        "status": status, # Pending, Shipped, Delivered, Returned, Cancelled
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def update_order_status(order_id, new_status):
    db.collection("orders").document(order_id).update({"status": new_status})

def get_orders():
    docs = db.collection("orders").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# --- 4. MODERN UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;600&display=swap');
    .stApp { background-color: #f4f6f9; font-family: 'Inter', sans-serif; color: #333; }
    
    .stat-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #3E64FF;
    }
    .stat-val { font-size: 24px; font-weight: bold; color: #2c3e50; }
    .stat-label { font-size: 14px; color: #7f8c8d; }
    
    /* Status Badges */
    .status-Pending { color: #e67e22; font-weight: bold; }
    .status-Shipped { color: #3498db; font-weight: bold; }
    .status-Delivered { color: #27ae60; font-weight: bold; }
    .status-Returned { color: #c0392b; font-weight: bold; }
    
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("📦 Admin Ops")
    menu = st.radio("Navigate", ["📊 Dashboard", "📝 New Order", "🚚 Order Manager", "📦 Inventory"])
    st.write("---")
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- 6. MODULES ---

# === DASHBOARD ===
if menu == "📊 Dashboard":
    st.subheader("Business Pulse 📉")
    orders = get_orders()
    
    pending = 0
    shipped = 0
    revenue = 0
    profit = 0
    
    if orders:
        df = pd.DataFrame(orders)
        pending = len(df[df['status'] == 'Pending'])
        shipped = len(df[df['status'] == 'Shipped'])
        # Revenue only from Delivered orders usually, but let's track Total Value for now
        delivered_df = df[df['status'] == 'Delivered']
        if not delivered_df.empty:
            revenue = delivered_df['total'].sum()
            profit = delivered_df['profit'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='stat-card'><div class='stat-label'>Orders Pending</div><div class='stat-val' style='color:#e67e22'>{pending}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-card'><div class='stat-label'>To Be Delivered</div><div class='stat-val' style='color:#3498db'>{shipped}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-card'><div class='stat-label'>Realized Revenue</div><div class='stat-val'>Rs {revenue:,}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-card' style='border-color:#27ae60'><div class='stat-label'>Net Profit</div><div class='stat-val' style='color:#27ae60'>Rs {profit:,}</div></div>", unsafe_allow_html=True)

    if orders:
        st.write("### 📦 Recent Order Flow")
        st.dataframe(pd.DataFrame(orders)[['date', 'customer', 'total', 'status', 'source']], use_container_width=True)

# === NEW ORDER ENTRY ===
elif menu == "📝 New Order":
    st.subheader("Manual Order Entry (WhatsApp/Insta)")
    
    products = get_products()
    p_names = [p['name'] for p in products if p['stock'] > 0]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown("##### 🛒 Cart Details")
            if 'ecom_cart' not in st.session_state: st.session_state.ecom_cart = []
            
            sel_p_name = st.selectbox("Select Product", ["Choose..."] + p_names)
            if sel_p_name != "Choose...":
                sel_p = next(p for p in products if p['name'] == sel_p_name)
                qty = st.number_input("Quantity", 1, 100, 1)
                if st.button("Add Item"):
                    st.session_state.ecom_cart.append({
                        "id": sel_p['id'], "name": sel_p['name'],
                        "price": sel_p['price'], "cost": sel_p['cost'], "qty": qty,
                        "subtotal": sel_p['price'] * qty
                    })
            
            # Show Cart
            if st.session_state.ecom_cart:
                cart_df = pd.DataFrame(st.session_state.ecom_cart)
                st.dataframe(cart_df[['name', 'qty', 'subtotal']], hide_index=True)
                if st.button("Clear Cart"): st.session_state.ecom_cart = []

    with col2:
        with st.container(border=True):
            st.markdown("##### 👤 Customer & Delivery")
            cust_name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
            address = st.text_area("Shipping Address")
            source = st.selectbox("Order Source", ["WhatsApp", "Instagram", "Website", "Call"])
            
            # Financials
            subtotal = sum([item['subtotal'] for item in st.session_state.ecom_cart])
            delivery = st.number_input("Delivery Charges", value=200)
            final_total = subtotal + delivery
            
            st.markdown(f"### Total COD: Rs {final_total}")
            
            if st.button("🚀 Place Order", type="primary"):
                if not st.session_state.ecom_cart or not cust_name:
                    st.error("Cart is empty or Customer Name missing!")
                else:
                    create_order(cust_name, phone, address, st.session_state.ecom_cart, subtotal, delivery, final_total, source)
                    st.session_state.ecom_cart = []
                    st.success("Order Created Successfully! Check Order Manager.")
                    time.sleep(1)
                    st.rerun()

# === ORDER MANAGER ===
elif menu == "🚚 Order Manager":
    st.subheader("Manage Shipments")
    
    orders = get_orders()
    if orders:
        # Filter options
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Shipped", "Delivered", "Returned"])
        
        for o in orders:
            if status_filter == "All" or o['status'] == status_filter:
                with st.expander(f"{o['date']} | {o['customer']} | Rs {o['total']} ({o['status']})"):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"**Items:** {[i['name'] + ' x' + str(i['qty']) for i in o['items']]}")
                        st.write(f"**Address:** {o.get('address', 'N/A')}")
                        st.write(f"**Phone:** {o.get('phone', 'N/A')}")
                        st.caption(f"Source: {o.get('source', 'Unknown')}")
                    with c2:
                        current_status = o['status']
                        new_status = st.selectbox("Update Status", 
                                                  ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], 
                                                  key=f"st_{o['id']}", index=["Pending", "Shipped", "Delivered", "Returned", "Cancelled"].index(current_status))
                        
                        if new_status != current_status:
                            update_order_status(o['id'], new_status)
                            st.toast(f"Status updated to {new_status}")
                            time.sleep(1)
                            st.rerun()
    else:
        st.info("No active orders.")

# === INVENTORY ===
elif menu == "📦 Inventory":
    st.subheader("Product Catalog")
    with st.expander("Add New Product"):
        with st.form("new_prod"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Product Name")
            sku = c2.text_input("SKU Code (Optional)")
            price = c1.number_input("Selling Price", min_value=0)
            cost = c2.number_input("Cost Price", min_value=0)
            stock = st.number_input("Stock Qty", min_value=1)
            if st.form_submit_button("Add to Catalog"):
                add_product(name, price, cost, stock, sku)
                st.success("Product Added")
                st.rerun()
    
    prods = get_products()
    if prods: st.dataframe(pd.DataFrame(prods))
