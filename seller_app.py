import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 
import time
import random
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM (FIXED & PERMANENT) ---
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
        st.markdown("<h1 style='text-align:center;'>⚡ Life OS Pro Login</h1>", unsafe_allow_html=True)
        st.text_input("Username (Email)", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Username (Email)", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not known or password incorrect")
        return False
    else:
        return True

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="Life OS Ultimate", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

if not check_password():
    st.stop()

current_user_id = st.session_state["logged_in_user"]

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

# --- 3. DATA FUNCTIONS (CLOUD SAVING) ---
def load_user_data(user_id):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except: return None

def save_user_data(user_id):
    try:
        data = {
            "goals": st.session_state.goals, "habits": st.session_state.habits,
            "balance": st.session_state.balance, "transactions": st.session_state.transactions,
            "water": st.session_state.water, "xp": st.session_state.xp,
            "level": st.session_state.level, "user_name": st.session_state.user_name,
            "currency": st.session_state.currency, "timezone": st.session_state.timezone,
            "journal_logs": st.session_state.journal_logs, "biz_revenue": st.session_state.get('biz_revenue', 0)
        }
        db.collection("users").document(user_id).set(data)
    except: pass

# --- 4. STATE INITIALIZATION ---
if 'data_loaded' not in st.session_state:
    saved_data = load_user_data(current_user_id)
    if saved_data:
        for k, v in saved_data.items(): st.session_state[k] = v
    else:
        # Initial Defaults
        st.session_state.update({
            "user_name": "Boss", "xp": 0, "level": 1, "balance": 0, "water": 0,
            "transactions": [], "goals": [], "habits": [], "currency": "PKR",
            "journal_logs": [], "timezone": "Asia/Karachi", "biz_revenue": 0
        })
    st.session_state.data_loaded = True

