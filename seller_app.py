import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM (ADMIN) ---
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

# --- 2. FIREBASE ---
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

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Admin Ops")
    # YAHAN HAI WO NAYA OPTION 👇
    menu = st.radio("Menu", ["📊 Dashboard", "👥 User Management", "📝 New Order", "🚚 Order Manager"])
    st.write("---")
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- 4. MODULES ---

if menu == "📊 Dashboard":
    st.title("Business Dashboard 📈")
    st.info("Welcome back, Boss! Select an option from the sidebar.")

# === 👥 USER MANAGEMENT (YE HAI WO CHEEZ) ===
elif menu == "👥 User Management":
    st.subheader("Customer Access Control 🔐")
    st.write("Yahan aap Customer ka login banayen ge taake wo Life OS app khol sakay.")
    
    with st.form("create_user"):
        st.write("### Create New Customer Login")
        new_email = st.text_input("Customer Email (e.g. dawood@gmail.com)")
        new_pass = st.text_input("Assign Password", type="password")
        
        if st.form_submit_button("Create Account"):
            if new_email and new_pass:
                # Database mein user save karo
                db.collection("users").document(new_email).set({
                    "password": new_pass,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "active": True
                })
                st.success(f"✅ User Created: {new_email}")
                st.info(f"Password set to: {new_pass}")
            else:
                st.error("Email aur Password dono likhna zaroori hai!")

    st.divider()
    st.write("### Active Users List")
    # Check karo kon kon registered hai
    users_ref = db.collection("users").stream()
    count = 0
    for u in users_ref:
        st.code(f"👤 {u.id}")
        count += 1
    if count == 0:
        st.warning("Abhi koi user nahi hai. Upar form se banayen!")

elif menu == "📝 New Order":
    st.title("New Order")
    st.write("(Order form yahan ayega...)")

elif menu == "🚚 Order Manager":
    st.title("Order Manager")
    st.write("(Order list yahan ayegi...)")
