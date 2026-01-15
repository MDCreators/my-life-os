import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 

# --- CONFIG ---
st.set_page_config(page_title="Life OS", page_icon="🌸", layout="centered")

# --- 🎵 FORCE SOUND (HTML Method) ---
def play_sound(sound_type="pop"):
    # 1. Vibration
    vibrate_js = """<script>
    if (navigator.vibrate) { navigator.vibrate([200]); }
    </script>"""
    components.html(vibrate_js, height=0, width=0)
    
    # 2. Sound URLs
    sounds = {
        "win": "https://www.soundjay.com/misc/sounds/magic-chime-01.mp3",
        "cash": "https://www.soundjay.com/misc/sounds/coins-in-hand-2.mp3",
        "pop": "https://www.soundjay.com/buttons/sounds/button-09.mp3",
        "tada": "https://www.soundjay.com/human/sounds/applause-01.mp3"
    }
    url = sounds.get(sound_type, sounds["pop"])
    
    # 3. HTML Audio Injection (Hidden but Autoplay)
    sound_html = f"""
    <audio autoplay="true" style="display:none;">
    <source src="{url}" type="audio/mp3">
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

# --- AUTO-REPAIR ---
if 'goals' in st.session_state and st.session_state.goals:
    if isinstance(st.session_state.goals[0], dict) and 'done' not in st.session_state.goals[0]:
        del st.session_state['goals'] 
        del st.session_state['habits'] 

# --- STATE INIT ---
if 'user_name' not in st.session_state: st.session_state.user_name = "User"
if 'water_count' not in st.session_state: st.session_state.water_count = 0
if 'total_savings' not in st.session_state: st.session_state.total_savings = 0 
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'life_score' not in st.session_state: st.session_state.life_score = 0
if 'habits' not in st.session_state: 
    st.session_state.habits = [{"name": "Exercise", "streak": 0}]
if 'goals' not in st.session_state:
    st.session_state.goals = [{"text": "Goal 1", "done": False}]

# --- LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        try: users = st.secrets["users"]
        except: 
            st.warning("⚠️ Secrets Not Found")
            return False
            
        with st.form("Login"):
            st.markdown("## 🔐 Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if email in users and users[email] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.rerun()
                else: st.error("❌ Error")
        return False
    return True

# --- APP ---
if check_password():
    # Time
    pk_tz = pytz.timezone('Asia/Karachi')
    pk_time = datetime.now(pk_tz)
    
    # CSS
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: white; }
        .stButton>button { background-color: #FF1493 !important; color: white !important; border-radius: 12px; border: none; font-weight: bold; }
        .big-score { font-size: 24px; font-weight: bold; color: #00FF7F; text-align: center; }
        </style>
        """, unsafe_allow_html=True)

    # Header
    st.caption(f"🗓️ {pk_time.strftime('%d %B')} | ⏰ {pk_time.strftime('%I:%M %p')}")
    st.markdown(f"<h1 style='text-align: center;'>Hi, {st.session_state.user_name}! 🌙</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-score'>🌟 XP: {st.session_state.life_score}</div>", unsafe_allow_html=True)
    
    # Tabs
    t1, t2, t3, t4, t5 = st.tabs(["🏠 Hub", "✅ Habits", "💰 Wallet", "🌿 Care", "⚙️ Set"])

    # 1. HUB
    with t1:
        st.write("### Today's Focus 🎯")
        # Progress
        tg = len(st.session_state.goals)
        cg = sum(1 for g in st.session_state.goals if g.get('done', False))
        if tg > 0: st.progress(cg / tg)
        
        for i, goal in enumerate(st.session_state.goals):
            c1, c2 = st.columns([1, 8])
            with c1:
                if st.checkbox("", key=f"g_{i}", value=goal['done']):
                    if not goal['done']:
                        st.session_state.goals[i]['done'] = True
                        st.session_state.life_score += 10
                        play_sound("win")
                        st.balloons()
                        st.rerun()
                else:
                    if goal['done']:
                         st.session_state.goals[i]['done'] = False
                         st.session_state.life_score -= 10
                         st.rerun()
            with c2:
                st.session_state.goals[i]['text'] = st.text_input(f"G{i}", goal['text'], label_visibility="collapsed")

        st.write("---")
        st.write(f"### 💧 Water: {st.session_state.water_count}/8")
        st.progress(min(st.session_state.water_count / 8, 1.0))

    # 2. HABITS
    with t2:
        c_a, c_b = st.columns([3, 1])
        nh = c_a.text_input("New Habit", label_visibility="collapsed")
        if c_b.button("Add"):
            if nh:
                st.session_state.habits.append({"name": nh, "streak": 0})
                play_sound("pop")
                st.rerun()
        
        for i, h in enumerate(st.session_state.habits):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"**{h['name']}**")
            c2.write(f"🔥 {h['streak']}")
            if c3.button("+1", key=f"h{i}"):
                st.session_state.habits[i]['streak'] += 1
                st.session_state.life_score += 5
                play_sound("pop")
                st.rerun()
            if c4.button("🗑️", key=f"d{i}"):
                st.session_state.habits.pop(i)
                st.rerun()

    # 3. WALLET
    with t3:
        st.metric("Savings", f"PKR {st.session_state.total_savings}")
        ta, tb = st.tabs(["Add", "List"])
        with ta:
            with st.form("fin"):
                item = st.text_input("Item")
                amt = st.number_input("Amount", min_value=0)
                cat = st.selectbox("Cat", ["Food", "Transport", "Shopping", "Salary", "Other"])
                typ = st.selectbox("Type", ["Expense", "Income"])
                if st.form_submit_button("Save"):
                    if typ == "Expense": st.session_state.total_savings -= amt
                    else: st.session_state.total_savings += amt
                    
                    st.session_state.expenses.append({
                        "Date": str(pk_time.date()), "Item": item, "Amount": amt, "Type": typ, "Category": cat
                    })
                    play_sound("cash")
                    st.rerun()
        with tb:
            if st.session_state.expenses: st.dataframe(pd.DataFrame(st.session_state.expenses))

    # 4. CARE
    with t4:
        st.write("### Hydration")
        cols = st.columns(4)
        cl = []
        for i in range(4): cl.append(cols[i].checkbox(f"{i+1}", value=st.session_state.water_count >= i+1, key=f"w1_{i}"))
        cols2 = st.columns(4)
        for i in range(4): cl.append(cols2[i].checkbox(f"{i+5}", value=st.session_state.water_count >= i+5, key=f"w2_{i}"))
        
        nc = sum(cl)
        if nc > st.session_state.water_count:
             st.session_state.water_count = nc
             play_sound("pop")
             st.rerun()

        st.write("---")
        st.write("### Journal")
        st.select_slider("Mood", ["😐", "🙂", "🤩"])
        st.text_area("Gratitude")
        if st.button("Save Log"):
            st.session_state.life_score += 5
            play_sound("tada")
            st.success("Saved!")

    # 5. SETUP
    with t5:
        nn = st.text_input("Name", value=st.session_state.user_name)
        if st.button("Update"): 
            st.session_state.user_name = nn
            play_sound("pop")
            st.rerun()
