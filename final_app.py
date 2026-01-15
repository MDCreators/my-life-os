import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 
import time
import random

# --- 1. PRO CONFIGURATION ---
st.set_page_config(
    page_title="Life OS Pro", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🛠️ AUTO-FIXER (CRITICAL) ---
if 'goals' in st.session_state:
    fixed_goals = []
    for g in st.session_state.goals:
        t = g.get('txt', g.get('text', 'New Goal'))
        d = g.get('done', False)
        fixed_goals.append({'text': t, 'done': d})
    st.session_state.goals = fixed_goals

if 'habits' in st.session_state:
    fixed_habits = []
    for h in st.session_state.habits:
        n = h.get('name', 'Habit')
        s = h.get('s', h.get('streak', 0))
        fixed_habits.append({'name': n, 'streak': s})
    st.session_state.habits = fixed_habits

# --- 🔔 REAL BROWSER NOTIFICATIONS (THE HACK) ---
# Ye script browser se permission le ga aur har 30 min baad alert bhejega
def inject_notification_system():
    js = """
    <script>
    // 1. Request Permission on Load
    if (!("Notification" in window)) {
        console.log("This browser does not support desktop notification");
    } else {
        Notification.requestPermission();
    }

    // 2. Notification Sender Function
    function sendNotification(msg) {
        if (Notification.permission === "granted") {
            var notification = new Notification("⚡ Life OS Alert", {
                body: msg,
                icon: "https://cdn-icons-png.flaticon.com/512/2913/2913584.png"
            });
        }
    }

    // 3. Timer Loop (Checks every 20 minutes)
    // Note: Streamlit reloads often, so we use a simpler interval for demo
    // setInterval(() => { sendNotification("💧 Pani peena mat bhoolna!"); }, 1200000); 
    
    // Test Notification (Runs once on load to show it works)
    // setTimeout(() => { sendNotification("🚀 Welcome back Boss! Focus Mode On."); }, 3000);
    </script>
    """
    components.html(js, height=0, width=0)

# --- 🎵 SOUND SYSTEM ---
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
    st.markdown(f"""
    <audio autoplay="true" style="display:none;">
    <source src="{url}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)
    time.sleep(0.8)

# --- STATE MANAGEMENT ---
if 'user_name' not in st.session_state: st.session_state.user_name = "Boss"
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'level' not in st.session_state: st.session_state.level = 1
if 'balance' not in st.session_state: st.session_state.balance = 0
if 'water' not in st.session_state: st.session_state.water = 0
if 'transactions' not in st.session_state: st.session_state.transactions = []
if 'currency' not in st.session_state: st.session_state.currency = "PKR"
if 'timezone' not in st.session_state: st.session_state.timezone = "Asia/Karachi"
if 'notifications' not in st.session_state: st.session_state.notifications = True

# --- LEVEL LOGIC ---
def check_level_up():
    req_xp = st.session_state.level * 100 
    if st.session_state.xp >= req_xp:
        st.session_state.level += 1
        st.session_state.xp = 0 
        play_sound_and_wait("levelup")
        st.balloons()

# --- LOGIN ---
def check_auth():
    if "auth" not in st.session_state:
        try: users = st.secrets["users"]
        except: 
            st.warning("⚠️ Setup Secrets")
            return False
        
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("## ⚡ Life OS Pro")
            with st.form("Log"):
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if e in users and users[e] == p:
                        st.session_state.auth = True
                        st.rerun()
                    else: st.error("Access Denied")
        return False
    return True

# --- APP ---
if check_auth():
    
    # Run Notification Script
    if st.session_state.notifications:
        inject_notification_system()

    # CSS for Giant Clock & Mobile
    st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .card { background-color: #1E1E1E; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; height: 45px; }
    
    /* ⏰ GIANT CLOCK STYLE */
    .clock-container {
        text-align: center;
        padding: 20px;
        background: radial-gradient(circle, #222 0%, #000 100%);
        border-radius: 15px;
        border: 2px solid #FF1493;
        box-shadow: 0 0 20px rgba(255, 20, 147, 0.4);
        margin-bottom: 20px;
    }
    .time-text {
        font-size: 60px;
        font-weight: 900;
        color: #FFF;
        text-shadow: 0 0 10px #FF1493;
        font-family: 'Courier New', monospace;
        line-height: 1;
    }
    .date-text {
        font-size: 18px;
        color: #AAA;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Time Logic
    try: tz = pytz.timezone(st.session_state.timezone)
    except: tz = pytz.timezone('Asia/Karachi')
    pk_time = datetime.now(tz)
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user_name}")
        
        # Level Widget
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #FF1493, #9d00ff); padding: 15px; border-radius: 10px; text-align: center;">
            <h2 style="margin:0; color:white;">Lvl {st.session_state.level}</h2>
            <p style="margin:0; color:white;">{st.session_state.xp} / {st.session_state.level * 100} XP</p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(st.session_state.xp / (st.session_state.level * 100))
        
        st.write("---")
        menu = st.radio("Navigate", ["📊 Dashboard", "🎯 Focus", "💰 Wallet", "💪 Habits", "⚙️ Settings"])

    # ==========================
    # 1. 📊 DASHBOARD (With Giant Clock)
    # ==========================
    if menu == "📊 Dashboard":
        # ⏰ GIANT PROMINENT CLOCK
        t_str = pk_time.strftime('%I:%M %p')
        d_str = pk_time.strftime('%A, %d %B')
        st.markdown(f"""
        <div class="clock-container">
            <div class="time-text">{t_str}</div>
            <div class="date-text">{d_str}</div>
        </div>
        """, unsafe_allow_html=True)

        # Summary Grid
        hr = pk_time.hour
        greet = "Morning" if 5<=hr<12 else "Afternoon" if 12<=hr<17 else "Evening" if 17<=hr<21 else "Night"
        st.markdown(f"### Good {greet}, Boss! 👋")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='card'><h6>💰 Savings</h6><div style='font-size:24px; color:#4CAF50;'>{st.session_state.currency} {st.session_state.balance}</div></div>", unsafe_allow_html=True)
        with c2:
            pending = sum(1 for g in st.session_state.goals if not g['done'])
            st.markdown(f"<div class='card'><h6>🎯 Pending</h6><div style='font-size:24px; color:#FF5722;'>{pending} Goals</div></div>", unsafe_allow_html=True)
        
        # Notification Trigger Button (Manual Check)
        if st.button("🔔 Test Notification"):
            # JavaScript Injection to trigger alert
            st.components.v1.html("""<script>
            new Notification("⚡ Life OS Test", { body: "This is how alerts will look!", icon: "https://cdn-icons-png.flaticon.com/512/2913/2913584.png" });
            </script>""", height=0, width=0)
            st.toast("Notification Sent! (Check Status Bar)")

    # ==========================
    # 2. 🎯 FOCUS
    # ==========================
    elif menu == "🎯 Focus":
        st.title("Daily Missions 🎯")
        
        done_c = sum(1 for g in st.session_state.goals if g['done'])
        total_c = len(st.session_state.goals)
        if total_c > 0: st.progress(done_c/total_c)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for i, g in enumerate(st.session_state.goals):
            c1, c2 = st.columns([1, 6])
            with c1:
                chk = st.checkbox("", value=g['done'], key=f"g{i}")
                if chk != g['done']:
                    st.session_state.goals[i]['done'] = chk
                    if chk:
                        st.session_state.xp += 20
                        check_level_up()
                        play_sound_and_wait("win")
                        st.rerun()
            with c2:
                st.session_state.goals[i]['text'] = st.text_input(f"g_t{i}", g['text'], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("🍅 Pomodoro Timer"):
            c_t1, c_t2, c_t3 = st.columns(3)
            with c_t2:
                if st.button("▶ Start 25 Mins"):
                    with st.empty
