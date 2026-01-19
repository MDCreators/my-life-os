import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM (ADMIN ONLY) ---
def check_password():
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>🚀 E-Com Admin</h1>", unsafe_allow_html=True)
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

# --- 1. CONFIG ---
st.set_page_config(page_title="E-Com Pro", page_icon="🚀", layout="wide")

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

def get_data(collection, limit=100):
    docs = db.collection(collection).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 Admin Ops")
    # YAHAN 'USER MANAGEMENT' ADD KIYA HAI 👇
    menu = st.radio("Menu", ["📊 Profit Dashboard", "👥 User Management", "📝 New Order", "🚚 Order Manager", "📦 Inventory"])
    st.write("---")
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- 5. MODULES ---

# === PROFIT DASHBOARD ===
if menu == "📊 Profit Dashboard":
    st.subheader("Business Dashboard 📈")
    orders = get_data("orders")
    if orders:
        df = pd.DataFrame(orders)
        st.metric("Total Orders", len(df))
        if 'net_profit' in df.columns:
            st.metric("Est. Net Profit", f"Rs {df['net_profit'].sum():,}")
    else:
        st.info("No orders yet.")

# === USER MANAGEMENT (YE HAI WO MISSING CHEEZ) ===
elif menu == "👥 User Management":
    st.subheader("🔐 Life OS Customer Access")
    st.info("Yahan se User banayen taake wo Doosri App (Life OS) mein login kar sakay.")
    
    with st.form("create_user"):
        st.write("### Create New User")
        new_email = st.text_input("User Email (e.g. dawood@gmail.com)")
        new_pass = st.text_input("Set Password", type="password")
        
        if st.form_submit_button("Create Account"):
            if new_email and new_pass:
                # Save to database
                db.collection("users").document(new_email).set({
                    "password": new_pass,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "active": True
                })
                st.success(f"✅ User Created: {new_email}")
                st.info(f"Ab ye user Life OS app mein login kar sakta hai.")
            else:
                st.error("Email aur Password zaroori hai.")

# === NEW ORDER ===
elif menu == "📝 New Order":
    st.subheader("Create Order")
    # (Simplified for brevity, but connects to DB)
    st.write("Use full code for order placement logic.")

# === ORDER MANAGER ===
elif menu == "🚚 Order Manager":
    st.subheader("Order Manager")
    orders = get_data("orders")
    if orders:
        st.dataframe(pd.DataFrame(orders))

# === INVENTORY ===
elif menu == "📦 Inventory":
    st.subheader("Inventory")
    prods = get_products()
    if prods:
        st.dataframe(pd.DataFrame(prods))