# --- 5. PREMIUM STYLING (GLASSMORPHISM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Poppins:wght@300;400;600&display=swap');
    
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }
    .neon-text {
        font-family: 'Orbitron', sans-serif;
        color: #00f2fe;
        text-shadow: 0 0 10px #00f2fe;
    }
    .stButton>button {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        color: black; border: none; border-radius: 12px; font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #00f2fe; }
</style>
""", unsafe_allow_html=True)

# --- 6. NAVIGATION & SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h1 class='neon-text'>🚀 {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    st.write(f"Level {st.session_state.level} • {st.session_state.xp} XP")
    st.progress(min(st.session_state.xp / (st.session_state.level * 100), 1.0))
    
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()
    
    menu = st.radio("System Access", ["📊 Intelligence", "🎯 Missions", "💰 Financials", "⚡ Boss Mode", "💪 Bio-Status", "📝 Logs", "⚙️ Core"])

# --- 7. HELPER FUNCTIONS ---
def check_level_up(xp_gain):
    st.session_state.xp += xp_gain
    req = st.session_state.level * 100
    if st.session_state.xp >= req:
        st.session_state.level += 1
        st.session_state.xp = 0
        st.balloons()
        st.toast("🎉 LEVEL UP! New potential unlocked.", icon="🆙")
    save_user_data(current_user_id)

# --- 8. MODULES ---
tz = pytz.timezone(st.session_state.timezone)
now = datetime.now(tz)

if menu == "📊 Intelligence":
    st.markdown("<h2 class='neon-text'>Strategic Overview</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='glass-card'><h5>Total Balance</h5><h2 style='color:#00ff87;'>{st.session_state.currency} {st.session_state.balance}</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='glass-card'><h5>Missions Pending</h5><h2 style='color:#ff4b2b;'>{sum(1 for g in st.session_state.goals if not g['done'])}</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='glass-card'><h5>Business Revenue</h5><h2 style='color:#f9d423;'>{st.session_state.currency} {st.session_state.biz_revenue}</h2></div>", unsafe_allow_html=True)
    
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        fig = px.line(df, x='Date', y='Amt', color='Type', title="Cashflow Trend", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

elif menu == "🎯 Missions":
    st.markdown("<h2 class='neon-text'>Active Missions</h2>", unsafe_allow_html=True)
    with st.expander("➕ Deploy New Mission"):
        new_g = st.text_input("Mission Name")
        if st.button("Deploy"):
            st.session_state.goals.append({"text": new_g, "done": False})
            save_user_data(current_user_id)
            st.rerun()
    
    for i, g in enumerate(st.session_state.goals):
        col1, col2 = st.columns([0.1, 0.9])
        if col1.checkbox("", value=g['done'], key=f"g_{i}"):
            if not g['done']:
                st.session_state.goals[i]['done'] = True
                check_level_up(25)
                st.rerun()
        col2.write(f"**{g['text']}**" if not g['done'] else f"~~{g['text']}~~")

elif menu == "💰 Financials":
    st.markdown("<h2 class='neon-text'>Financial Hub</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Add Entry", "Ledger"])
    with tab1:
        with st.form("wallet_form"):
            t_type = st.radio("Type", ["Expense 🔴", "Income 🟢"], horizontal=True)
            cats = ["Food 🍔", "Fuel ⛽", "Business 📈", "Freelance 💻", "Salary 💰", "Fun 🎉", "Education 📚"]
            cat = st.selectbox("Category", cats)
            amt = st.number_input("Amount", min_value=1)
            desc = st.text_input("Description")
            if st.form_submit_button("Record Transaction"):
                val = amt if "Income" in t_type else -amt
                st.session_state.balance += val
                if "Business" in cat or "Freelance" in cat: st.session_state.biz_revenue += amt
                st.session_state.transactions.append({"Date": str(now.date()), "Cat": cat, "Amt": amt, "Type": t_type, "Desc": desc})
                check_level_up(10)
                st.rerun()
    with tab2:
        st.dataframe(pd.DataFrame(st.session_state.transactions[::-1]), use_container_width=True)

elif menu == "⚡ Boss Mode":
    st.markdown("<h2 class='neon-text'>Deep Focus Timer</h2>", unsafe_allow_html=True)
    st.write("Focus for 25 minutes to earn bonus XP.")
    col1, col2 = st.columns(2)
    minutes = col1.number_input("Set Minutes", value=25)
    if col2.button("Start Focus Session"):
        ph = st.empty()
        for i in range(minutes * 60, 0, -1):
            mm, ss = divmod(i, 60)
            ph.markdown(f"<h1 style='text-align:center; font-size:100px;'>{mm:02d}:{ss:02d}</h1>", unsafe_allow_html=True)
            time.sleep(1)
        st.success("Session Complete! +50 XP")
        check_level_up(50)

elif menu == "💪 Bio-Status":
    st.markdown("<h2 class='neon-text'>Biological Tracking</h2>", unsafe_allow_html=True)
    st.write(f"💧 Water: {st.session_state.water}/8 Glasses")
    if st.button("➕ Log Hydration"):
        st.session_state.water += 1
        check_level_up(5)
        st.rerun()

elif menu == "📝 Logs":
    st.markdown("<h2 class='neon-text'>Neural Journal</h2>", unsafe_allow_html=True)
    mood = st.select_slider("Mood Level", options=["Sad", "Neutral", "Happy", "God Mode"])
    note = st.text_area("Daily Reflection")
    if st.button("Sync Log"):
        st.session_state.journal_logs.append({"Date": str(now.date()), "Mood": mood, "Note": note})
        check_level_up(15)
        st.rerun()

elif menu == "⚙️ Core":
    st.markdown("<h2 class='neon-text'>System Settings</h2>", unsafe_allow_html=True)
    st.session_state.user_name = st.text_input("Pilot Name", value=st.session_state.user_name)
    st.session_state.currency = st.text_input("Currency Unit", value=st.session_state.currency)
    if st.button("Update Core Settings"):
        save_user_data(current_user_id)
        st.success("Settings Synced to Cloud.")
