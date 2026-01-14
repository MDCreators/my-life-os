import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Aimen's Life OS", page_icon="🌸", layout="centered")

# Initialize Session State
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

# --- 2. DARK THEME & BUTTON FIXES ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* FIX: BUTTON VISIBILITY */
    .stButton > button {
        color: white !important;
        background-color: #FF1493 !important; /* Bright Pink */
        border-radius: 12px;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #FF69B4 !important; /* Lighter Pink on Hover */
        transform: scale(1.05); /* Slight pop effect */
    }
    
    /* Inputs */
    .stTextInput>div>div>input { 
        background-color: #262730; color: white !important; 
        border-radius: 10px; border: 1px solid #555; 
    }
    /* Labels */
    label { color: #FFB6C1 !important; font-weight: bold; }
    
    /* Text Colors */
    .big-score { font-size: 24px; font-weight: bold; color: #00FF7F; text-align: center; margin-bottom: 20px;}
    .streak-num { font-size: 28px; font-weight: bold; color: #00BFFF; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1E1E1E; color: white; border-radius: 5px; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #FF1493; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TABS ---
tab_setup, tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Setup", "🏠 Main Hub", "✅ Habits", "💰 Finance", "🌿 Self-Care"])

# === TAB 0: SETUP ===
with tab_setup:
    st.subheader("User Profile ⚙️")
    new_name = st.text_input("What should I call you?", value=st.session_state.user_name)
    if st.button("Save Profile"):
        st.session_state.user_name = new_name
        st.toast("Saved!", icon="✅")
        st.rerun()

# === TAB 1: MAIN HUB ===
with tab1:
    now = datetime.now()
    dt_string = now.strftime("%A, %d %B")
    tm_string = now.strftime("%I:%M %p")
    
    st.markdown(f"<p style='text-align: center; color: #888;'>🗓️ {dt_string} | ⏰ {tm_string}</p>", unsafe_allow_html=True)
    
    curr_hour = datetime.now().hour
    if 5 <= curr_hour < 12: greeting = "Good Morning"
    elif 12 <= curr_hour < 17: greeting = "Good Afternoon"
    elif 17 <= curr_hour < 21: greeting = "Good Evening"
    else: greeting = "Good Night"

    st.markdown(f"<h1 style='text-align: center;'>{greeting}, {st.session_state.user_name}! 🌙</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-score'>🌟 Life Score: {st.session_state.life_score} XP</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Goals
    st.subheader("Today's Focus 🎯")
    goals_done_count = sum([1 for g in st.session_state.goals if g['done']])
    st.progress(goals_done_count / 3)
    
    for i, goal in enumerate(st.session_state.goals):
        c1, c2 = st.columns([1, 8])
        with c1:
            if st.checkbox("", key=f"g_check_{i}", value=goal['done']):
                if not goal['done']:
                    st.session_state.goals[i]['done'] = True
                    st.session_state.life_score += 10
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
    
    # Hydration
    st.subheader("Hydration Tracker 💧")
    progress = min(st.session_state.water_count / 8, 1.0)
    st.progress(progress)
    st.caption(f"Status: {st.session_state.water_count} / 8 Glasses")

# === TAB 2: HABITS (Counter Logic Fixed) ===
with tab2:
    st.subheader("Habit Tracker ✨")
    
    # Add Habit Input Visibility Fix
    c_in, c_btn = st.columns([3, 1])
    with c_in: 
        new_h = st.text_input("Add new habit here:", placeholder="e.g. Gym", label_visibility="visible")
    with c_btn: 
        st.write("") # Spacing for alignment
        st.write("")
        if st.button("➕ Add"):
            if new_h:
                st.session_state.habits.append({"name": new_h, "streak": 0})
                st.rerun()

    st.write("---")

    for i, habit in enumerate(st.session_state.habits):
        with st.container():
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
            
            with col1:
                st.markdown(f"### {habit['name']}")
            
            with col2:
                # Big Neon Number
                st.markdown(f"<span class='streak-num'>{habit['streak']} 🔥</span>", unsafe_allow_html=True)
            
            with col3:
                # LOGIC CHANGE: Just keeps adding (Counter Style)
                if st.button("➕ 1", key=f"h_inc_{i}"):
                    st.session_state.habits[i]['streak'] += 1  
                    st.session_state.life_score += 5
                    st.toast(f"{habit['name']} +1!", icon="🔥")
                    st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"h_del_{i}"):
                    st.session_state.habits.pop(i)
                    st.rerun()
            st.markdown("---")

# === TAB 3: FINANCE (15+ Categories) ===
with tab3:
    st.subheader("Wallet & Savings 💰")
    color = "#00FF7F" if st.session_state.total_savings >= 0 else "#FF4500"
    st.markdown(f"<h1 style='text-align: center; color: {color};'>PKR {st.session_state.total_savings}</h1>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📝 Transaction", "📊 Charts", "📜 History"])
    
    exp_cats = ["🍔 Food/Dining", "🏠 Rent/Housing", "🚗 Transport", "🛒 Groceries", "🛍️ Shopping", 
                "💡 Utilities/Bills", "💊 Medical", "🎓 Education", "🎉 Entertainment", "✈️ Travel", 
                "🎁 Gifts", "🙏 Charity", "💅 Self-Care", "🔧 Repairs", "💻 Subscriptions", "💸 Debt", "📝 Other"]
    
    inc_cats = ["💼 Salary", "💻 Freelance", "📈 Business Profit", "🎁 Gift Received", "🏠 Rental Income", 
                "💵 Dividends", "💰 Bonus", "🪙 Crypto", "🤝 Side Hustle", "🔄 Refund", 
                "🏦 Interest", "👴 Pension", "🎒 Allowance", "📝 Other"]

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            with st.form("ex_form"):
                st.write("**Add Expense 💸**")
                item = st.text_input("Item Name")
                cat = st.selectbox("Category", exp_cats)
                amt = st.number_input("Amount", min_value=0, key="ex_amt")
                if st.form_submit_button("Spend"):
                    st.session_state.total_savings -= amt
                    txn_date = datetime.now().strftime("%Y-%m-%d")
                    st.session_state.expenses.append({"Date": txn_date, "Type": "Expense", "Item": item, "Amount": amt, "Category": cat})
                    st.toast(f"Spent {amt}!", icon="💸")
                    st.rerun()
        with c2:
            with st.form("in_form"):
                st.write("**Add Income 💰**")
                src = st.text_input("Source Name")
                cat_in = st.selectbox("Category", inc_cats)
                amt_in = st.number_input("Amount", min_value=0, key="in_amt")
                if st.form_submit_button("Deposit"):
                    st.session_state.total_savings += amt_in
                    txn_date = datetime.now().strftime("%Y-%m-%d")
                    st.session_state.expenses.append({"Date": txn_date, "Type": "Income", "Item": src, "Amount": amt_in, "Category": cat_in})
                    st.toast("Money Added!", icon="💰")
                    st.rerun()
    
    with t2:
        if st.session_state.expenses:
            df = pd.DataFrame(st.session_state.expenses)
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption("Expenses")
                df_ex = df[df["Type"] == "Expense"]
                if not df_ex.empty:
                    fig1 = px.pie(df_ex, values='Amount', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
                    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
                    st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                st.caption("Income")
                df_in = df[df["Type"] == "Income"]
                if not df_in.empty:
                    fig2 = px.pie(df_in, values='Amount', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)
        else: st.info("Add data to see charts.")
    
    with t3:
        if st.session_state.expenses:
            df_hist = pd.DataFrame(st.session_state.expenses)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else: st.info("No transactions found.")

# === TAB 4: SELF CARE ===
with tab4:
    st.subheader("Daily Water Intake 💧")
    cols = st.columns(4)
    w1 = cols[0].checkbox("1", value=st.session_state.water_count >= 1)
    w2 = cols[1].checkbox("2", value=st.session_state.water_count >= 2)
    w3 = cols[2].checkbox("3", value=st.session_state.water_count >= 3)
    w4 = cols[3].checkbox("4", value=st.session_state.water_count >= 4)
    cols2 = st.columns(4)
    w5 = cols2[0].checkbox("5", value=st.session_state.water_count >= 5)
    w6 = cols2[1].checkbox("6", value=st.session_state.water_count >= 6)
    w7 = cols2[2].checkbox("7", value=st.session_state.water_count >= 7)
    w8 = cols2[3].checkbox("8", value=st.session_state.water_count >= 8)
    
    new_count = sum([w1, w2, w3, w4, w5, w6, w7, w8])
    if new_count != st.session_state.water_count:
        if new_count > st.session_state.water_count: st.session_state.life_score += 2
        st.session_state.water_count = new_count
        st.rerun()

    st.divider()
    c_mood, c_sleep = st.columns(2)
    with c_mood: st.selectbox("Mood", ["Happy 🙂", "Calm 😌", "Stressed 😫", "Sad 😢", "Excited 🤩"])
    with c_sleep: st.selectbox("Sleep", ["8+ Hours 💤", "6-7 Hours", "4-5 Hours", "Less than 4"])
    
    st.text_area("Gratitude Journal 📝")
    if st.button("Save Entry"):
        st.session_state.life_score += 5
        st.balloons()
        st.success("Saved! (+5 XP)")

    st.divider()
    quotes = ["Believe in yourself.", "Focus on the good.", "One day at a time.", "You are enough."]
    idx = datetime.now().minute % len(quotes)
    st.markdown(f"### 💭 *{quotes[idx]}*")