import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIG ---
st.set_page_config(page_title="E-Com Pro", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# --- 2. FIREBASE CONNECTION (AUTO-FIXER ADDED) ---
if not firebase_admin._apps:
    try:
        # Secrets se key uthao
        # Make sure secrets.toml mein [firebase] section ho
        if "firebase" not in st.secrets:
            st.error("🚨 Secrets file mein [firebase] section nahi mila!")
            st.stop()
            
        key_content = st.secrets["firebase"]["my_key"]
        
        # JSON Parse
        try:
            key_dict = json.loads(key_content)
        except json.JSONDecodeError:
            st.error("🚨 Key Error: Secrets mein 'my_key' sahi JSON format mein nahi hay.")
            st.stop()
        
        # 🔥 CRITICAL FIX: Private Key ki new lines ko theek karo
        # Yeh 'InvalidByte' aur 'MalformedFraming' errors ko khatam kar de ga
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
        
        # Ab connect karo
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
        
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}")
        st.stop()

db = firestore.client()

# --- 3. DARK MODE UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0F172A; font-family: 'Inter', sans-serif; color: #F8FAFC; }
    h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; font-weight: 700; }
    p, label, .stMarkdown { color: #CBD5E1 !important; }
    section[data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
    .kpi-card {
        background: #1E293B; padding: 20px; border-radius: 12px;
        border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    .kpi-title { font-size: 13px; font-weight: 600; color: #94A3B8; letter-spacing: 1px; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #F8FAFC; margin-top: 5px; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; border-radius: 8px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
    .invoice-box { background: white; color: black; padding: 30px; border-radius: 5px; }
    .invoice-box div, .invoice-box p, .invoice-box span { color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN SYSTEM (PERSISTENT & AUTO) ---
def login_system():
    # 1. Check URL for existing session (Auto Login)
    if "user_session" not in st.session_state:
        # URL se check karo (query params)
        qp = st.query_params
        if "session" in qp:
            user_email = qp["session"]
            # Verify if user actually exists (Quick check)
            if user_email == "admin@owner.com":
                st.session_state["user_session"] = "SUPER_ADMIN"
                st.session_state["is_admin"] = True
                st.session_state["business_name"] = "Super Admin"
            else:
                # Normal user verification
                try:
                    doc = db.collection("users").document(user_email).get()
                    if doc.exists:
                        st.session_state["user_session"] = user_email
                        st.session_state["business_name"] = doc.to_dict().get("business_name", "Shop")
                        st.session_state["is_admin"] = False
                except:
                    pass # Fail silently and show login screen

    # 2. Init Session State defaults
    if "user_session" not in st.session_state:
        st.session_state["user_session"] = None
        st.session_state["is_admin"] = False
        st.session_state["business_name"] = "My Shop"

    # 3. If Logged In, Return True
    if st.session_state["user_session"]: 
        return True

    # 4. Show Login Screen
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><div style='text-align:center; padding: 40px; background: #1E293B; border-radius: 20px; border: 1px solid #334155;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#6366F1;'>🚀 E-Com Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p>Secure Merchant Portal</p>", unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="admin@shop.com")
        password = st.text_input("Password", type="password")
        
        if st.button("✨ Login", use_container_width=True):
            # A. Super Admin
            if email == "apexsports480@gmail.com" and password == "13032a7c":
                st.session_state["user_session"] = "SUPER_ADMIN"
                st.session_state["is_admin"] = True
                st.query_params["session"] = "admin@owner.com" # Save to URL
                st.rerun()
            
            # B. Clients
            try:
                doc = db.collection("users").document(email).get()
                if doc.exists and doc.to_dict().get("password") == password:
                    st.session_state["user_session"] = email
                    st.session_state["business_name"] = doc.to_dict().get("business_name")
                    st.session_state["is_admin"] = False
                    st.query_params["session"] = email # Save to URL
                    st.success("Success!")
                    time.sleep(0.1)
                    st.rerun()
                else: st.error("Invalid Credentials")
            except: st.error("Error connecting to DB")
        st.markdown("</div>", unsafe_allow_html=True)
    return False

if not login_system(): st.stop()

# --- GLOBALS ---
current_owner = st.session_state["user_session"]
is_super_admin = st.session_state["is_admin"]
current_biz_name = st.session_state.get("business_name", "My Shop")

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

# --- 6. SUPER ADMIN UI ---
if is_super_admin:
    st.sidebar.markdown("### 👑 Super Admin")
    if st.sidebar.button("Logout"):
        st.query_params.clear() # Clear URL
        st.session_state["user_session"] = None
        st.rerun()
    
    st.title("Admin HQ")
    t1, t2 = st.tabs(["Create Client", "Manage Clients"])
    
    with t1:
        with st.form("new_client"):
            st.subheader("Add New Client")
            c_email = st.text_input("Email")
            c_pass = st.text_input("Password")
            c_name = st.text_input("Business Name")
            if st.form_submit_button("Create Account"):
                db.collection("users").document(c_email).set({
                    "password": c_pass, "business_name": c_name, "created_at": firestore.SERVER_TIMESTAMP
                })
                st.success(f"Client {c_name} Created!")

    with t2:
        st.subheader("Active Clients")
        users = db.collection("users").stream()
        for u in users:
            d = u.to_dict()
            with st.expander(f"🏢 {d.get('business_name')} ({u.id})"):
                c1, c2 = st.columns([4, 1])
                c1.write(f"**Password:** {d.get('password')}")
                if c2.button("🗑️ Delete", key=f"del_{u.id}"):
                    db.collection("users").document(u.id).delete()
                    st.warning(f"Deleted {u.id}")
                    time.sleep(1)
                    st.rerun()
    st.stop()

# --- 7. MERCHANT UI ---
with st.sidebar:
    st.markdown(f"## 🛍️ {current_biz_name}")
    st.caption(f"ID: {current_owner}")
    st.write("---")
    menu = st.radio("Menu", ["📊 Overview", "📝 New Order", "🚚 Orders", "📦 Inventory", "💸 Expenses"])
    st.write("---")
    if st.button("Logout"):
        st.query_params.clear() # Clear URL
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
    c2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Gross Profit</div><div class='kpi-value' style='color:#4ADE80'>Rs {profit-loss:,}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Expenses</div><div class='kpi-value' style='color:#F87171'>Rs {sum([e['amount'] for e in expenses]):,}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Profit</div><div class='kpi-value' style='color:#818CF8'>Rs {net:,}</div></div>", unsafe_allow_html=True)

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
            if st.button("Clear Cart"): st.session_state.cart = []

    with c2:
        with st.form("checkout"):
            cust = st.text_input("Name")
            phone = st.text_input("Phone")
            addr = st.text_area("Address")
            src = st.selectbox("Source", ["WhatsApp", "Instagram", "Facebook", "TikTok", "Web", "Walk-in", "Other"])
            
            subt = sum([i['price']*i['qty'] for i in st.session_state.cart])
            c_a, c_b, c_c = st.columns(3)
            dlv = c_a.number_input("Delivery", value=200)
            ship = c_b.number_input("Courier Cost", value=180)
            pack = c_c.number_input("Packing", value=15)
            
            if st.form_submit_button("🚀 Place Order"):
                if st.session_state.cart and cust:
                    create_order(cust, phone, addr, st.session_state.cart, subt, dlv, ship, pack, subt+dlv, src, current_owner)
                    st.session_state.cart = []
                    st.success("Order Placed!")
                    time.sleep(0.5)
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
                st.caption(f"Address: {o.get('address')} | Phone: {o.get('phone')}")
                
                new_stat = st.selectbox("Status", ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], key=f"s_{o['id']}", index=["Pending", "Shipped", "Delivered", "Returned", "Cancelled"].index(o.get('status', 'Pending')))
                if new_stat != o.get('status'):
                    db.collection("orders").document(o['id']).update({"status": new_stat})
                    st.rerun()
            
            with c2:
                if st.button("🧾 Invoice", key=f"inv_{o['id']}"):
                    st.markdown("---")
                    inv_html = f"""
                    <div class="invoice-box">
                        <h2 style="color:black;">INVOICE</h2>
                        <p><b>Merchant:</b> {current_biz_name}<br><b>Date:</b> {o['date'].split('.')[0]}</p>
                        <hr>
                        <p><b>Bill To:</b><br>{o['customer']}<br>{o.get('phone','')}<br>{o.get('address','')}</p>
                        <hr>
                        {''.join([f"<div style='display:flex; justify-content:space-between;'><span>{i['name']} (x{i['qty']})</span><span>Rs {i['price']*i['qty']}</span></div>" for i in o['items']])}
                        <br>
                        <div style="display:flex; justify-content:space-between;"><b>Delivery</b><span>Rs {o.get('delivery',0)}</span></div>
                        <hr>
                        <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:18px;"><span>TOTAL</span><span>Rs {o['total']}</span></div>
                    </div>
                    """
                    st.markdown(inv_html, unsafe_allow_html=True)

# === INVENTORY ===
elif menu == "📦 Inventory":
    st.title("Inventory")
    tab1, tab2 = st.tabs(["Stock Adjustment", "Add Product"])
    
    with tab1:
        st.subheader("Update Stock")
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
                
                if st.button("Update"):
                    new_stock = p_obj['stock'] + qty_change if action == "Add (+)" else p_obj['stock'] - qty_change
                    update_stock(p_obj['id'], new_stock)
                    st.success("Updated!")
                    time.sleep(0.5)
                    st.rerun()
        else: st.info("No products.")

    with tab2:
        with st.form("new_prod"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name")
            sku = c2.text_input("SKU")
            price = c1.number_input("Sale Price", min_value=1)
            cost = c2.number_input("Cost Price", min_value=1)
            stock = st.number_input("Initial Stock", min_value=1)
            if st.form_submit_button("Save"):
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
