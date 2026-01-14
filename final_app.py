import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Life OS", page_icon="🌸", layout="centered")

# --- SOUND & VIBRATION FUNCTION ---
def trigger_feedback():
    # 1. VIBRATION (JavaScript Attempt)
    # Hum browser ko 'User Gesture' dikhane ki koshish kar rahay hain
    vibrate_js = """
    <script>
    navigator.vibrate = navigator.vibrate || navigator.webkitVibrate || navigator.mozVibrate || navigator.msVibrate;
    if (navigator.vibrate) {
        navigator.vibrate([200]);
    }
    </script>
    """
    components.html(vibrate_js, height=0, width=0)
    
    # 2. SOUND (Streamlit Native Autoplay)
    # Ye invisible player hai jo automatically chalay ga
    # Short "Ding" Sound
    st.audio("https://www.soundjay.com/buttons/sounds/button-3.mp3", format="audio/mp3", autoplay=True)

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
            st.warning("⚠️ Add [users] to Secrets.")
            return True 
            
        with st.form("Login"):
            st.markdown("## 🔐 Secure Login")
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
        .stButton>button { color: white !important; background-color: #FF1493 !important; border-radius: 12px; border: none; font-weight: bold; }
        .stTextInput>div>div>input { background-color: #262730; color: white !important; border-radius: 10px; }
        .big-score { font-size: 24px; font-weight: bold; color: #00FF7F; text-align: center; }
        .streak-num { font-size: 26px; font-weight: bold; color: #00BFFF; }
        /* Hide Audio Player */
        audio { display: none; }
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
                        trigger_feedback() # SOUND HERE
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
                    trigger_feedback() # SOUND HERE
                    st.rerun()
        st.write("---")
        for i, habit in enumerate(st.session_state.habits):
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                with c1: st.markdown(f"**{habit['name']}**")
                with c2: st.markdown(f"<span class='streak-num'>{habit['streak']} 🔥</span>", unsafe_allow_html=True)
                with c3:
                    if st.button("➕ 1", key=f"h_inc_{i}"):
                        st.session_state.habits[i]['streak'] += 1  
                        st.session_state.life_score += 5
                        trigger_feedback() # SOUND HERE
                        st.rerun()
                with c4:
                    if st.button("🗑️", key=f"h_del_{i}"):
                        st.session_state.habits.pop(i)
                        st.rerun()
                st.markdown("---")

    # === TAB 3: FINANCE ===
    with tab3:
        st.subheader("Wallet 💰")
        clr = "#00FF7F" if st.session_state.total_savings >= 0 else "#FF4500"
        st.markdown(f"<h1 style='text-align: center; color: {clr};'>PKR {st.session_state.total_savings}</h1>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📝 Add", "📊 Charts", "📜 History"])
        exp_cats = ["🍔 Food", "🏠 Rent", "🚗 Fuel", "🛍️ Shopping", "💡 Bills", "💊 Medical", "🎓 Fees", "🎉 Fun", "✈️ Travel", "🎁 Gifts", "💸 Debt", "📝 Other"]
        inc_cats = ["💼 Salary", "💻 Freelance", "📈 Business", "🎁 Gift", "💰 Bonus", "📝 Other"]

        with t1:
            c1, c2 = st.columns(2)
            with c1:
                with st.form("ex_form"):
                    st.write("**Expense 💸**")
                    item = st.text_input("Item")
                    cat = st.selectbox("Category", exp_cats)
                    amt = st.number_input("Amount", min_value=0)
                    if st.form_submit_button("Spend"):
                        st.session_state.total_savings -= amt
                        entry = {"Date": pk_time.strftime("%Y-%m-%d"), "Type": "Expense", "Item": item, "Amount": amt, "Category": cat}
                        st.session_state.expenses.append(entry)
                        trigger_feedback() # SOUND HERE
                        st.rerun()
            with c2:
                with st.form("in_form"):
                    st.write("**Income 💰**")
                    src = st.text_input("Source")
                    cat_in = st.selectbox("Category", inc_cats)
                    amt_in = st.number_input("Amount", min_value=0)
                    if st.form_submit_button("Deposit"):
                        st.session_state.total_savings += amt_in
                        entry_in = {"Date": pk_time.strftime("%Y-%m-%d"), "Type": "Income", "Item": src, "Amount": amt_in, "Category": cat_in}
                        st.session_state.expenses.append(entry_in)
                        trigger_feedback() # SOUND HERE
                        st.rerun()

        with t2:
            if st.session_state.expenses:
                df = pd.DataFrame(st.session_state.expenses)
                c_a, c_b = st.columns(2)
                with c_a:
                    st.caption("Expenses")
                    df_ex = df[df["Type"] == "Expense"]
                    if not df_ex.empty:
                        fig = px.pie(df_ex, values='Amount', names='Category', hole=0.5)
                        st.plotly_chart(fig, use_container_width=True)
                with c_b:
                    st.caption("Income")
                    df_in = df[df["Type"] == "Income"]
                    if not df_in.empty:
                        fig2 = px.pie(df_in, values='Amount', names='Category', hole=0.5)
                        st.plotly_chart(fig2, use_container_width=True)
            else: st.info("No data yet.")

        with t3:
            if st.session_state.expenses: 
                st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)

    # === TAB 4: SELF CARE ===
    with tab4:
        st.subheader("Hydration 💧")
        cols = st.columns(4); check_list = []
        for i in range(4): check_list.append(cols[i].checkbox(f"{i+1}", value=st.session_state.water_count >= i+1))
        cols2 = st.columns(4)
        for i in range(4): check_list.append(cols2[i].checkbox(f"{i+5}", value=st.session_state.water_count >= i+5))
        
        new_count = sum(check_list)
        if new_count > st.session_state.water_count:
             st.session_state.water_count = new_count
             trigger_feedback() # SOUND HERE
             st.rerun()

        st.divider()
        st.subheader("Journal 📝")
        c1, c2 = st.columns(2)
        c1.selectbox("Mood", ["Happy 🙂", "Calm 😌", "Stressed 😫", "Sad 😢"])
        c2.selectbox("Sleep", ["8+ Hours 💤", "6-7 Hours", "4-5 Hours", "Less than 4"])
        st.text_area("Gratitude", placeholder="I am thankful for...")
        if st.button("Save Entry"):
            st.session_state.life_score += 5
            trigger_feedback() # SOUND HERE
            st.success("Saved!")

    # === SETUP ===
    with tab_setup:
        st.subheader("Profile")
        new_name = st.text_input("Change Name", value=st.session_state.user_name)
        if st.button("Update"): 
            st.session_state.user_name = new_name
            trigger_feedback() # SOUND HERE
            st.rerun()
