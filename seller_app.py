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

# --- 3. PREMIUM UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp { background-color: #F3F4F6; font-family: 'Inter', sans-serif; }
    
    /* Dashboard Cards */
    .kpi-card {
        background: white; padding: 24px; border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 6px solid #4F46E5;
    }
    .kpi-title { font-size: 14px; font-weight: 600; color: #6B7280; text-transform: uppercase; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #111827; margin-top: 8px; }
    
    /* Invoice Style */
    .invoice-box {
        background: white; padding: 30px; border: 1px solid #eee;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.15); font-size: 16px;
        line-height: 24px; font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
        color: #555; margin-top: 20px;
    }
    .invoice-header { display: flex; justify-content: space-between; border-bottom: 2px solid #eee; padding-bottom: 20px; }
    .invoice-item { border-bottom: 1px solid #eee; padding: 10px 0; display: flex; justify-content: space-between; }
    .invoice-total { border-top: 2px solid #eee; font-weight: bold; padding-top: 10px; margin-top: 10px; text-align: right; }
    
    .stButton>button {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN SYSTEM ---
def login_system():
    if "user_session" not in st.session_state:
        st.session_state["user_session"] = None
        st.session_state["is_admin"] = False

    if st.session_state["user_session"]: return True

    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><div style='text-align:center; padding: 30px; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#4F46E5;'>🚀 E-Com Pro</h1>", unsafe_allow_html=True)
        
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        
        if st.button("✨ Access Dashboard", use_container_width=True):
            if email == "admin@owner.com" and password == "boss123":
                st.session_state["user_session"] = "SUPER_ADMIN"
                st.session_state["is_admin"] = True
                st.rerun()
            
            try:
                doc = db.collection("users").document(email).get()
                if doc.exists and doc.to_dict().get("password") == password:
                    st.session_state["user_session"] = email
                    st.session_state["is_admin"] = False
                    st.success("Welcome!")
                    time.sleep(0.5)
                    st.rerun()
                else: st.error("Invalid Credentials")
            except: st.error("Login Error")
        st.markdown("</div>", unsafe_allow_html=True)
    return False

if not login_system(): st.stop()

current_owner = st.session_state["user_session"]
is_super_admin = st.session_state["is_admin"]

# --- 5. FUNCTIONS ---
def get_products(owner_id):
    docs = db.collection("products").where("owner", "==", owner_id).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, sku, owner_id):
    db.collection("products").add({
        "name": name, "price": int(price), "cost": int(cost), 
        "stock": int(stock), "sku": sku, "owner": owner_id
    })

def update_stock(product_id, new_qty):
    db.collection("products").document(product_id).update({"stock": int(new_qty)})

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

# --- 6. SUPER ADMIN ---
if is_super_admin:
    st.sidebar.title("👑 Super Admin")
    if st.sidebar.button("Logout"):
        st.session_state["user_session"] = None
        st.rerun()
    with st.form("new_client"):
        st.subheader("New Merchant")
        c_email = st.text_input("Email")
        c_pass = st.text_input("Password")
        c_name = st.text_input("Business Name")
        if st.form_submit_button("Create"):
            db.collection("users").document(c_email).set({"password": c_pass, "business_name": c_name})
            st.success("Created!")
    st.stop()

# --- 7. MERCHANT UI ---
with st.sidebar:
    st.markdown(f"## 🛍️ {current_owner.split('@')[0].capitalize()}")
    menu = st.radio("Navigate", ["📊 Overview", "📝 New Order", "🚚 Orders", "📦 Inventory", "💸 Expenses"])
    st.write("---")
    if st.button("Logout"):
        st.session_state["user_session"] = None
        st.rerun()

# === DASHBOARD ===
if menu == "📊 Overview":
    st.title("Business Pulse ⚡")
    orders = get_orders(current_owner)
    expenses = get_expenses(current_owner)
    
    sales = sum([o['total'] for o in orders if o['status']!='Cancelled'])
    profit = sum([o.get('net_profit',0) for o in orders if o['status'] not in ['Returned','Cancelled']])
    loss = sum([o.get('ship_cost',0)+o.get('pack_cost',0) for o in orders if o['status']=='Returned'])
    net = profit - loss - sum([e['amount'] for e in expenses])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Revenue</div><div class='kpi-value'>Rs {sales:,}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Gross Profit</div><div class='kpi-value' style='color:#10B981'>Rs {profit-loss:,}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Expenses</div><div class='kpi-value' style='color:#EF4444'>Rs {sum([e['amount'] for e in expenses]):,}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Profit</div><div class='kpi-value' style='color:#6366F1'>Rs {net:,}</div></div>", unsafe_allow_html=True)

# === NEW ORDER ===
elif menu == "📝 New Order":
    st.title("Create Order")
    products = get_products(current_owner)
    p_names = [p['name'] for p in products if p['stock'] > 0]
    
    c1, c2 = st.columns(2)
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with c1:
        sel = st.selectbox("Product", ["Select..."] + p_names)
        if sel != "Select...":
            p_obj = next(p for p in products if p['name'] == sel)
            qty = st.number_input("Qty", 1, 100, 1)
            if st.button("Add"): st.session_state.cart.append({"name": sel, "qty": qty, "price": p_obj['price'], "cost": p_obj['cost'], "id": p_obj['id']})
        if st.session_state.cart:
            st.dataframe(pd.DataFrame(st.session_state.cart))
            if st.button("Clear"): st.session_state.cart = []

    with c2:
        with st.form("checkout"):
            cust = st.text_input("Name")
            phone = st.text_input("Phone")
            addr = st.text_area("Address")
            src = st.selectbox("Source", ["Web", "WhatsApp", "Insta"])
            subt = sum([i['price']*i['qty'] for i in st.session_state.cart])
            dlv = st.number_input("Delivery", value=200)
            ship = st.number_input("Courier Cost", value=180)
            pack = st.number_input("Packing", value=15)
            if st.form_submit_button("Place Order"):
                if st.session_state.cart and cust:
                    create_order(cust, phone, addr, st.session_state.cart, subt, dlv, ship, pack, subt+dlv, src, current_owner)
                    st.session_state.cart = []
                    st.success("Done!")
                    time.sleep(1)
                    st.rerun()

# === ORDERS & INVOICE ===
elif menu == "🚚 Orders":
    st.title("Order Manager")
    orders = get_orders(current_owner)
    
    for o in orders:
        with st.expander(f"{o.get('date','')} | {o.get('customer','Unknown')} | Rs {o['total']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**Items:** {[i['name'] for i in o['items']]}")
                st.write(f"**Address:** {o.get('address')}")
                # Status Update
                new_stat = st.selectbox("Status", ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], key=f"s_{o['id']}", index=["Pending", "Shipped", "Delivered", "Returned", "Cancelled"].index(o.get('status', 'Pending')))
                if new_stat != o.get('status'):
                    db.collection("orders").document(o['id']).update({"status": new_stat})
                    st.rerun()
            
            with c2:
                # INVOICE GENERATOR
                if st.button("🧾 View Invoice", key=f"inv_{o['id']}"):
                    st.markdown("---")
                    # HTML Invoice Template
                    inv_html = f"""
                    <div class="invoice-box">
                        <div class="invoice-header">
                            <h2>INVOICE</h2>
                            <div>
                                <b>Order ID:</b> {o['id'][:8]}<br>
                                <b>Date:</b> {o['date'].split('.')[0]}<br>
                                <b>Merchant:</b> {current_owner}
                            </div>
                        </div>
                        <p><b>Bill To:</b><br>{o['customer']}<br>{o.get('phone','')}<br>{o.get('address','')}</p>
                        <hr>
                        {''.join([f"<div class='invoice-item'><span>{i['name']} (x{i['qty']})</span><span>Rs {i['price']*i['qty']}</span></div>" for i in o['items']])}
                        <div class='invoice-item'><span>Delivery</span><span>Rs {o['delivery']}</span></div>
                        <div class='invoice-total'>TOTAL: Rs {o['total']}</div>
                    </div>
                    """
                    st.markdown(inv_html, unsafe_allow_html=True)
                    st.info("Tip: Iska screenshot le kar customer ko bhej dein.")

# === INVENTORY (MANUAL MANAGE) ===
elif menu == "📦 Inventory":
    st.title("Inventory")
    tab1, tab2 = st.tabs(["Stock Adjustment", "Add Product"])
    
    # 1. Manual Stock Adjustment
    with tab1:
        st.subheader("Update Stock (Manual)")
        products = get_products(current_owner)
        if products:
            p_names = [p['name'] for p in products]
            sel_p_name = st.selectbox("Select Product", p_names)
            
            if sel_p_name:
                p_obj = next(p for p in products if p['name'] == sel_p_name)
                st.write(f"Current Stock: **{p_obj['stock']}**")
                
                c1, c2 = st.columns(2)
                action = c1.radio("Action", ["Add (+)", "Remove (-)"])
                qty_change = c2.number_input("Quantity", min_value=1, value=1)
                
                if st.button("Update Stock"):
                    new_stock = p_obj['stock'] + qty_change if action == "Add (+)" else p_obj['stock'] - qty_change
                    update_stock(p_obj['id'], new_stock)
                    st.success(f"Stock updated to {new_stock}")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("No products found.")

    # 2. Add New Product
    with tab2:
        with st.form("new_prod"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name")
            sku = c2.text_input("SKU")
            price = c1.number_input("Sale Price", min_value=1)
            cost = c2.number_input("Cost Price", min_value=1)
            stock = st.number_input("Initial Stock", min_value=1)
            if st.form_submit_button("Save Product"):
                add_product(name, price, cost, stock, sku, current_owner)
                st.success("Added!")
                st.rerun()
    
    st.dataframe(pd.DataFrame(get_products(current_owner)))

# === EXPENSES ===
elif menu == "💸 Expenses":
    st.title("Expenses")
    with st.form("add_exp"):
        desc = st.text_input("Description")
        amt = st.number_input("Amount", min_value=1)
        cat = st.selectbox("Category", ["Ads", "Rent", "Salary", "Other"])
        if st.form_submit_button("Log"):
            log_expense(desc, amt, cat, current_owner)
            st.success("Saved!")
            st.rerun()
    st.dataframe(pd.DataFrame(get_expenses(current_owner)))
