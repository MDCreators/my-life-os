import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Life OS", page_icon="🌸", layout="centered")

# --- VIBRATION FUNCTION ---
def vibrate():
    js = """
    <script>
    if (window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(200);
    }
    </script>
    """
    components.html(js, height=0, width=0)

# --- SESSION STATE ---
if 'user_name' not in st.session_state: st.session_state.user_name = "User"
if 'water_count' not in st.session_state: st.session_state.water_count = 0
if 'total_savings' not in st.session_state: st.session_state.total_savings = 0 
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'life_score' not in st.session_state: st.session_state.life_score = 0
if 'habits' not in st.session_state: 
    st.session_state.habits = [
        {"name": "Exercise", "streak": 0}, 
        {"name": "Prayers", "streak": 0}
    ]
if 'goals' not in st.session_state:
    st.session_state.goals = [
        {"text": "Goal 1", "done": False},
        {"text": "Goal 2", "done": False},
        {"text": "Goal 3", "done": False}
    ]

# --- LOGIN SYSTEM ---
def check_password():
    if "authenticated" not in st.session_state:
        try:
            users = st.secrets["users"]
        except:
            st.warning("⚠️ Setup Incomplete: Add [users] to Streamlit Secrets.")
            return True 
            
        with st.form("Login"):
            st.markdown("<h2 style='text-align: center; color: #FF1493;'>🔐 Secure Login</h2>", unsafe_allow_html=True)
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Unlock"):
                if email in users and users[email] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.rerun()
                else:
                    st.error("❌ Access Denied")
        return False
    return True

# --- MAIN APP ---
if check_password():
    
    # Timezone
    pk_tz = pytz.timezone('Asia/Karachi')
    pk_time = datetime.now(pk_tz)
    
    # CSS
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        .stButton > button { color: white !important; background-color: #FF1493 !important; border-radius: 12px; border: none; font-weight: bold; }
        .stTextInput>div>div>input { background-color: #262730; color: white !important; border-radius: 10px; }
        .big-score { font-size: 24px; font-weight: bold; color: #00FF7F; text-align: center; }
        .streak-num { font-size: 26px; font-weight: bold; color: #00BFFF; }
        </style>
        """, unsafe_allow_html=True)

    # Header
    dt_str = pk_time.strftime("%A, %d %B")
    tm_str = pk_time.strftime("%I:%M %p")
    st.markdown(f"<p style='text-align: center; color: #888;'>🗓️ {dt_str} | ⏰ {tm_str} (PKT)</p>", unsafe_allow_html=True)

    curr_hour = pk_time.hour
    if 5 <= curr_hour < 12: greeting = "Good Morning"
    elif 12 <= curr_hour < 17: greeting = "Good Afternoon"
    elif 17 <= curr_hour < 21: greeting = "Good Evening"
    else: greeting = "Good Night"

    st.markdown(f"<h1 style='text-align: center;'>{greeting}, {st.session_state.user_name}! 🌙</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-score'>🌟 Life Score: {st.session_state.life_score} XP</div>", unsafe_allow_html=True)
    
    # Tabs
    tab_setup, tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Setup", "🏠 Main Hub", "✅ Habits", "💰 Finance", "🌿 Self-Care"])

    # === TAB 1: MAIN HUB ===
    with tab1:
        st.divider()
        st.subheader("Today's Focus 🎯")
        for i, goal in enumerate(st.session_state.goals):
            c1, c2 = st.columns([1, 8])
            with c1:
                if st.checkbox("", key=f"g_{i}", value=goal['done']):
                    if not goal['done']:
                        st.session_state.goals[i]['done'] = True
                        st.session_state.life_score += 10
                        vibrate()
                        st.balloons()
                        st.rerun()
                else:
                    if goal['done']:
                         st.session_state.goals[i]['done'] = False
                         st.session_state.life_score -= 10
                         st.rerun()
            with c2:
                st.session_state.goals[i]['text'] = st.text_input(f"G{i}", goal['text'], label_visibility="collapsed")

        st.divider()
        st.subheader("Hydration 💧")
        progress = min(st.session_state.water_count / 8, 1.0)
        st.progress(progress)
        st.caption(f"{st.session_state.water_count} / 8 Glasses")

    # === TAB 2: HABITS ===
    with tab2:
        st.subheader("Habit Tracker ✨")
        c_in, c_btn = st.columns([3, 1])
        with c_in: new_h = st.text_input("New Habit", label_visibility="collapsed")
        with c_btn: 
            if st.button("➕"):
                if new_h:
                    st.session_state.habits.append({"name": new_h, "streak": 0})
                    vibrate()
                    st.rerun()
        st.write("---")
        for i, habit in enumerate(st.session_state.habits):
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                with c1: st.markdown(f"**{habit
