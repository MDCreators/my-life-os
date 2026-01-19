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

# --- 0. LOGIN SYSTEM (FIXED) ---
def check_password():
    """Returns `True` if the user had a correct password."""
    
    def password_entered():
        # Check if password matches
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            
            st.session_state["password_correct"] = True
            # 🔴 CRITICAL FIX: Username ko permanent variable mein save karna
            st.session_state["logged_in_user"] = st.session_state["username"]
            
            del st.session_state["password"]  # Password memory se delete
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

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="Life OS Pro", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

if not check_password():
    st.stop()

# Ab hum "username" ki bajaye "logged_in_user" use karenge jo delete nahi hoga
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
        # Defaults
        if 'user_name' not in st.session_state: st.session_state.user_name = "New User"
        if 'xp' not in st.session_state: st.session_state.xp = 0
        if 'level' not in st.session_state: st.session_state.level = 1
        if 'balance' not in st.session_state: st.session_state.balance = 0
        if 'water' not in st.session_state: st.session_state.water = 0
        if 'transactions' not in st.session_state: st.session_state.transactions = []
        if 'goals' not in st.session_state: st.session_state.goals = [{"text": "First Mission", "done": False}]
        if 'habits' not in st.session_state: st.session_state.habits = [{"name": "Exercise", "streak": 0}]
        if 'currency' not in st.session_state: st.session_state.currency = "PKR"
        if 'journal_logs' not in st.session_state: st.session_state.journal_logs = []
        if 'timezone' not in st.session_state: st.session_state.timezone = "Asia/Karachi"
    st.session_state.data_loaded = True

if 'run_effect' not in st.session_state: st.session_state.run_effect = None

# --- 5. UI STYLES & HELPERS ---
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
    menu = st.radio("Navigate", ["📊 Dashboard", "🎯 Focus", "💰 Wallet", "💪 Habits", "📝 Journal", "⚙️ Settings"])

# === DASHBOARD ===
if menu == "📊 Dashboard":
    t_str = pk_time.strftime('%I:%M %p')
    d_str = pk_time.strftime('%A, %d %B')
    st.markdown(f"""<div class="clock-box"><div class="time-font">{t_str}</div><div style="color:#AAA;">{d_str}</div></div>""", unsafe_allow_html=True)
    
    hr = pk_time.hour
    greet = "Morning" if 5<=hr<12 else "Afternoon" if 12<=hr<17 else "Evening" if 17<=hr<21 else "Night"
    st.markdown(f"### Good {greet}! 👋")
    st.info(f"💡 {random.choice(['Focus on the process.', 'Discipline is freedom.', 'Keep grinding.'])}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='card'><h5>💰 Balance</h5><div class='neon-text' style='color:#00FF7F;'>{st.session_state.currency} {st.session_state.balance}</div></div>", unsafe_allow_html=True)
    with c2:
        pending = sum(1 for g in st.session_state.goals if not g.get('done', False))
        st.markdown(f"<div class='card'><h5>🎯 Pending</h5><div class='neon-text' style='color:#FF4500;'>{pending}</div></div>", unsafe_allow_html=True)

# === FOCUS ===
elif menu == "🎯 Focus":
    st.title("Missions 🎯")
    with st.expander("➕ Add Goal", expanded=False):
        new_g = st.text_input("Goal Name")
        if st.button("Add"):
            if new_g:
                st.session_state.goals.append({'text': new_g, 'done': False})
                save_user_data(current_user_id)
                st.rerun()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if st.session_state.goals:
        for i, g in enumerate(st.session_state.goals):
            c1, c2, c3 = st.columns([1, 6, 1])
            with c1:
                chk = st.checkbox("", value=g.get('done', False), key=f"g_chk_{i}")
                if chk != g.get('done', False):
                    st.session_state.goals[i]['done'] = chk
                    if chk:
                        st.session_state.xp += 20
                        check_level_up()
                        play_sound_and_wait("win")
                        st.session_state.run_effect = "balloons"
                    save_user_data(current_user_id)
                    st.rerun()
            with c2:
                st.session_state.goals[i]['text'] = st.text_input(f"g_t{i}", g.get('text',''), label_visibility="collapsed")
            with c3:
                if st.button("🗑️", key=f"del_g{i}"):
                    st.session_state.goals.pop(i)
                    save_user_data(current_user_id)
                    st.rerun()
    else: st.info("No goals.")
    st.markdown("</div>", unsafe_allow_html=True)

