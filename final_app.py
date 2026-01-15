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
    initial_sidebar_state="collapsed" # Collapsed looks better on mobile
)

# --- 🛠️ AUTO-FIXER (CRITICAL: Prevents Errors) ---
# This block fixes the mismatch between old and new data
if 'goals' in st.session_state:
    fixed_goals = []
    for g in st.session_state.goals:
        # Support both 'text' (old) and 'txt' (new)
        t = g.get('txt', g.get('text', 'New Goal'))
        d = g.get('done', False)
        fixed_goals.append({'text': t, 'done': d})
    st.session_state.goals = fixed_goals

if 'habits' in st.session_state:
    fixed_habits = []
    for h in st.session_state.habits:
        # Support both 'streak' (old) and 's' (new)
        n = h.get('name', 'Habit')
        s = h.get('s', h.get('streak', 0))
        fixed_habits.append({'name': n, 'streak': s})
    st.session_state.habits = fixed_habits

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
    
    # HTML Audio
    st.markdown(f"""
    <audio autoplay="true" style="display:none;">
    <source src="{url}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)
    time.sleep(1.0) # Short wait for mobile

# --- STATE MANAGEMENT ---
if 'user_name' not in st.session_state: st.session_state.user_name = "Boss"
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'level' not in st.session_state: st.session_state.level = 1
if 'balance' not in st.session_state: st.session_state.balance = 0
if 'water' not in st.session_state: st.session_state.water = 0
if 'transactions' not in st.session_state: st.session_state.transactions = []

# --- 🌍 NEW SETTINGS STATE ---
if 'currency' not in st.session_state: st.session_state.currency = "PKR"
if 'timezone' not in st.session_state: st.session_state.timezone = "Asia/Karachi"

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
    
    # Custom CSS for Mobile Optimization
    st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    /* Mobile Friendly Cards */
    .card { background-color: #1E1E1E; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 10px; }
    .big-stat { font-size: 28px; font-weight: bold; color: #4CAF50; }
    /* Better Buttons on Phone */
    .stButton>button { width: 100%; border-radius: 10px; height: 45px; }
    /* Remove top padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

    # Timezone Logic
    try:
        tz = pytz.timezone(st.session_state.timezone)
    except:
        tz = pytz.timezone('Asia/Karachi')
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
        
        st.write("---")
        st.caption(f"🕒 {pk_time.strftime('%I:%M %p')}")

    # ==========================
    # 1. 📊 DASHBOARD
    # ==========================
    if menu == "📊 Dashboard":
        # Dynamic Greeting
        hr = pk_time.hour
        greet = "Morning" if 5<=hr<12 else "Afternoon" if 12<=hr<17 else "Evening" if 17<=hr<21 else "Night"
        st.title(f"Good {greet}, Boss! 👋")
        
        # Mobile Grid Summary
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='card'><h6>💰 Savings</h6><div class='big-stat'>{st.session_state.currency} {st.session_state.balance}</div></div>", unsafe_allow_html=True)
        with c2:
            pending = sum(1 for g in st.session_state.goals if not g['done'])
            st.markdown(f"<div class='card'><h6>🎯 Pending</h6><div class='big-stat'>{pending}</div></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='card'><h6>💧 Hydration</h6><div class='big-stat'>{st.session_state.water} / 8</div></div>", unsafe_allow_html=True)

        st.info(f"💡 Quote: {random.choice(['Focus on the process.', 'Discipline is freedom.', 'Keep grinding.'])}")

    # ==========================
    # 2. 🎯 FOCUS (Goals)
    # ==========================
    elif menu == "🎯 Focus":
        st.title("Daily Missions 🎯")
        
        # Progress
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
        
        # Pomodoro (Mobile Friendly)
        with st.expander("🍅 Focus Timer"):
            if st.button("Start 25 Mins"):
                with st.empty():
                    for seconds in range(1500, 0, -1):
                        mins, secs = divmod(seconds, 60)
                        st.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
                        time.sleep(1)
                    st.success("Done!")
                    play_sound_and_wait("win")

    # ==========================
    # 3. 💰 WALLET (Custom Currency)
    # ==========================
    elif menu == "💰 Wallet":
        curr = st.session_state.currency
        st.title(f"Wallet ({curr}) 💸")
        
        val = st.session_state.balance
        clr = "#00FF00" if val >= 0 else "#FF0000"
        st.markdown(f"<div style='text-align:center; padding:10px; background:#111; border-radius:10px;'><h1 style='color:{clr}; margin:0;'>{curr} {val}</h1></div>", unsafe_allow_html=True)
        st.write("")

        tab1, tab2 = st.tabs(["Add", "Stats"])
        
        with tab1:
            with st.form("money"):
                item = st.text_input("Item")
                c_amt, c_cat = st.columns(2)
                amt = c_amt.number_input("Amount", min_value=1)
                cat = c_cat.selectbox("Cat", ["Food", "Rent", "Fuel", "Shopping", "Salary", "Biz"])
                typ = st.radio("Type", ["Expense 🔴", "Income 🟢"], horizontal=True)
                
                if st.form_submit_button("Save Transaction"):
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
                st.info("No data yet.")

    # ==========================
    # 4. 💪 HABITS
    # ==========================
    elif menu == "💪 Habits":
        st.title("Habits & Water 🌱")
        
        # Water Grid (Mobile Optimized)
        st.markdown("<div class='card'><h4>💧 Water Intake</h4>", unsafe_allow_html=True)
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

        # Habits List
        st.markdown("<div class='card'><h4>🔥 Streaks</h4>", unsafe_allow_html=True)
        nh = st.text_input("New Habit", placeholder="Type & Press Enter")
        if st.button("Add Habit"):
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
        
        # Journal
        with st.expander("📝 Daily Journal"):
            st.text_area("Write here...", height=100)
            if st.button("Save"):
                st.success("Saved!")
                play_sound_and_wait("pop")

    # ==========================
    # 5. ⚙️ SETTINGS
    # ==========================
    elif menu == "⚙️ Settings":
        st.title("System Settings ⚙️")
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Preferences")
        
        # 1. Custom Currency
        new_curr = st.text_input("Set Currency Symbol", value=st.session_state.currency)
        if st.button("Update Currency"):
            st.session_state.currency = new_curr
            st.success("Currency Updated!")
            st.rerun()
            
        st.write("---")
        
        # 2. Custom Timezone
        tz_list = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York", "Australia/Sydney"]
        new_tz = st.selectbox("Select Timezone", tz_list, index=0)
        if st.button("Update Timezone"):
            st.session_state.timezone = new_tz
            st.success("Timezone Updated!")
            st.rerun()
        
        st.write("---")
        
        # 3. Profile
        new_n = st.text_input("Your Name", value=st.session_state.user_name)
        if st.button("Update Name"):
            st.session_state.user_name = new_n
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("🔴 Factory Reset App"):
            st.session_state.clear()
            st.rerun()
