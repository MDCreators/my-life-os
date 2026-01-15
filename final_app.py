import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import streamlit.components.v1 as components 
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Life OS", page_icon="🌸", layout="centered")

# --- 🎵 SOUND SYSTEM ---
def play_sound_and_wait(sound_type="pop"):
    # Vibration
    vibrate_js = """<script>
    if (navigator.vibrate) { navigator.vibrate([200]); }
    </script>"""
    components.html(vibrate_js, height=0, width=0)
    
    # Sound URLs
    sounds = {
        "win": "https://www.soundjay.com/misc/sounds/magic-chime-01.mp3",
        "cash": "https://www.soundjay.com/misc/sounds/coins-in-hand-2.mp3",
        "pop": "https://www.soundjay.com/buttons/sounds/button-09.mp3",
        "tada": "https://www.soundjay.com/human/sounds/applause-01.mp3"
    }
    url = sounds.get(sound_type, sounds["pop"])
    
    # Player
    sound_html = f"""
    <audio autoplay="true" style="display:none;">
    <source src="{url}" type="audio/mp3">
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)
    
    # Delay for Sound
    time.sleep(1.2) 

# --- SESSION STATE ---
if 'user_name' not in st.session_state: st.session_state.user_name = "User"
if 'water_count' not in st.session_state: st.session_state.water_count = 0
if 'total_savings' not in st.session_state: st.session_state.total_savings = 0 
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'life_score' not in st.session_state: st.session_state.life_score = 0
if 'habits' not in st.session_state: 
    st.session_state.habits = [{"name": "Exercise", "streak": 0}, {"name": "Prayers", "streak": 0}]

# --- 3 GOALS RESTORED ---
if 'goals' not in st.session_state:
    st.session_state.goals = [
        {"text": "Goal 1", "done": False}, 
        {"text": "Goal 2", "done": False},
        {"text": "Goal 3", "done": False}
    ]

# --- AUTO REPAIR ---
if 'goals' in st.session_state and st.session_state.goals:
    if isinstance(st.session_state.goals[0], dict) and 'done' not in st.session_state.goals[0]:
        del st.session_state['goals']

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
                else: st.error("❌ Invalid Login")
        return False
    return True

# --- MAIN APP ---
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

    # --- RESTORED GREETING LOGIC ---
    curr_hour = pk_time.hour
    if 5 <= curr_hour < 12: greeting = "Good Morning"
    elif 12 <= curr_hour < 17: greeting = "Good Afternoon"
    elif 17 <= curr_hour < 21: greeting = "Good Evening"
    else: greeting = "Good Night"

    # Header
    st.caption(f"🗓️ {pk_time.strftime('%d %B')} | ⏰ {pk_time.strftime('%I:%M %p')}")
    st.markdown(f"<h1 style='text-align: center;'>{greeting}, {st.session_state.user_name}! 🌙</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-score'>🌟 Life Score: {st.session_state.life_score} XP</div>", unsafe_allow_html=True)
    
    # Tabs
    t_set, t1, t2, t3, t4 = st.tabs(["⚙️ Setup", "🏠 Hub", "✅ Habits", "💰 Finance", "🌿 Care"])

    # 1. SETUP
    with t_set:
        st.write("### Profile Settings")
        nn = st.text_input("Name", value=st.session_state.user_name)
        if st.button("Update Profile"): 
            st.session_state.user_name = nn
            play_sound_and_wait("pop")
            st.rerun()

    # 2. HUB
    with t1:
        st.write("### Today's Focus 🎯")
        tg = len(st.session_state.goals)
        cg = sum(1 for g in st.session_state.goals if g.get('done', False))
        if tg > 0: st.progress(cg / tg)
        
        for i, goal in enumerate(st.session_state.goals):
            c1, c2 = st.columns([1, 8])
            with c1:
                is_checked = st.checkbox("", key=f"g_{i}", value=goal['done'])
                if is_checked != goal['done']:
                    st.session_state.goals[i]['done'] = is_checked
                    if is_checked:
                        st.session_state.life_score += 10
                        play_sound_and_wait("win")
                        st.balloons()
                    else:
                        st.session_state.life_score -= 10
                    st.rerun()
            with c2:
                st.session_state.goals[i]['text'] = st.text_input(f"G{i}", goal['text'], label_visibility="collapsed")

        st.write("---")
        st.write(f"### 💧 Water: {st.session_state.water_count}/8")
        st.progress(min(st.session_state.water_count / 8, 1.0))

    # 3. HABITS
    with t2:
        c_a, c_b = st.columns([3, 1])
        nh = c_a.text_input("New Habit", label_visibility="collapsed")
        if c_b.button("Add"):
            if nh:
                st.session_state.habits.append({"name": nh, "streak": 0})
                play_sound_and_wait("pop")
                st.rerun()
        
        for i, h in enumerate(st.session_state.habits):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"**{h['name']}**")
            c2.write(f"🔥 {h['streak']}")
            if c3.button("+1", key=f"h{i}"):
                st.session_state.habits[i]['streak'] += 1
                st.session_state.life_score += 5
                play_sound_and_wait("pop")
                st.rerun()
            if c4.button("🗑️", key=f"d{i}"):
                st.session_state.habits.pop(i)
                st.rerun()

    # 4. FINANCE
    with t3:
        st.write("### Wallet 💰")
        
        # Color Logic
        val = st.session_state.total_savings
        color = "#00FF7F" if val >= 0 else "#FF4500" 
        st.markdown(f"<h1 style='text-align: center; color: {color};'>PKR {val}</h1>", unsafe_allow_html=True)
        
        ta, tb, tc = st.tabs(["📝 Add", "📊 Charts", "📜 History"])
        
        exp_cats = ["🍔 Food", "🏠 Rent", "🚗 Fuel", "🛍️ Shopping", "💡 Bills", "💊 Medical", "🎓 Fees", "🎉 Fun", "✈️ Travel", "🎁 Gifts", "💸 Debt", "📝 Other"]
        inc_cats = ["💼 Salary", "💻 Freelance", "📈 Business", "🎁 Gift", "💰 Bonus", "🤝 Side Hustle"]

        with ta:
            c1, c2 = st.columns(2)
            with c1:
                with st.form("ex_form"):
                    st.write("**Expense 💸**")
                    item = st.text_input("Item")
                    cat = st.selectbox("Category", exp_cats)
                    amt = st.number_input("Amount", min_value=0)
                    if st.form_submit_button("Spend"):
                        st.session_state.total_savings -= amt
                        st.session_state.expenses.append({
                            "Date": str(pk_time.date()), "Item": item, "Amount": amt, "Type": "Expense", "Category": cat
                        })
                        play_sound_and_wait("cash")
                        st.rerun()
            with c2:
                with st.form("in_form"):
                    st.write("**Income 💰**")
                    src = st.text_input("Source")
                    cat_in = st.selectbox("Category", inc_cats)
                    amt_in = st.number_input("Amount", min_value=0)
                    if st.form_submit_button("Deposit"):
                        st.session_state.total_savings += amt_in
                        st.session_state.expenses.append({
                            "Date": str(pk_time.date()), "Item": src, "Amount": amt_in, "Type": "Income", "Category": cat_in
                        })
                        play_sound_and_wait("cash")
                        st.rerun()
        
        with tb:
            if st.session_state.expenses:
                df = pd.DataFrame(st.session_state.expenses)
                c_pie1, c_pie2 = st.columns(2)
                with c_pie1:
                    st.caption("Expense")
                    df_ex = df[df["Type"] == "Expense"]
                    if not df_ex.empty:
                        fig = px.pie(df_ex, values='Amount', names='Category', hole=0.4)
                        st.plotly_chart(fig, use_container_width=True)
                with c_pie2:
                    st.caption("Income")
                    df_in = df[df["Type"] == "Income"]
                    if not df_in.empty:
                        fig2 = px.pie(df_in, values='Amount', names='Category', hole=0.4)
                        st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data yet.")

        with tc:
            if st.session_state.expenses:
                st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)
            else:
                st.info("No transactions found.")

    # 5. CARE
    with t4:
        st.write("### 💧 Hydration")
        cols = st.columns(4)
        cl = []
        for i in range(4): cl.append(cols[i].checkbox(f"{i+1}", value=st.session_state.water_count >= i+1, key=f"w1_{i}"))
        cols2 = st.columns(4)
        for i in range(4): cl.append(cols2[i].checkbox(f"{i+5}", value=st.session_state.water_count >= i+5, key=f"w2_{i}"))
        
        nc = sum(cl)
        if nc != st.session_state.water_count:
             st.session_state.water_count = nc
             if nc > st.session_state.water_count:
                 play_sound_and_wait("pop")
             st.rerun()

        st.divider()
        st.write("### 📝 Journal")
        c_m, c_s = st.columns(2)
        c_m.selectbox("Mood", ["Happy 🙂", "Calm 😌", "Stressed 😫", "Sad 😢", "Angry 😠"])
        c_s.selectbox("Sleep", ["8+ Hours 💤", "6-7 Hours", "4-5 Hours", "Less than 4"])
        
        st.text_area("Gratitude", placeholder="I am thankful for...")
        if st.button("Save Log"):
            st.session_state.life_score += 5
            play_sound_and_wait("tada")
            st.success("Saved! (+5 XP)")
