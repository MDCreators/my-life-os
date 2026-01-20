import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG ---
st.set_page_config(page_title="Dry Yeast Manager", layout="wide")

# --- 2. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("l"):
        u = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "saeedjanarman3@gmail.com" and p == "saeedjanarman3221":
                st.session_state["auth"] = True; st.rerun()
            else: st.error("Ghalat credentials!")
    st.stop()

# --- 3. CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(tab): return conn.read(worksheet=tab, ttl=0)
def save_data(tab, df): return conn.update(worksheet=tab, data=df)

# --- 4. NAVIGATION ---
st.sidebar.title("🍞 Menu")
m = st.sidebar.radio("Go to:", ["📦 Inventory", "👥 Customers", "🧾 Sales", "🏦 Bank", "💸 Expenses"])
if st.sidebar.button("Logout"): st.session_state["auth"] = False; st.rerun()

st.title(f"Section: {m}")

# Data Load
df = get_data(m) #
st.dataframe(df, use_container_width=True)

# Add Entry Form
with st.form("data_form"):
    st.subheader(f"Add New {m}")
    col1, col2, col3 = st.columns(3)
    with col1: f1 = st.text_input("Username / Item")
    with col2: f2 = st.text_input("Password / Qty / Price")
    with col3: f3 = st.text_input("Shop Name / Detail")
    
    if st.form_submit_button("Save Entry"):
        new_row = pd.DataFrame([{"Username": f1, "Password": f2, "Shop Name": f3}])
        if save_data(m, pd.concat([df, new_row], ignore_index=True)):
            st.success("✅ Recorded!"); st.rerun()
