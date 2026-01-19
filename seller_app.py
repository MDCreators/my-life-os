import streamlit as st
import pandas as pd
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
        st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>🚀 E-Com Scale Up</h1>", unsafe_allow_html=True)
        st.text_input("Admin Login", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Admin Login", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("🔒 Access Denied")
        return False
    else:
        return True

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="E-Com Pro", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

if not check_password():
    st.stop()

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

# --- 3. DATABASE FUNCTIONS ---
def get_products():
    docs = db.collection("products").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, sku):
    db.collection("products").add({
        "name": name, "price": int(price), "cost": int(cost), 
        "stock": int(stock), "sku": sku
    })

def adjust_stock_manually(product_id, qty, reason):
    ref = db.collection("products").document(product_id)
    curr = ref.get().to_dict()
    if curr:
        new_stock = int(curr.get('stock', 0)) + int(qty)
        ref.update({"stock": new_stock})
        tz = pytz.timezone('Asia/Karachi')
        db.collection("stock_logs").add({
            "date": str(datetime.now(tz)),
            "product": curr['name'],
            "change": qty,
            "reason": reason,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

def create_order(customer, phone, address, items, subtotal, delivery_charged, actual_shipping_cost, packaging_cost, total, source):
    tz = pytz.timezone('Asia/Karachi')
    product_cost = sum([item['cost'] * item['qty'] for item in items])
    total_expense_on_order = product_cost + actual_shipping_cost + packaging_cost
    net_profit = total - total_expense_on_order
    
    db.collection("orders").add({
        "date": str(datetime.now(tz)),
        "customer": customer,
        "phone": phone,
        "address": address,
        "items": items,
        "subtotal": int(subtotal),
        "delivery_charged": int(delivery_charged),
        "actual_shipping_cost": int(actual_shipping_cost),
        "packaging_cost": int(packaging_cost),
        "total": int(total),
        "net_profit": int(net_profit),
        "source": source,
        "status": "Pending",
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    
    for item in items:
        adjust_stock_manually(item['id'], -item['qty'], "Online Order")

def update_order_status(order_id, new_status):
    db.collection("orders").document(order_id).update({"status": new_status})

def log_general_expense(desc, amount, category):
    tz = pytz.timezone('Asia/Karachi')
    db.collection("expenses").add({
        "date": str(datetime.now(tz)),
        "desc": desc,
        "amount": int(amount),
        "category": category,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_data(collection, limit=100):
    docs = db.collection(collection).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# --- 4. UI STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; color: #333; }
    .kpi-card {
        background: white; padding: 20px; border-radius: 12px;
        border: 1px solid #E0E0E0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-title { font-size: 14px; color: #757575; }
    .kpi-val { font-size: 26px; font-weight: 700; color: #333; }
    .success-val { color: #2E7D32; }
    .danger-val { color: #D32F2F; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🚀 E-Com Ops")
    menu = st.radio("Menu", ["📊 Profit Dashboard", "📝 New Order", "💸 Expenses (Ads/Ops)", "📦 Inventory & Stock", "🚚 Order Manager"])
    st.write("---")
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- 6. MODULES ---

# === PROFIT DASHBOARD ===
if menu == "📊 Profit Dashboard":
    st.subheader("Real Net Profit Report 📉")
    
    orders = get_data("orders")
    expenses = get_data("expenses")
    
    total_sales = 0
    gross_profit_orders = 0
    total_marketing = 0
    total_ops = 0
    
    if orders:
        df_ord = pd.DataFrame(orders)
        if 'total' in df_ord.columns:
            total_sales = df_ord['total'].sum()
        if 'net_profit' in df_ord.columns:
            gross_profit_orders = df_ord['net_profit'].sum()
    
    if expenses:
        df_exp = pd.DataFrame(expenses)
        if 'category' in df_exp.columns and 'amount' in df_exp.columns:
            total_marketing = df_exp[df_exp['category'] == 'Marketing (Ads)']['amount'].sum()
            total_ops = df_exp[df_exp['category'] != 'Marketing (Ads)']['amount'].sum()
    
    final_net_profit = gross_profit_orders - total_marketing - total_ops
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Sales (COD)</div><div class='kpi-val'>Rs {total_sales:,}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Order Gross Profit</div><div class='kpi-val success-val'>Rs {gross_profit_orders:,}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Marketing Spend</div><div class='kpi-val danger-val'>Rs {total_marketing:,}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card'><div class='kpi-title'>🔥 REAL NET PROFIT</div><div class='kpi-val success-val'>Rs {final_net_profit:,}</div></div>", unsafe_allow_html=True)
    
    st.info("💡 **Formula:** (Order Revenue - Product Cost - Shipping - Packaging) - (Ads + Other Expenses)")

# === NEW ORDER ===
elif menu == "📝 New Order":
    st.subheader("Create Order 📦")
    
    col1, col2 = st.columns(2)
    products = get_products()
    p_names = [p['name'] for p in products if p.get('stock', 0) > 0]
    
    if 'cart_adv' not in st.session_state: st.session_state.cart_adv = []
    
    with col1:
        with st.container(border=True):
            st.markdown("##### 1. Select Products")
            sel_p = st.selectbox("Product", ["Select..."] + p_names)
            if sel_p != "Select...":
                prod_obj = next(p for p in products if p['name'] == sel_p)
                qty = st.number_input("Qty", 1, 100, 1)
                if st.button("Add to Order"):
                    st.session_state.cart_adv.append({
                        "id": prod_obj['id'], "name": prod_obj['name'],
                        "price": prod_obj['price'], "cost": prod_obj['cost'], "qty": qty,
                        "subtotal": prod_obj['price'] * qty
                    })
            
            if st.session_state.cart_adv:
                st.dataframe(pd.DataFrame(st.session_state.cart_adv)[['name', 'qty', 'subtotal']], hide_index=True)
                if st.button("Clear Cart"): st.session_state.cart_adv = []

    with col2:
        with st.form("order_details"):
            st.markdown("##### 2. Customer & Costs")
            cust = st.text_input("Customer Name")
            phone = st.text_input("Phone")
            addr = st.text_area("Address")
            src = st.selectbox("Source", ["Facebook Ad", "Instagram", "WhatsApp", "Website"])
            
            st.divider()
            st.markdown("##### 💰 Financials")
            
            sub_t = sum([i['subtotal'] for i in st.session_state.cart_adv])
            st.write(f"Product Total: Rs {sub_t}")
            
            c_a, c_b = st.columns(2)
            del_charged = c_a.number_input("Delivery (Customer Pays)", value=200)
            ship_cost = c_b.number_input("Actual Courier Cost (You Pay)", value=180)
            pack_cost = st.number_input("Packaging Cost", value=15)
            
            final_cod = sub_t + del_charged
            st.markdown(f"### COD Amount: Rs {final_cod}")
            
            if st.form_submit_button("🚀 Confirm Order"):
                if st.session_state.cart_adv and cust:
                    create_order(cust, phone, addr, st.session_state.cart_adv, sub_t, del_charged, ship_cost, pack_cost, final_cod, src)
                    st.session_state.cart_adv = []
                    st.success("Order Created! Stock Deducted.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Cart empty or details missing.")

# === EXPENSES ===
elif menu == "💸 Expenses (Ads/Ops)":
    st.subheader("Marketing & Overheads 💸")
    
    with st.form("exp_form"):
        c1, c2 = st.columns(2)
        desc = c1.text_input("Description (e.g. Facebook Ad Budget)")
        amt = c2.number_input("Amount (Rs)", min_value=1)
        cat = st.selectbox("Category", ["Marketing (Ads)", "Packaging Material (Bulk)", "Internet/Load", "Office Rent", "Other"])
        
        if st.form_submit_button("Log Expense"):
            log_general_expense(desc, amt, cat)
            st.success("Expense Logged.")
            time.sleep(1)
            st.rerun()
            
    exps = get_data("expenses")
    if exps:
        st.write("### Recent Spending")
        st.dataframe(pd.DataFrame(exps)[['date', 'category', 'desc', 'amount']], use_container_width=True)

# === INVENTORY & STOCK ===
elif menu == "📦 Inventory & Stock":
    st.subheader("Hybrid Inventory Manager 🏪")
    
    tab1, tab2 = st.tabs(["Stock Adjustment (Offline)", "Product Catalog"])
    
    with tab1:
        st.info("Offline Sale / Damage Adjustment")
        prods = get_products()
        p_list = [p['name'] for p in prods]
        
        c1, c2, c3 = st.columns(3)
        sel_prod = c1.selectbox("Select Product", p_list)
        action = c2.radio("Action", ["Reduce Stock (Sale/Damage)", "Add Stock (Restock)"])
        qty_adj = c3.number_input("Quantity", min_value=1, value=1)
        
        if st.button("Update Stock"):
            target_p = next(p for p in prods if p['name'] == sel_prod)
            final_qty = -qty_adj if "Reduce" in action else qty_adj
            reason = "Offline Sale/Manual" if "Reduce" in action else "Restock"
            adjust_stock_manually(target_p['id'], final_qty, reason)
            st.success(f"Stock Updated: {action} {qty_adj}")
            time.sleep(1)
            st.rerun()

    with tab2:
        with st.expander("➕ Add New Product"):
            with st.form("new_p"):
                name = st.text_input("Name")
                sku = st.text_input("SKU")
                pr = st.number_input("Sale Price", min_value=0)
                co = st.number_input("Cost Price", min_value=0)
                stk = st.number_input("Stock", min_value=1)
                if st.form_submit_button("Save"):
                    add_product(name, pr, co, stk, sku)
                    st.success("Saved")
                    st.rerun()
        if prods:
            df = pd.DataFrame(prods)
            st.dataframe(df[['name', 'stock', 'price', 'cost', 'sku']], use_container_width=True)

# === ORDER MANAGER (UPDATED) ===
elif menu == "🚚 Order Manager":
    st.subheader("Track & Update Orders")
    orders = get_data("orders")
    
    if orders:
        status_options = ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"]
        
        for o in orders:
            # Color code for status
            status_color = "red"
            if o['status'] == "Delivered": status_color = "green"
            elif o['status'] == "Shipped": status_color = "blue"
            elif o['status'] == "Pending": status_color = "orange"
            
            with st.expander(f"{o['date']} | {o['customer']} | Rs {o['total']} ({o['status']})"):
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    st.write(f"**Items:** {[i['name'] + ' x' + str(i['qty']) for i in o['items']]}")
                    st.caption(f"Address: {o.get('address', 'N/A')} | Phone: {o.get('phone', 'N/A')}")
                    st.caption(f"Profit on this Order: Rs {o.get('net_profit', 0)}")
                
                with c2:
                    current_idx = 0
                    if o['status'] in status_options:
                        current_idx = status_options.index(o['status'])
                    
                    new_val = st.selectbox("Change Status", status_options, index=current_idx, key=o['id'])
                    
                    if new_val != o['status']:
                        update_order_status(o['id'], new_val)
                        st.toast(f"Status Updated to {new_val}")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("No active orders found.")
