import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 
import time
import random
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM (SB SE PEHLAY) ---
def check_password():
    """Returns `True` if the user had a correct password."""
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Password foran delete karo memory se
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs
        st.text_input("Username (Email)", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show inputs again + error
        st.text_input("Username (Email)", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct
        return True

# --- 1. SETUP PAGE & AUTH ---
st.set_page_config(page_title="Life OS Pro", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# 🛑 YAHAN RUKO: Agar password ghalat hay to agay mat barho
if not check_password():
    st.stop()

# --- LOGIN SUCCESSFUL ---
current_user_id = st.session_state["username"]

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

# --- 3. DATA FUNCTIONS ---
def load_user_data(user_id):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except:
        return None

def save_user_data(user_id):
    try:
        data = {
            "goals": st.session_state.goals,
            "habits": st.session_state.habits,
            "balance": st.session_state.balance,
            "transactions": st.session_state.transactions,
            "water": st.session_state.water,
            "xp": st.session_state.xp,
            "level": st.session_state.level,
            "user_name": st.session_state.user_name,
            "currency": st.session_state.currency,
            "timezone": st.session_state.timezone,
            "journal_logs": st.session_state.journal_logs
        }
        db.collection("users").document(user_id).set(data)
    except:
        pass

# --- 4. STATE INITIALIZATION ---
if 'data_loaded' not in st.session_state:
    saved_data = load_user_data(current_user_id)
    if saved_data:
        st.toast(f"Welcome back, {saved_data.get('user_name')}! ☁️")
        if 'user_name' not in st.session_state: st.session_state.user_name = saved_data.get("user_name", "Boss")
        if 'xp' not in st.session_state: st.session_state.xp = saved_data.get("xp", 0)
        if 'level' not in st.session_state: st.session_state.level = saved_data.get("level", 1)
        if 'balance' not in st.session_state: st.session_state.balance = saved_data.get("balance", 0)
        if 'water' not in st.session_state: st.session_state.water = saved_data.get("water", 0)
        if 'transactions' not in st.session_state: st.session_state.transactions = saved_data.get("transactions", [])
        if 'goals' not in st.session_state: st.session_state.goals = saved_data.get("goals", [])
        if 'habits' not in st.session_state: st.session_state.habits = saved_data.get("habits", [])
        if 'currency' not in st.session_state: st.session_state.currency = saved_data.get("currency", "PKR")
        if 'journal_logs' not in st.session_state: st.session_state.journal_logs = saved_data.get("journal_logs", [])
        if 'timezone' not in st.session_state: st.session_state.timezone = saved_data.get("timezone", "Asia/Karachi")
    else:
        # Defaults for NEW USER
        if 'user_name' not in st.session_state: st.session_state.user_name = "New User"
        if 'xp' not in st.session_state: st.session_state.xp = 0
        if 'level' not in st.session_state: st.session_state.level = 1
        if 'balance' not in st.session_state: st.session_state.balance = 0
        if 'water' not in st.session_state: st.session_state.water = 0
        if 'transactions' not in st.session_state: st.session_state.transactions = []
        if 'goals' not in st.session_state: st.session_state.goals = [{"text": "Mission 1", "done": False}]
        if 'habits' not in st.session_state: st.session_state.habits = [{"name": "Exercise", "streak": 0}]
        if 'currency' not in st.session_state: st.session_state.currency = "PKR"
        if 'journal_logs' not in st.session_state: st.session_state.journal_logs = []
        if 'timezone' not in st.session_state: st.session_state.timezone = "Asia/Karachi"
    st.session_state.data_loaded = True

if 'run_effect' not in st.session_state: st.session_state.run_effect = None

# --- 5. UI & HELPERS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
.stApp { background-color: #0E1117; }
.card { background-color: #1A1C24; padding: 15px; border-radius: 15px; border: 1px solid #333; margin-bottom: 15px; }
.neon-text { font-size: 32px; font-weight: 800; color: #fff; text-shadow: 0 0 10px rgba(0, 255, 127, 0.5); }
.stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: 600; }
.clock-box {
    text-align: center; padding: 15px;
    background: radial-gradient(circle, #222 0%, #000 100%);
    border-radius: 15px; border: 1px solid #FF1493;
    box-shadow: 0 0 15px rgba(255, 20, 147, 0.3); margin-bottom: 20px;
}
.time-font { font-size: 42px; font-weight: 900; color: #FFF; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

def play_sound_and_wait(sound_type="pop"):
    vibrate_js = """<script>if(navigator.vibrate){navigator.vibrate([200]);}</script>"""
    components.html(vibrate_js, height=0, width=0)
    sounds = {
        "win": "https://www.soundjay.com/misc/sounds/magic-chime-01.mp3",
        "cash": "https://www.soundjay.com/misc/sounds/coins-in-hand-2.mp3",
        "pop": "https://www.soundjay.com/buttons/sounds/button-09.mp3",
        "levelup": "https://www.soundjay.com/human/sounds/applause-01.mp3"
    }
    url = sounds.get(sound_type, sounds["pop"])
    st.markdown(f"""<audio autoplay="true" style="display:none;"><source src="{url}" type="audio/mp3"></audio>""", unsafe_allow_html=True)
    time.sleep(0.5)

def check_level_up():
    req_xp = st.session_state.level * 100 
    if st.session_state.xp >= req_xp:
        st.session_state.level += 1
        st.session_state.xp = 0 
        play_sound_and_wait("levelup")
        st.session_state.run_effect = "balloons"
        st.toast(f"🎉 LEVEL UP! You are now Level {st.session_state.level}!", icon="🆙")
    save_user_data(current_user_id)

# Effect Runner
if st.session_state.run_effect == "balloons":
    st.balloons()
    st.session_state.run_effect = None
elif st.session_state.run_effect == "snow":
    st.snow()
    st.session_state.run_effect = None

# --- 6. MAIN NAVIGATION ---
try: tz = pytz.timezone(st.session_state.timezone)
except: tz = pytz.timezone('Asia/Karachi')
pk_time = datetime.now(tz)

with st.sidebar:
    st.title(f"🚀 {st.session_state.user_name}")
    st.caption(f"Lvl {st.session_state.level} • {st.session_state.xp} XP")
    st.progress(st.session_state.xp / (st.session_state.level * 100))
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()
    st.write("---")
    menu = st.
