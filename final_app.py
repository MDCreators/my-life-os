import streamlit as st
import pandas as pd
import datetime as dt
import pytz 
import streamlit.components.v1 as components 

# --- CONFIG ---
st.set_page_config(layout="centered", page_title="Life OS", page_icon="🌸")
ss = st.session_state # Short Alias for Session State

# --- FEEDBACK (Sound + Vibrate) ---
def run_fb():
    # 1. Vibrate
    vcode = """<script>
    if(navigator.vibrate) { navigator.vibrate([200]); }
    </script>"""
    components.html(vcode, height=0, width=0)
    # 2. Sound
    st.audio("https://www.soundjay.com/buttons/sounds/button-3.mp3", autoplay=True)

# --- STATE ---
if 'u_name' not in ss: ss.u_name = "User"
if 'water' not in ss: ss.water = 0
if 'money' not in ss: ss.money = 0 
if 'exp' not in ss: ss.exp = []
if 'score' not in ss: ss.score = 0
if 'habits' not in ss: ss.habits = [{"name": "Exercise", "s": 0}]
if 'goals' not in ss: 
    ss.goals = [{"t": "Goal 1", "d": False}, {"t": "Goal 2", "d": False}]

# --- AUTH ---
def check_auth():
    if "auth" not in ss:
        try: users = st.secrets["users"]
        except: 
            st.warning("⚠️ Setup Secrets [users]")
            return True 
        
        with st.form("Log"):
            st.write("### 🔐 Login")
            e = st.text_input("Email")
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("Go"):
                if e in users and users[e] == p:
                    ss.auth = True
                    ss.email = e
                    st.rerun()
                else: st.error("Wrong info")
        return False
    return True

# --- APP ---
if check_auth():
    # Time
    tz = pytz.timezone('Asia/Karachi')
    now = dt.datetime.now(tz)
    
    # CSS
    st.markdown("""<style>
    .stApp { background-color: #0E1117; color: white; }
    .stButton>button { background: #FF1493 !important; color: white !important; border: none; }
    audio { display: none; }
    </style>""", unsafe_allow_html=True)

    # Head
    st.caption(f"🗓️ {now.strftime('%d %B')} | ⏰ {now.strftime('%I:%M %p')}")
    st.title(f"Hi, {ss.u_name}! 🌙")
    st.write(f"**🌟 XP: {ss.score}**")

    # Tabs
    t1, t2, t3, t4, t5 = st.tabs(["🏠 Hub", "✅ Habits", "💰 Wallet", "🌿 Care", "⚙️ Set"])

    # 1. HUB
    with t1:
        st.write("### Focus 🎯")
        # Progress
        done = sum(1 for g in ss.goals if g['d'])
        total = len(ss.goals)
        if total > 0: st.progress(done/total)
        
        for i, g in enumerate(ss.goals):
            c1, c2 = st.columns([1, 8])
            with c1:
                if st.checkbox("", key=f"g{i}", value=g['d']):
                    if not g['d']:
                        ss.goals[i]['d'] = True
                        ss.score += 10
                        run_fb()
                        st.balloons()
                        st.rerun()
                else:
                    if g['d']:
                        ss.goals[i]['d'] = False
                        ss.score -= 10
                        st.rerun()
            with c2:
                ss.goals[i]['t'] = st.text_input(f"txt{i}", g['t'], label_visibility="collapsed")
        
        st.write("---")
        st.write(f"### 💧 Water: {ss.water}/8")
        st.progress(min(ss.water/8, 1.0))

    # 2. HABITS
    with t2:
        c_a, c_b = st.columns([3, 1])
        nh = c_a.text_input("New Habit", label_visibility="collapsed")
        if c_b.button("Add"):
            if nh:
                ss.habits.append({"name": nh, "s": 0})
                run_fb()
                st.rerun()
        
        for i, h in enumerate(ss.habits):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"**{h['name']}**")
            c2.write(f"🔥 {h['s']}")
            if c3.button("+1", key=f"h{i}"):
                ss.habits[i]['s'] += 1
                ss.score += 5
                run_fb()
                st.rerun()
            if c4.button("X", key=f"d{i}"):
                ss.habits.pop(i)
                st.rerun()

    # 3. WALLET
    with t3:
        st.metric("Savings", f"PKR {ss.money}")
        ta, tb = st.tabs(["Add", "List"])
        with ta:
            with st.form("fin"):
                item = st.text_input("Item")
                amt = st.number_input("Amount", min_value=0)
                typ = st.selectbox("Type", ["Expense", "Income"])
                if st.form_submit_button("Save"):
                    if typ == "Expense": ss.money -= amt
                    else: ss.money += amt
                    
                    ss.exp.append({
                        "Date": str(now.date()), 
                        "Item": item, 
                        "Amt": amt, 
                        "Type": typ
                    })
                    run_fb()
                    st.rerun()
        with tb:
            if ss.exp: st.dataframe(pd.DataFrame(ss.exp))

    # 4. CARE
    with t4:
        st.write("### Hydration")
        # Checkboxes for water
        cols = st.columns(4)
        cl = [] # check_list
        for i in range(4): 
            val = ss.water >= (i+1)
            cl.append(cols[i].checkbox(f"{i+1}", value=val, key=f"w1_{i}"))
            
        cols2 = st.columns(4)
        for i in range(4): 
            val = ss.water >= (i+5)
            cl.append(cols2[i].checkbox(f"{i+5}", value=val, key=f"w2_{i}"))
            
        # FIXED SHORT LOGIC
        nc = sum(cl) # nc = new_count
        if nc > ss.water:
             ss.water = nc
             run_fb()
             st.rerun()
                
        st.write("---")
        st.write("### Journal")
        st.select_slider("Mood", ["😞", "😐", "🙂", "🤩"])
        st.text_area("Gratitude")
        if st.button("Save Log"):
            ss.score += 5
            run_fb()
            st.success("Saved!")

    # 5. SET
    with t5:
        nn = st.text_input("Name", value=ss.u_name)
        if st.button("Update Profile"):
            ss.u_name = nn
            run_fb()
            st.rerun()