# === WALLET (UPDATED WITH EMOJIS) ===
elif menu == "💰 Wallet":
    curr = st.session_state.currency
    val = st.session_state.balance
    color = "#00FF7F" if val >= 0 else "#FF4500"
    st.markdown(f"<div class='card' style='text-align:center;'><h5 style='margin:0;'>Balance</h5><h1 style='color:{color}; font-size:42px; margin:0;'>{curr} {val}</h1></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Add", "History", "Charts"])
    with tab1:
        typ = st.radio("Type", ["Expense 🔴", "Income 🟢"], horizontal=True)
        with st.form("money"):
            # --- EMOJI CATEGORIES ADDED ---
            if "Income" in typ:
                cats = ["Salary 💰", "Freelance 💻", "Business 📈", "Gift 🎁", "Investments 📊", "Allowance 💵", "Other ➕"]
            else:
                cats = ["Food 🍔", "Rent 🏠", "Fuel ⛽", "Shopping 🛍️", "Bills 💡", "Fun 🎉", "Education 📚", "Health 🏥", "Travel ✈️", "Charity 🤝", "Other 💸"]
            
            cat = st.selectbox("Category", cats)
            item = st.text_input("Description")
            amt = st.number_input("Amount", min_value=1)
            
            if st.form_submit_button("Save"):
                real_amt = amt if "Income" in typ else -amt
                st.session_state.balance += real_amt
                st.session_state.transactions.append({
                    "Date": str(pk_time.date()), "Item": item, "Amt": abs(amt), "Type": "Expense" if "Expense" in typ else "Income", "Cat": cat
                })
                st.session_state.xp += 10
                check_level_up()
                play_sound_and_wait("cash")
                st.session_state.run_effect = "snow"
                save_user_data(current_user_id)
                st.rerun()
    
    with tab2:
        if st.session_state.transactions: st.dataframe(pd.DataFrame(st.session_state.transactions[::-1]), use_container_width=True)
        else: st.info("No history.")
    with tab3:
        if st.session_state.transactions:
            df = pd.DataFrame(st.session_state.transactions)
            df_ex = df[df["Type"] == "Expense"]
            if not df_ex.empty: st.plotly_chart(px.pie(df_ex, values='Amt', names='Cat', title="Expenses", hole=0.5), use_container_width=True)
        else: st.info("No data.")

# === HABITS ===
elif menu == "💪 Habits":
    st.title("Habits 🌱")
    st.markdown("<div class='card'><h4>💧 Hydration</h4>", unsafe_allow_html=True)
    st.progress(min(st.session_state.water / 8, 1.0))
    st.caption(f"{st.session_state.water}/8 Glasses")
    c1, c2 = st.columns([1, 4])
    if c1.button("➕ Drink"):
        if st.session_state.water < 8:
            st.session_state.water += 1
            play_sound_and_wait("pop")
            st.session_state.run_effect = "snow"
            save_user_data(current_user_id)
            st.rerun()
    if c2.button("➖ Undo"):
        if st.session_state.water > 0:
            st.session_state.water -= 1
            save_user_data(current_user_id)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'><h4>🔥 Streaks</h4>", unsafe_allow_html=True)
    c_in, c_btn = st.columns([3, 1])
    nh = c_in.text_input("New Habit", label_visibility="collapsed")
    if c_btn.button("Add"):
        if nh:
            st.session_state.habits.append({"name": nh, "streak": 0})
            save_user_data(current_user_id)
            st.rerun()
            
    if st.session_state.habits:
        for i, h in enumerate(st.session_state.habits):
            c_x, c_y, c_z, c_del = st.columns([3, 1, 1, 0.5])
            c_x.markdown(f"**{h.get('name','Habit')}**")
            c_y.metric("Streak", f"{h.get('streak',0)} 🔥")
            if c_z.button("Done", key=f"h_d_{i}"):
                st.session_state.habits[i]['streak'] += 1
                st.session_state.xp += 15
                check_level_up()
                play_sound_and_wait("pop")
                st.session_state.run_effect = "snow"
                save_user_data(current_user_id)
                st.rerun()
            if c_del.button("x", key=f"del_h{i}"):
                st.session_state.habits.pop(i)
                save_user_data(current_user_id)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === JOURNAL ===
elif menu == "📝 Journal":
    st.title("Journal 📔")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    c_m, c_s = st.columns(2)
    mood = c_m.selectbox("Mood", ["Happy 🙂", "Calm 😌", "Stressed 😫", "Sad 😢"])
    sleep = c_s.selectbox("Sleep", ["8+ Hours 💤", "6-7 Hours", "4-5 Hours", "Less than 4"])
    gratitude = st.text_area("Gratitude", placeholder="I am grateful for...")
    
    if st.button("Save Entry"):
        entry = {"Date": str(pk_time.date()), "Mood": mood, "Sleep": sleep, "Gratitude": gratitude}
        st.session_state.journal_logs.append(entry)
        st.session_state.xp += 5
        check_level_up()
        play_sound_and_wait("win")
        st.session_state.run_effect = "balloons"
        save_user_data(current_user_id)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.journal_logs:
        st.write("### Past Entries")
        st.dataframe(pd.DataFrame(st.session_state.journal_logs[::-1]), use_container_width=True)

# === SETTINGS ===
elif menu == "⚙️ Settings":
    st.title("Settings")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    new_n = st.text_input("Display Name", value=st.session_state.user_name)
    if st.button("Update Name"):
        st.session_state.user_name = new_n
        save_user_data(current_user_id)
        st.rerun()
        
    new_curr = st.text_input("Currency", value=st.session_state.currency)
    if st.button("Save Currency"):
        st.session_state.currency = new_curr
        save_user_data(current_user_id)
        st.rerun()
        
    tz_list = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"]
    new_tz = st.selectbox("Timezone", tz_list, index=0)
    if st.button("Save Timezone"):
        st.session_state.timezone = new_tz
        save_user_data(current_user_id)
        st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("🔴 Reset Data (Clear Cloud)"):
        st.session_state.clear()
        save_user_data(current_user_id)
        st.rerun()

