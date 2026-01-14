import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz # TIMEZONE LIBRARY
import streamlit.components.v1 as components # VIBRATION LIBRARY

# --- PAGE CONFIG ---
st.set_page_config(page_title="Aimen's Life OS", page_icon="🌸", layout="centered")

# --- VIBRATION FUNCTION (Javascript) ---
def vibrate():
    # Ye script phone ko vibrate karne ka order deti hay
    js_code = """
    <script>
    try {
        window.navigator.vibrate(200);  // 200ms Vibration
    } catch (e) {
        console.log("Vibration not supported");
    }
    </script>
    """
    components.html(js_code, height=0, width=0)

# --- LOGIN CHECK ---
def check_password():
    if "authenticated" not in st.session_state:
        try:
            users = st.secrets["users"]
        except:
            st.warning("⚠️ Setup incomplete: Add [users] to Secrets.")
            return True 
            
        with st.form("Login"):
            st.markdown("<h2 style='text-align: center; color: #FF1493;'>🔐 Paid User Login</h2>", unsafe_allow_html=True)
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Unlock Life OS"):
                if email in users and users[email] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        return False
    return True

# --- INITIALIZE STATE ---
if 'user_name' not in st.session_state: st.session_state.user_name = "Aimen"
if 'water_count' not in st.session_state: st.session_state.water_count = 0
if 'total_savings' not in st.session_state: st.session_state.total_savings = 0 
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'life_score' not in st.session_state: st.session_state.life_score = 0
if 'habits' not in st.session_state: 
    st.session_state.habits = [
        {"name": "Exercise", "streak": 5}, 
        {"name": "Reading", "streak": 2}, 
        {"name": "Meditation", "streak": 10}
    ]
if 'goals' not in st.session_state:
    st.session_state.goals = [
        {"text": "Eat Fastfood", "done": False},
        {"text": "Eat Beef Burger", "done": False},
        {"text": "Help Someone", "done": False}
    ]

# --- MAIN APP ---
if check_password():
    
    # 1. TIMEZONE FIX (KARACHI/LAHORE)
    pk_timezone = pytz.timezone('Asia/Karachi')
    pk_time = datetime.now(pk_timezone)
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        .stButton > button { color: white !important; background-color: #FF1493 !important; border-radius: 12px; border: none; font-weight: bold; }
        .stTextInput>div>div>input { background-color: #262730; color: white !important; border-radius: 10px; }
        .big-score { font-size: 24px; font-weight: bold; color: #00FF7F; text-align: center; }
        .streak-num { font-size: 28px; font-weight: bold; color: #00BFFF; }
        </style>
        """, unsafe_allow_html=True)

    # --- HEADER ---
    # Time Display
    dt_string = pk_time.strftime("%A, %d %B")
    tm_string = pk_time.strftime("%I:%M %p")
    st.markdown(f"<p style='text-align: center; color: #aaa; font-size: 14px;'>🗓️ {dt_string} | ⏰ {tm_string} (PKT)</p>", unsafe_allow_html=True)

    # Greeting Logic
    curr_hour = pk_time.hour
    if 5 <= curr_hour < 12: greeting = "Good Morning"
    elif 12 <= curr_hour < 17: greeting = "Good Afternoon"
    elif 17 <= curr_hour < 21: greeting = "Good Evening"
    else: greeting = "Good Night"

    st.markdown(f"<h1 style='text-align: center;'>{greeting}, {st.session_state.user_name}! 🌙</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-score'>🌟 Life Score: {st.session_state.life_score} XP</div>", unsafe_allow_html=True)
    
    # --- TABS ---
    tab_setup, tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Setup", "🏠 Main Hub", "✅ Habits", "💰 Finance", "🌿 Self-Care"])

    # === TAB 1: MAIN HUB ===
    with tab1:
        st.divider()
        st.subheader("Today's Focus 🎯")
        
        for i, goal in enumerate(st.session_state.goals):
            c1, c2 = st.columns([1, 8])
            with c1:
                # Goal Checkbox
                if st.checkbox("", key=f"g_check_{i}", value=goal['done']):
                    if not goal['done']:
                        st.session_state.goals[i]['done'] = True
                        st.session_state.life_score += 10
                        vibrate() # <--- VIBRATE
                        st.balloons()
                        st.rerun()
                else:
                    if goal['done']:
                         st.session_state.goals[i]['done'] = False
                         st.session_state.life_score -= 10
                         st.rerun()
            with c2:
                st.text_input(f"Goal {i+1}", goal['text'], label_visibility="collapsed", key=f"g_text_{i}")

        st.divider()
        st.subheader("Hydration Tracker 💧")
        progress = min(st.session_state.water_count / 8, 1.0)
        st.progress(progress)
        st.caption(f"Status: {st.session_state.water_count} / 8 Glasses")

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
                col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                with col1: st.markdown(f"### {habit['name']}")
                with col2: st.markdown(f"<span class='streak-num'>{habit['streak']} 🔥</span>", unsafe_allow_html=True)
                with col3:
                    if st.button("➕ 1", key=f"h_inc_{i}"):
                        st.session_state.habits[i]['streak'] += 1  
                        st.session_state.life_score += 5
                        vibrate() # <--- VIBRATE
                        st.toast(f"{habit['name']} +1!", icon="🔥")
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"h_del_{i}"):
                        st.session_state.habits.pop(i)
                        st.rerun()
                st.markdown("---")

    # === TAB 3: FINANCE ===
    with tab3:
        st.subheader("Wallet 💰")
        st.markdown(f"<h1 style='text-align: center; color: #00FF7F;'>PKR {st.session_state.total_savings}</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📝 Transact", "📊 History"])
        with t1:
            with st.form("ex_form"):
                item = st.text_input("Item")
                amt = st.number_input("Amount", min_value=0)
                if st.form_submit_button("Spend"):
                    st.session_state.total_savings -= amt
                    st.session_state.expenses.append({"Date": pk_time.strftime("%Y-%m-%d"), "Type": "Expense", "Item": item, "Amount": amt})
                    vibrate()
                    st.rerun()
        with t2:
             if st.session_state.expenses: st.dataframe(pd.DataFrame(st.session_state.expenses))

    # === TAB 4: SELF CARE ===
    with tab4:
        st.subheader("Hydration 💧")
        cols = st.columns(4)
        check_list = []
        # Create checkboxes
        for i in range(4): check_list.append(cols[i].checkbox(f"{i+1}", value=st.session_state.water_count >= i+1))
        
        # Check logic
        new_count = sum(check_list) # Simplified logic for checkboxes
        # (Real implementation needs explicit index checking, but keeping it simple for vibration test)
        if new_count > st.session_state.water_count:
             st.session_state.water_count = new_count
             vibrate() # <--- VIBRATE
             st.rerun()

    # === SETUP TAB ===
    with tab_setup:
        st.subheader("Profile")
        new_name = st.text_input("Name", value=st.session_state.user_name)
        if st.button("Save"): 
            st.session_state.user_name = new_name
            st.rerun()
