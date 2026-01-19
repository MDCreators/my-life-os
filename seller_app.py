import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM (SECURE) ---
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
        st.markdown("<h1 style='text-align:center; color:#FFD700;'>💼 Business Manager Pro</h1>", unsafe_allow_html=True)
        st.text_input("Admin Email", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Admin Email", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("🔒 Access Denied")
        return False
    else:
        return True

# --- 1. SETUP & AUTH ---
st.set_page_config(page_title="Ecommerce Pro", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

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

# --- 3. DATABASE FUNCTIONS ---
# Products (Inventory)
def get_products():
    docs = db.collection("products").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, category):
    db.collection("products").add({
        "name": name, "price": price, "cost": cost, 
        "stock": stock, "category": category
    })

def update_stock(product_id, qty_sold):
    # Transaction logic would be better here, but keeping simple
    ref = db.collection("products").document(product_id)
    curr = ref.get().to_dict()
    new_stock = curr['stock'] - qty_sold
    ref.update({"stock": new_stock})

# Sales (Orders)
def log_sale(items, total, profit, customer):
    tz = pytz.timezone('Asia/Karachi')
    db.collection("sales").add({
        "date": str(datetime.now(tz)),
        "items": items,
        "total": total,
        "profit": profit,
        "customer": customer,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_sales():
    docs = db.collection("sales").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# --- 4. UI STYLING (PREMIUM BUSINESS) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .metric-card {
        background: linear-gradient(145deg, #1e212b, #16181f);
        padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .big-num { font-size: 32px; font-weight: bold; color: #FFD700; }
    .stButton>button { background-color: #FFD700; color: black; font-weight: bold; border-radius: 8px; }
    .success-msg { color: #00FF7F; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("💼 Admin Panel")
    st.write(f"Logged in as: {current_user}")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 POS Terminal", "📦 Inventory", "🧾 Orders History"])
    st.write("---")
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- 6. APP MODULES ---

# === DASHBOARD ===
if menu == "📊 Dashboard":
    st.title("Business Overview 📈")
    
    sales_data = get_sales()
    products_data = get_products()
    
    if sales_data:
        df_sales = pd.DataFrame(sales_data)
        total_rev = df_sales['total'].sum()
        total_profit = df_sales['profit'].sum()
        orders_count = len(df_sales)
    else:
        total_rev, total_profit, orders_count = 0, 0, 0
        
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h5>Total Revenue</h5><div class='big-num'>PKR {total_rev:,}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h5>Net Profit</h5><div class='big-num' style='color:#00FF7F;'>PKR {total_profit:,}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h5>Total Orders</h5><div class='big-num' style='color:white;'>{orders_count}</div></div>", unsafe_allow_html=True)

    st.write("### 📉 Sales Trend")
    if sales_data:
        fig = px.bar(df_sales, x='date', y='total', title="
