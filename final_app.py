import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 
import time
import random

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Life OS Pro", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🛠️ AUTO-FIXER ---
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

# --- LEVEL UP ---
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
    
    # 🌟 NEW VISUALS: GOOGLE FONTS & STYLING
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp { background-color: #0E1117; }
    
    .card { 
        background-color: #1A1C24; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #333; 
        margin-bottom: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* BIG NEON TEXT */
    .neon-text {
        font-size: 38px;
        font-weight: 800;
        color: #fff;
        text-shadow: 0 0 10px rgba(0, 255, 127, 0.5);
    }
    
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 50px; 
        font-weight: 600;
        font-size: 16px;
    }
    
    /* PROGRESS BARS */
    .stProgress > div > div > div > div { background-color: #00CCFF; }
    </style>
    """, unsafe_allow_html=True)

    try: tz = pytz.timezone(st.session_state.timezone)
    except: tz = pytz.timezone('Asia/Karachi')
    pk_time = datetime.now(tz)
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user_name}")
        st.markdown(f"**Lvl {st.session_state.level}** • {st.session_state.xp} XP")
        st.progress(st.session_state.xp / (st.session_state.level * 100))
        st.write("---")
        menu = st.radio("Menu", ["📊 Dashboard", "🎯 Focus", "💰 Wallet", "💪 Habits", "⚙️ Settings"])

    # === DASHBOARD ===
    if menu == "📊 Dashboard":
        # Header
        hr = pk_time.hour
        greet = "Morning" if 5<=hr<12 else "Afternoon" if 12<=hr<17 else "Evening" if 17<=hr<21 else "Night"
        st.markdown(f"<h1 style='font-size: 42px;'>Good {greet}! 👋</h1>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='card'><h5>💰 Total Balance</h5><div class='neon-text' style='color:#00FF7F;'>{st.session_state.currency} {st.session_state.balance}</div></div>", unsafe_allow_html=True)
        with c2:
            pending = sum(1 for g in st.session_state.goals if not g['done'])
            st.markdown(f"<div class='card'><h5>🎯 Goals Left</h5><div class='neon-text' style='color:#FF4500;'>{pending}</div></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='card'><h5>💧 Hydration Level</h5>", unsafe_allow_html=True)
        st.progress(min(st.session_state.water / 8, 1.0))
        st.caption(f"{st.session_state.water} / 8 Glasses")
        st.markdown("</div>", unsafe_allow_html=True)

    # === FOCUS (GOALS) ===
    elif menu == "🎯 Focus":
        st.title("Daily Missions 🎯")
        
        with st.expander("➕ Add New Goal", expanded=False):
            new_g = st.text_input("Goal Name", placeholder="e.g. Read 10 Pages")
            if st.button("Add Goal"):
                if new_g:
                    st.session_state.goals.append({'text': new_g, 'done': False})
                    play_sound_and_wait("pop")
                    st.rerun()

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for i, g in enumerate(st.session_state.goals):
            c1, c2, c3 = st.columns([1, 6, 1])
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
            with c3:
                if st.button("🗑️", key=f"del_g{i}"):
                    st.session_state.goals.pop(i)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # === WALLET (FIXED INCOME CATEGORIES) ===
    elif menu == "💰 Wallet":
        curr = st.session_state.currency
        val = st.session_state.balance
        color = "#00FF7F" if val >= 0 else "#FF4500"
        
        st.markdown(f"<div class='card' style='text-align:center;'><h5 style='margin:0;'>Current Balance</h5><h1 style='color:{color}; font-size:48px; margin:0;'>{curr} {val}</h1></div>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["➕ Transaction", "📜 History", "📊 Analytics"])
        
        # CATEGORIES LISTS
        income_cats = ["💼 Salary", "💻 Freelance", "📈 Business", "🎁 Gift", "💰 Bonus", "🤝 Side Hustle"]
        expense_cats = ["🍔 Food", "🏠 Rent", "🚗 Fuel", "🛍️ Shopping", "💡 Bills", "💊 Medical", "🎉 Fun", "✈️ Travel", "🎓 Education"]

        with tab1:
            st.write("#### New Entry")
            
            # --- CRITICAL FIX: TYPE SELECTION OUTSIDE FORM ---
            # Ye form se bahar hay, is liye click karte hi page refresh hoga
            # aur sahi categories load ho jayengi.
            typ = st.radio("Transaction Type", ["Expense 🔴", "Income 🟢"], horizontal=True)
            
            with st.form("money"):
                # Dynamic Category Selection
                if "Income" in typ:
                    cat = st.selectbox("Select Income Source", income_cats)
                else:
                    cat = st.selectbox("Select Expense Category", expense_cats)
                
                item = st.text_input("Description (e.g. Burger)")
                amt = st.number_input("Amount", min_value=1)
                
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
            st.subheader("History 📜")
            if st.session_state.transactions:
                df = pd.DataFrame(st.session_state.transactions[::-1])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No transactions yet.")

        with tab3:
            if st.session_state.transactions:
                df = pd.DataFrame(st.session_state.transactions)
                df_ex = df[df["Type"] == "Expense"]
                if not df_ex.empty:
                    fig = px.pie(df_ex, values='Amt', names='Cat', title="Expenses Breakdown", hole=0.5)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data.")

    # === HABITS ===
    elif menu == "💪 Habits":
        st.title("Habits & Health 🌱")
        
        # WATER BAR
        st.markdown("<div class='card'><h4>💧 Hydration</h4>", unsafe_allow_html=True)
        st.progress(min(st.session_state.water / 8, 1.0))
        c1, c2, c3 = st.columns([1, 1, 3])
        if c1.button("➕ Drink"):
            if st.session_state.water < 8:
                st.session_state.water += 1
                play_sound_and_wait("pop")
                st.rerun()
        if c2.button("➖ Undo"):
            if st.session_state.water > 0:
                st.session_state.water -= 1
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # HABITS
        st.markdown("<div class='card'><h4>🔥 Streaks</h4>", unsafe_allow_html=True)
        c_in, c_btn = st.columns([3, 1])
        nh = c_in.text_input("New Habit", placeholder="Habit Name...", label_visibility="collapsed")
        if c_btn.button("Add"):
            if nh:
                st.session_state.habits.append({"name": nh, "streak": 0})
                st.rerun()
                
        for i, h in enumerate(st.session_state.habits):
            c_x, c_y, c_z, c_del = st.columns([3, 1, 1, 0.5])
            c_x.markdown(f"**{h['name']}**")
            c_y.metric("Streak", f"{h['streak']} 🔥")
            if c_z.button("Done", key=f"h_{i}"):
                st.session_state.habits[i]['streak'] += 1
                st.session_state.xp += 15
                check_level_up()
                play_sound_and_wait("pop")
                st.snow()
                st.rerun()
            if c_del.button("x", key=f"del_h{i}"):
                st.session_state.habits.pop(i)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # === SETTINGS ===
    elif menu == "⚙️ Settings":
        st.title("Settings ⚙️")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        new_curr = st.text_input("Currency", value=st.session_state.currency)
        if st.button("Save Currency"):
            st.session_state.currency = new_curr
            st.rerun()
            
        tz_list = ["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"]
        new_tz = st.selectbox("Timezone", tz_list, index=0)
        if st.button("Save Timezone"):
            st.session_state.timezone = new_tz
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🔴 Factory Reset App"):
            st.session_state.clear()
            st.rerun()
