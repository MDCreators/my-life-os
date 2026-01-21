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

# --- 2. FIREBASE CONNECTION ---
if not firebase_admin._apps:
    try:
        if "firebase" not in st.secrets:
            st.error("🚨 Secrets file mein [firebase] section nahi mila.")
            st.stop()
        
        key_content = st.secrets["firebase"]["my_key"]
        try:
            key_dict = json.loads(key_content)
        except json.JSONDecodeError:
            st.error("🚨 JSON Error: Secrets mein key sahi copy-paste nahi hui.")
            st.stop()
        
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
        
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}")
        st.stop()

db = firestore.client()

# --- 3. UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0F172A; font-family: 'Inter', sans-serif; color: #F8FAFC; }
    h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; font-weight: 700; }
    p, label, .stMarkdown { color: #CBD5E1 !important; }
    section[data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
    .kpi-card { background: #1E293B; padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    .kpi-title { font-size: 13px; font-weight: 600; color: #94A3B8; letter-spacing: 1px; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #F8FAFC; margin-top: 5px; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; border-radius: 8px; }
    .stButton>button { background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color: white; border: none; border-radius: 8px; font-weight: 600; }
    
    /* INVOICE STYLING */
    .invoice-box { background: white; color: black; padding: 30px; border-radius: 5px; font-family: Arial, sans-serif; }
    .invoice-box h2, .invoice-box p, .invoice-box span, .invoice-box div { color: #333 !important; }
    .invoice-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .invoice-table th { text-align: left; border-bottom: 2px solid #ddd; padding: 8px; background-color: #f8f8f8; color: black !important; font-weight: bold; }
    .invoice-table td { border-bottom: 1px solid #eee; padding: 8px; color: black !important; }
    .total-row td { border-top: 2px solid #333; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN SYSTEM ---
def login_system():
    if "user_session" not in st.session_state:
        qp = st.query_params
        if "session" in qp:
            user_email = qp["session"]
            if user_email == "admin@owner.com":
                st.session_state["user_session"] = "SUPER_ADMIN"
                st.session_state["is_admin"] = True
                st.session_state["business_name"] = "Super Admin"
            else:
                try:
                    doc = db.collection("users").document(user_email).get()
                    if doc.exists:
                        st.session_state["user_session"] = user_email
                        st.session_state["business_name"] = doc.to_dict().get("business_name", "Shop")
                        st.session_state["is_admin"] = False
                except: pass

    if "user_session" not in st.session_state:
        st.session_state["user_session"] = None
        st.session_state["is_admin"] = False
        st.session_state["business_name"] = "My Shop"

    if st.session_state["user_session"]: return True

    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><div style='text-align:center; padding: 40px; background: #1E293B; border-radius: 20px; border: 1px solid #334155;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#6366F1;'>🚀 E-Com Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p>Secure Merchant Portal</p>", unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="admin@shop.com")
        password = st.text_input("Password", type="password")
        if st.button("✨ Login", use_container_width=True):
            if email == "apexsports480@gmail.com" and password == "13032a7c":
                st.session_state["user_session"] = "SUPER_ADMIN"
                st.session_state["is_admin"] = True
                st.query_params["session"] = "admin@owner.com"
                st.rerun()
            try:
                doc = db.collection("users").document(email).get()
                if doc.exists and doc.to_dict().get("password") == password:
                    st.session_state["user_session"] = email
                    st.session_state["business_name"] = doc.to_dict().get("business_name")
                    st.session_state["is_admin"] = False
                    st.query_params["session"] = email
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

def create_order(customer, phone, address, items, subtotal, global_discount, delivery, ship_cost, pack_cost, total, source, owner_id):
    tz = pytz.timezone('Asia/Karachi')
    total_cost = sum([i.get('cost',0)*i['qty'] for i in items])
    net_profit = total - (total_cost + ship_cost + pack_cost)
    
    db.collection("orders").add({
        "date": str(datetime.now(tz)), "customer": customer, "phone": phone, "address": address,
        "items": items, "subtotal": subtotal, "global_discount": global_discount,
        "delivery": delivery, "ship_cost": ship_cost, "pack_cost": pack_cost, 
        "total": total, "net_profit": net_profit, "source": source, "status": "Pending",
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

# --- 6. UI LOGIC ---
if is_super_admin:
    st.sidebar.markdown("### 👑 Super Admin")
    if st.sidebar.button("Logout"):
        st.query_params.clear()
        st.session_state["user_session"] = None
        st.rerun()
    st.title("Admin HQ")
    st.stop()

with st.sidebar:
    st.markdown(f"## 🛍️ {current_biz_name}")
    st.caption(f"ID: {current_owner}")
    st.write("---")
    menu = st.radio("Menu", ["📊 Overview", "📝 New Order", "🚚 Orders", "📦 Inventory", "💸 Expenses"])
    st.write("---")
    if st.button("Logout"):
        st.query_params.clear()
        st.session_state["user_session"] = None
        st.rerun()

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

elif menu == "📝 New Order":
    st.title("Create Order")
    products = get_products(current_owner)
    p_names = [p['name'] for p in products if p['stock'] > 0]
    c1, c2 = st.columns(2)
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with c1:
        st.subheader("Add Item")
        sel = st.selectbox("Product", ["Select..."] + p_names)
        if sel != "Select...":
            p_obj = next(p for p in products if p['name'] == sel)
            
            # --- Per Item Discount ---
            col_q, col_d = st.columns(2)
            qty = col_q.number_input("Qty", 1, 100, 1)
            item_disc = col_d.number_input("Discount %", 0, 100, 0, help="Is item par kitna discount dena hai?")
            
            unit_price = p_obj['price']
            final_unit_price = int(unit_price * (1 - item_disc/100))
            
            st.markdown(f"Price: Rs {unit_price} ➝ **Rs {final_unit_price}**")
            
            if st.button("Add to Cart"):
                st.session_state.cart.append({
                    "name": sel, "qty": qty, 
                    "original_price": unit_price, "discount_percent": item_disc, "final_price": final_unit_price,
                    "cost": p_obj['cost'], "id": p_obj['id'], "line_total": final_unit_price * qty
                })
        
        if st.session_state.cart:
            st.markdown("---")
            cart_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(cart_df[['name', 'qty', 'discount_percent', 'final_price', 'line_total']], use_container_width=True)
            if st.button("Clear Cart"): st.session_state.cart = []
    
    with c2:
        st.subheader("Customer & Bill")
        with st.form("checkout"):
            cust = st.text_input("Name")
            phone = st.text_input("Phone")
            addr = st.text_area("Address")
            src = st.selectbox("Source", ["WhatsApp", "Instagram", "Facebook", "TikTok", "Web", "Walk-in"])
            
            subt = sum([i['line_total'] for i in st.session_state.cart])
            st.markdown(f"**Subtotal:** Rs {subt}")
            
            c_a, c_b, c_c, c_d = st.columns(4)
            global_disc = c_a.number_input("Extra Disc (Rs)", 0)
            dlv = c_b.number_input("Delivery", value=200)
            ship = c_c.number_input("Courier Cost", value=180)
            pack = c_d.number_input("Packing", value=15)
            
            final_total = subt - global_disc + dlv
            st.markdown(f"<h3 style='color:#4ADE80'>Total: Rs {final_total}</h3>", unsafe_allow_html=True)

            if st.form_submit_button("🚀 Place Order"):
                if st.session_state.cart and cust:
                    create_order(cust, phone, addr, st.session_state.cart, subt, global_disc, dlv, ship, pack, final_total, src, current_owner)
                    st.session_state.cart = []
                    st.success("Order Placed!")
                    time.sleep(0.5)
                    st.rerun()

elif menu == "🚚 Orders":
    st.title("Order Manager")
    orders = get_orders(current_owner)
    for o in orders:
        with st.expander(f"{o.get('date','')} | {o.get('customer','Unknown')} | Rs {o['total']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write("**Items:**")
                for i in o['items']:
                    d_per = i.get('discount_percent', 0)
                    price = i.get('final_price', i.get('price', 0))
                    disc_txt = f"(Disc: {d_per}%)" if d_per > 0 else ""
                    st.write(f"- {i['name']} x{i['qty']} {disc_txt} = Rs {price*i['qty']}")
                
                st.caption(f"Address: {o.get('address')} | Phone: {o.get('phone')}")
                new_stat = st.selectbox("Status", ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], key=f"s_{o['id']}", index=["Pending", "Shipped", "Delivered", "Returned", "Cancelled"].index(o.get('status', 'Pending')))
                if new_stat != o.get('status'):
                    db.collection("orders").document(o['id']).update({"status": new_stat})
                    st.rerun()
            with c2:
                if st.button("🧾 Invoice", key=f"inv_{o['id']}"):
                    st.markdown("---")
                    
                    # INVOICE GENERATION
                    rows = ""
                    for i in o['items']:
                        d_per = i.get('discount_percent', 0)
                        price = i.get('final_price', i.get('price', 0))
                        total = price * i['qty']
                        badg = f"<span style='color:red; font-size:12px;'>(-{d_per}%)</span>" if d_per > 0 else ""
                        rows += f"<tr><td>{i['name']} {badg}</td><td>{i['qty']}</td><td>{price}</td><td style='text-align:right;'>{total}</td></tr>"
                    
                    g_disc_row = ""
                    if o.get('global_discount', 0) > 0:
                        g_disc_row = f"<tr><td colspan='3'>Extra Discount</td><td style='text-align:right; color:red;'>-{o.get('global_discount')}</td></tr>"

                    # HTML (No indentation to prevent code block)
                    html = f"""<div class="invoice-box">
<h2 style="margin-top:0;">INVOICE</h2>
<p><b>Merchant:</b> {current_biz_name}<br><b>Date:</b> {o['date'].split('.')[0]}</p>
<hr>
<p><b>Bill To:</b><br>{o['customer']}<br>{o.get('phone','')}<br>{o.get('address','')}</p>
<table class="invoice-table">
<thead><tr><th>Item</th><th>Qty</th><th>Price</th><th style="text-align:right;">Total</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<br>
<div style="float:right; width:50%;">
<table style="width:100%">
<tr><td>Subtotal:</td><td style="text-align:right;">{o.get('subtotal',0)}</td></tr>
{g_disc_row}
<tr><td>Delivery:</td><td style="text-align:right;">{o.get('delivery',0)}</td></tr>
<tr style="font-weight:bold; font-size:18px;"><td>TOTAL:</td><td style="text-align:right;">Rs {o['total']}</td></tr>
</table>
</div>
<div style="clear:both;"></div>
</div>"""
                    st.markdown(html, unsafe_allow_html=True)

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
