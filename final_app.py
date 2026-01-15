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
    layout="wide", # Full Screen Layout
    initial_sidebar_state="expanded"
)

# --- 🎵 SOUND & VIBRATION ---
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
    
    # Audio Player
    st.markdown(f"""
    <audio autoplay="true" style="display:none;">
    <source src="{url}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)
    
    time.sleep(1.2) # Wait for sound

# --- STATE MANAGEMENT ---
if 'user_name' not in st.session_state: st.session_state.user_name = "Boss"
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'level' not in st.session_state: st.session_state.level = 1
if 'balance' not in st.session_state: st.session_state.balance = 0
if 'water' not in st.session_state: st.session_state.water = 0
if 'goals' not in st.session_state: 
    st.session_state.goals = [{"txt": "Deep Work (2 Hours)", "done": False}, {"txt": "Read 10 Pages", "done": False}, {"txt": "No Sugar", "done": False}]
if 'habits' not in st.session_state: st.session_state.habits = [{"name": "Gym", "s": 0}]
if 'transactions' not in st.session_state: st.session_state.transactions = []

# --- LEVEL SYSTEM LOGIC ---
def check_level_up():
    # Formula: Level barhnay ke liye har baar 100 XP zyada chahiye
    req_xp = st.session_state.level * 100 
    if st.session_state.xp >= req_xp:
        st.session_state.level += 1
        st.session_state.xp = 0 # XP Reset for next level
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
            st.markdown("## ⚡ Life OS Pro Login")
            with st.form("Log"):
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Access Dashboard"):
                    if e in users and users[e] == p:
                        st.session_state.auth = True
                        st.rerun()
                    else: st.error("Access Denied")
        return False
    return True

# --- APP START ---
if check_auth():
    
    # Custom CSS for Modern Look
    st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .card { background-color: #1E1E1E; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
    .big-stat { font-size: 32px; font-weight: bold; color: #4CAF50; }
    .stProgress > div > div > div > div { background-color: #00CCFF; }
    </style>
    """, unsafe_allow_html=True)

    pk_time = datetime.now(pytz.timezone('Asia/Karachi'))
    
    # --- SIDEBAR (NAVIGATION) ---
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user_name}")
        
        # Level Card
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #FF1493, #9d00ff); padding: 15px; border-radius: 10px; text-align: center;">
            <h2 style="margin:0; color:white;">Lvl {st.session_state.level}</h2>
            <p style="margin:0; color:white;">{st.session_state.xp} / {st.session_state.level * 100} XP</p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(st.session_state.xp / (st.session_state.level * 100))
        
        st.write("---")
        menu = st.radio("Navigate", ["📊 Dashboard", "🎯 Focus & Goals", "💰 Wallet Pro", "💪 Habits & Health", "⚙️ Settings"])
        
        st.write("---")
        st.caption(f"🕒 {pk_time.strftime('%I:%M %p')}")

    # ==========================
    # 1. 📊 DASHBOARD (Summary)
    # ==========================
    if menu == "📊 Dashboard":
        st.title("Good Day, Boss! 👋")
        
        # 3 Big Cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='card'><h3>💰 Savings</h3><div class='big-stat'>PKR {st.session_state.balance}</div></div>", unsafe_allow_html=True)
        with c2:
            pending = sum(1 for g in st.session_state.goals if not g['done'])
            st.markdown(f"<div class='card'><h3>🎯 Pending</h3><div class='big-stat'>{pending} Goals</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='card'><h3>💧 Water</h3><div class='big-stat'>{st.session_state.water}/8</div></div>", unsafe_allow_html=True)

        # Quick Motivational Quote
        quotes = ["Focus on the process, not the outcome.", "Discipline is freedom.", "One day or Day one? You decide."]
        st.info(f"💡 Quote: {random.choice(quotes)}")

    # ==========================
    # 2. 🎯 FOCUS & GOALS (With Timer)
    # ==========================
    elif menu == "🎯 Focus & Goals":
        st.title("Productivity Zone 🧠")
        
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.subheader("Daily Missions")
            # Progress Bar
            done_c = sum(1 for g in st.session_state.goals if g['done'])
            total_c = len(st.session_state.goals)
            if total_c > 0: st.progress(done_c/total_c)
            
            for i, g in enumerate(st.session_state.goals):
                cc1, cc2 = st.columns([1, 8])
                with cc1:
                    chk = st.checkbox("", value=g['done'], key=f"g{i}")
                    if chk != g['done']:
                        st.session_state.goals[i]['done'] = chk
                        if chk:
                            st.session_state.xp += 20
                            check_level_up()
                            play_sound_and_wait("win")
                            st.rerun()
                with cc2:
                    st.session_state.goals[i]['txt'] = st.text_input(f"g_t{i}", g['txt'], label_visibility="collapsed")
        
        with c_right:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("🍅 Pomodoro Timer")
            st.caption("25 Mins Focus")
            if st.button("Start Timer"):
                with st.empty():
                    for seconds in range(1500, 0, -1):
                        mins, secs = divmod(seconds, 60)
                        st.metric("Time Left", f"{mins:02d}:{secs:02d}")
                        time.sleep(1)
                    st.success("Time's Up! Take a break.")
                    play_sound_and_wait("win")
            st.markdown("</div>", unsafe_allow_html=True)

    # ==========================
    # 3. 💰 WALLET PRO (Finance)
    # ==========================
    elif menu == "💰 Wallet Pro":
        st.title("Financial Control 💸")
        
        # Balance Display
        clr = "#00FF00" if st.session_state.balance >= 0 else "#FF0000"
        st.markdown(f"<h1 style='color:{clr};'>PKR {st.session_state.balance}</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["➕ New Transaction", "📈 Analysis"])
        
        with tab1:
            with st.form("money"):
                c1, c2 = st.columns(2)
                item = c1.text_input("Description")
                amt = c2.number_input("Amount", min_value=1)
                cat = c1.selectbox("Category", ["Food", "Transport", "Shopping", "Salary", "Biz", "Other"])
                typ = c2.radio("Type", ["Expense 🔴", "Income 🟢"], horizontal=True)
                
                if st.form_submit_button("Add Record"):
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
                
                # Charts
                c_a, c_b = st.columns(2)
                df_ex = df[df["Type"] == "Expense"]
                if not df_ex.empty:
                    fig = px.pie(df_ex, values='Amt', names='Cat', title="Expenses Breakdown", hole=0.5)
                    c_a.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available.")

    # ==========================
    # 4. 💪 HABITS & HEALTH
    # ==========================
    elif menu == "💪 Habits & Health":
        st.title("Body & Mind 🌱")
        
        c_h1, c_h2 = st.columns(2)
        
        with c_h1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("💧 Hydration")
            cols = st.columns(4)
            # Smart Water Logic
            clicks = 0
            for i in range(8):
                if i == 4: cols = st.columns(4) # New row
                done = st.session_state.water > i
                if cols[i%4].button(f"{'🟦' if done else '⬜'}", key=f"w_{i}"):
                    if not done: 
                        st.session_state.water += 1
                        st.session_state.xp += 5
                        play_sound_and_wait("pop")
                        st.rerun()
            st.caption(f"Level: {st.session_state.water}/8")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_h2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("🔥 Habit Streaks")
            
            nh = st.text_input("Add Habit", placeholder="e.g., Read Book")
            if st.button("Add"):
                st.session_state.habits.append({"name": nh, "s": 0})
                st.rerun()
                
            for i, h in enumerate(st.session_state.habits):
                c_x, c_y, c_z = st.columns([3, 1, 1])
                c_x.write(f"**{h['name']}**")
                c_y.write(f"🔥 {h['s']}")
                if c_z.button("✅", key=f"h_{i}"):
                    st.session_state.habits[i]['s'] += 1
                    st.session_state.xp += 15
                    check_level_up()
                    play_sound_and_wait("pop")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Journal
        st.write("---")
        st.subheader("📝 Daily Journal")
        st.text_area("How was your day?", height=100)
        if st.button("Save Entry"):
            st.success("Saved to memory!")
            play_sound_and_wait("pop")

    # ==========================
    # 5. ⚙️ SETTINGS
    # ==========================
    elif menu == "⚙️ Settings":
        st.title("Profile Settings")
        new_n = st.text_input("Update Name", value=st.session_state.user_name)
        if st.button("Save Changes"):
            st.session_state.user_name = new_n
            st.success("Profile Updated!")
            st.rerun()
            
        st.warning("Reset Zone")
        if st.button("🔴 Reset All Progress"):
            st.session_state.clear()
            st.rerun()
