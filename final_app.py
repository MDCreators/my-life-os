import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 
import time
import random

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Life OS Pro", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. AUTO-FIXER (PREVENTS CRASHES) ---
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

# --- 3. NOTIFICATION SYSTEM ---
def inject_notification_system():
    # Browser Notification Logic
    js = """
    <script>
    if (!("Notification" in window)) {
        console.log("Not supported");
    } else {
        Notification.requestPermission();
    }
    </script>
    """
    components.html(js, height=0, width=0)

# --- 4. SOUND SYSTEM ---
def play_sound_and_wait(sound_type="pop"):
    # Vibration
    vcode = """<script>if(navigator.vibrate){navigator.vibrate([200]);}</script>"""
    components.html(vcode, height=0, width=0)
    
    # Sounds
    sounds = {
        "win": "https://www.soundjay.com/misc/sounds/magic-chime-01.mp3",
        "cash": "https://www.soundjay.com/misc/sounds/coins-in-hand-2.mp3",
        "pop": "https://www.soundjay.com/buttons/sounds/button-09.mp3",
        "levelup": "https://www.soundjay.com/human/sounds/applause-01.mp3"
    }
    url = sounds.get(sound_type, sounds["pop"])
    
    # Audio Player
    st.markdown(f"""
    <audio autoplay="true" style="display:none;">
    <source src="{url}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)
    time.sleep(0.8)

# --- 5. STATE INIT ---
if 'user_name' not in st.session_state: st.session_state.user_name = "Boss"
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'level' not in st.session_state: st.session_state.level = 1
if 'balance' not in st.session_state: st.session_state.balance = 0
if 'water' not in st.session_state: st.session_state.water = 0
if 'transactions' not in st.session_state: st.session_state.transactions = []
if 'currency' not in st.session_state: st.session_state.currency = "PKR"
if 'timezone' not in st.session_state: st.session_state.timezone = "Asia/Karachi"
if 'notifications' not in st.session_state: st.session_state.notifications = True

# --- LEVEL UP ---
def check_level_up():
    req_xp = st.session_state.level * 100 
    if st.session_state.xp >= req_xp:
        st.session_state.level += 1
        st.session_state.xp = 0 
        play_sound_and_wait("levelup")
        st.balloons()

# --- 6. LOGIN ---
def check_auth():
    if "auth" not in st.session_state:
        try: users = st.secrets["users"]
        except: 
            st.warning("⚠️ Add [users] to Secrets")
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

# --- 7. MAIN APP ---
if check_auth():
    
    # Notifications
    if st.session_state.notifications:
        inject_notification_system()

    # CSS Styles
    st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .card { background-color: #1E1E1E; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; height: 45px; }
    
    /* GIANT CLOCK */
    .clock-container {
        text-align: center; padding: 20px;
        background: radial-gradient(circle, #222 0%, #000 100%);
        border-radius: 15px; border: 2px solid #FF1493;
        box-shadow: 0 0 20px rgba(255, 20, 147, 0.4); margin-bottom: 20px;
    }
    .time-text { font-size: 50px; font-weight: 900; color: #FFF; font-family: monospace; }
    .date-text { font-size: 16px; color: #AAA; }
    </style>
    """, unsafe_allow_html=True)

    # Time Setup
    try: tz = pytz.timezone(st.session_state.timezone)
    except: tz = pytz.timezone('Asia/Karachi')
    pk_time = datetime.now(tz)
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user_name}")
        
        # Level Badge
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #FF1493, #9d00ff); padding: 15px; border-radius: 10px; text-align: center;">
            <h3 style="margin:0; color:white;">Lvl {st.session_state.level}</h3>
            <p style="margin:0; color:white;">{st.session_state.xp} / {st.session_state.level * 100} XP</p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(st.session_state.xp / (st.session_state.level * 100))
        
        st.write("---")
        menu = st.radio("Menu", ["📊 Dashboard", "🎯 Focus", "💰 Wallet", "💪 Habits", "⚙️ Settings"])

    # === DASHBOARD ===
    if menu == "📊 Dashboard":
        # Clock
        t_str = pk_time.strftime('%I:%M %p')
        d_str = pk_time.strftime('%A, %d %B')
        st.markdown(f"""
        <div class="clock-container">
            <div class="time-text">{t_str}</div>
            <div class="date-text">{d_str}</div>
        </div>
        """, unsafe_allow_html=True)

        # Greeting
        hr = pk_time.hour
        greet = "Morning" if 5<=hr<12 else "Afternoon" if 12<=hr<17 else "Evening" if 17<=hr<21 else "Night"
        st.markdown(f"### Good {greet}, Boss! 👋")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='card'><h6>💰 Savings</h6><h3>{st.session_state.currency} {st.session_state.balance}</h3></div>", unsafe_allow_html=True)
        with c2:
            pending = sum(1 for g in st.session_state.goals if not g['done'])
            st.markdown(f"<div class='card'><h6>🎯 Pending</h6><h3>{pending} Goals</h3></div>", unsafe_allow_html=True)
        
        if st.button("🔔 Test Alert"):
            st.components.v1.html("""<script>new Notification("⚡ Life OS", { body: "Test Successful!" });</script>""", height=0, width=0)
            st.toast("Check Notification!")

    # === FOCUS ===
    elif menu == "🎯 Focus":
        st.title("Daily Missions 🎯")
        
        # Goals
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
        
        # Pomodoro (FIXED SECTION)
        with st.expander("🍅 Pomodoro Timer"):
            c_t1, c_t2, c_t3 = st.columns(3)
            with c_t2:
                if st.button("▶ Start 25 Mins"):
                    timer_placeholder = st.empty() # SAFE METHOD
                    for seconds in range(1500, 0, -1):
                        mins, secs = divmod(seconds, 60)
                        timer_placeholder.metric("Focus Time", f"{mins:02d}:{secs:02d}")
                        time.sleep(1)
                    st.success("Time's Up! Take a break.")
                    play_sound_and_wait("win")

    # === WALLET ===
    elif menu == "💰 Wallet":
        curr = st.session_state.currency
        st.title(f"Wallet ({curr}) 💸")
        
        val = st.session_state.balance
        clr = "#00FF00" if val >= 0 else "#FF0000"
        st.markdown(f"<div style='text-align:center; padding:10px; background:#111; border-radius:10px;'><h1 style='color:{clr}; margin:0;'>{curr} {val}</h1></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Add", "Stats"])
        with tab1:
            with st.form("money"):
                item = st.text_input("Item")
                c_amt, c_cat = st.columns(2)
                amt = c_amt.number_input("Amount", min_value=1)
                cat = c_cat.selectbox("Cat", ["Food", "Rent", "Fuel", "Shopping", "Salary", "Biz"])
                typ = st.radio("Type", ["Expense 🔴", "Income 🟢"], horizontal=True)
                
                if st.form_submit_button("Save"):
                    real_amt = amt if "Income" in typ else -amt
                    st.session_state.balance += real_amt
                    st.session_state.transactions.append({
                        "Date": str(pk_time.date()), "Item": item, "Amt": abs(amt), 
                        "Type": "Expense" if "Expense" in typ else "Income", "Cat": cat
                    })
                    st.session_state.xp += 10
                    check_level_up()
                    play_sound_and_wait("cash")
                    st.rerun()
        with tab2:
            if st.session_state.transactions:
                df = pd.DataFrame(st.session_state.transactions)
                st.dataframe(df, use_container_width=True)
                df_ex = df[df["Type"] == "Expense"]
                if not df_ex.empty:
                    fig = px.pie(df_ex, values='Amt', names='Cat', title="Expenses", hole=0.5)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data.")

    # === HABITS ===
    elif menu == "💪 Habits":
        st.title("Habits & Water 🌱")
        
        st.markdown("<div class='card'><h4>💧 Water</h4>", unsafe_allow_html=True)
        cols = st.columns(4)
        for i in range(4):
             if cols[i].button(f"{'🟦' if st.session_state.water > i else '⬜'}", key=f"w1_{i}"):
                 if st.session_state.water <= i:
                     st.session_state.water += 1
                     play_sound_and_wait("pop")
                     st.rerun()
        cols2 = st.columns(4)
        for i in range(4):
             if cols2[i].button(f"{'🟦' if st.session_state.water > i+4 else '⬜'}", key=f"w2_{i}"):
                 if st.session_state.water <= i+4:
                     st.session_state.water += 1
                     play_sound_and_wait("pop")
                     st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h4>🔥 Streaks</h4>", unsafe_allow_html=True)
        nh = st.text_input("New Habit", placeholder="Type & Enter")
        if st.button("Add"):
            if nh:
                st.session_state.habits.append({"name": nh, "streak": 0})
                st.rerun()
                
        for i, h in enumerate(st.session_state.habits):
            c_x, c_y, c_z = st.columns([4, 2, 2])
            c_x.write(f"**{h['name']}**")
            c_y.write(f"🔥 {h['streak']}")
            if c_z.button("✅", key=f"h_{i}"):
                st.session_state.habits[i]['streak'] += 1
                st.session_state.xp += 15
                check_level_up()
                play_sound_and_wait("pop")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # === SETTINGS ===
    elif menu == "⚙️ Settings":
        st.title("Settings ⚙️")
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        notif = st.toggle("Browser Notifications", value=st.session_state.notifications)
        if notif != st.session_state.notifications:
            st.session_state.notifications = notif
            st.rerun()
            
        new_curr = st.text_input("Currency", value=st.session_state.currency)
        if st.button("Save Currency"):
            st.session_state.currency = new_curr
            st.rerun()
            
        st.write("---")
        tz_list = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"]
        new_tz = st.selectbox("Timezone", tz_list, index=0)
        if st.button("Save Timezone"):
            st.session_state.timezone = new_tz
            st.rerun()
            
        st.write("---")
        new_n = st.text_input("Name", value=st.session_state.user_name)
        if st.button("Update Name"):
            st.session_state.user_name = new_n
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("🔴 Reset App"):
            st.session_state.clear()
            st.rerun()
