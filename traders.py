import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
import gspread
from google.oauth2.service_account import Credentials

# --- 1. PROFESSIONAL CONFIG (No Branding) ---
st.set_page_config(page_title="SI Traders System", page_icon="⚖️", layout="wide")

# CSS to Hide Streamlit Branding & Make App Look Native
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp { background-color: #f4f6f9; }
        
        /* Custom Cards for Totals */
        .metric-card {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #2e7d32; /* Green */
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-title { font-size: 14px; color: #555; }
        .metric-value { font-size: 24px; font-weight: bold; color: #000; }
        
        /* Red Border for Sales */
        .sale-card { border-left: 5px solid #c62828; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GOOGLE SHEETS CONNECTION ---
def get_connection():
    # Wohi Master Key use karein jo Secrets mein hay
    if "service_account" not in st.secrets:
        st.error("🚨 Secrets file mein key nahi mili!")
        st.stop()
    
    # Connect
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    # ⚠️ NOTE: Yahan apni NEW Google Sheet ka naam likhein
    return client.open("SI Traders Data") 

# --- 3. HELPER FUNCTIONS ---
def load_data(tab):
    try:
        ws = get_connection().worksheet(tab)
        return pd.DataFrame(ws.get_all_records())
    except: return pd.DataFrame()

def save_data(tab, row_data):
    try:
        ws = get_connection().worksheet(tab)
        ws.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- 4. MAIN APP ---
st.title("⚖️ SI Traders Management")

# Tabs for Navigation (Jaisa Excel mein neechay hota hay)
tab_buy, tab_sell, tab_close = st.tabs(["🟢 Khareedari (Purchase)", "🔴 Farokht (Sale)", "📒 Closing / Profit"])

# === TAB 1: KHAREEDARI (PURCHASE) ===
with tab_buy:
    st.subheader("Khareedari Entry")
    
    # 1. Form
    with st.form("buy_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        party = c1.text_input("Party Name (e.g. Bhai)")
        weight = c2.number_input("Weight (Wazan)", min_value=0.0, format="%.2f")
        rate = c3.number_input("Rate", min_value=0)
        details = st.text_input("Details / Item")
        
        # Auto Calculate Amount
        amount = weight * rate
        st.caption(f"💰 Total Amount: {amount:,.0f}")
        
        if st.form_submit_button("📥 Save Purchase"):
            pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            save_data("Purchase", [pk_time, party, weight, rate, amount, details])
            st.success("Saved!")
            st.rerun()

    # 2. View Data & Totals
    df_buy = load_data("Purchase")
    if not df_buy.empty:
        # Top Totals Bar (Jaisa image mein upar total likha hay)
        t_w = df_buy["Weight"].sum()
        t_a = df_buy["Amount"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><div class='metric-title'>Total Weight</div><div class='metric-value'>{t_w:,.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-title'>Total Amount</div><div class='metric-value'>{t_a:,.0f}</div></div>", unsafe_allow_html=True)
        
        st.markdown("### 📋 Record List")
        st.dataframe(df_buy, use_container_width=True)

# === TAB 2: FAROKHT (SALE) ===
with tab_sell:
    st.subheader("Farokht Entry")
    
    # 1. Form
    with st.form("sell_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1,1,1])
        cust = c1.text_input("Customer Name (e.g. Bawani)")
        bill_no = c2.text_input("Bill No")
        weight = c3.number_input("Weight", min_value=0.0, format="%.2f")
        
        c4, c5 = st.columns(2)
        rate = c4.number_input("Rate", min_value=0)
        details = c5.text_input("Details")
        
        amount = weight * rate
        st.caption(f"💰 Bill Amount: {amount:,.0f}")
        
        if st.form_submit_button("📤 Save Sale"):
            pk_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d")
            save_data("Sale", [pk_time, cust, bill_no, weight, rate, amount, details])
            st.success("Sold!")
            st.rerun()

    # 2. View Data
    df_sell = load_data("Sale")
    if not df_sell.empty:
        t_w = df_sell["Weight"].sum()
        t_a = df_sell["Amount"].sum()
        
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card sale-card'><div class='metric-title'>Sold Weight</div><div class='metric-value'>{t_w:,.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card sale-card'><div class='metric-title'>Sold Amount</div><div class='metric-value'>{t_a:,.0f}</div></div>", unsafe_allow_html=True)
        
        st.dataframe(df_sell, use_container_width=True)

# === TAB 3: CLOSING (PROFIT/LOSS) ===
with tab_close:
    st.header("📒 Daily Closing")
    
    # Load Data
    df_b = load_data("Purchase")
    df_s = load_data("Sale")
    
    # Calculate Totals
    buy_w = df_b["Weight"].sum() if not df_b.empty else 0
    buy_amt = df_b["Amount"].sum() if not df_b.empty else 0
    
    sell_w = df_s["Weight"].sum() if not df_s.empty else 0
    sell_amt = df_s["Amount"].sum() if not df_s.empty else 0
    
    # Net Calculations (Logic from Image 3)
    closing_w = sell_w - buy_w  # Net Weight (Negative means Bought < Sold?)
    closing_amt = sell_amt - buy_amt # Net Profit/Loss
    
    # Display Big Numbers
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Closing Weight", f"{closing_w:,.1f}")
    c2.metric("Closing Amount (Profit)", f"Rs {closing_amt:,.0f}", delta_color="normal")
    
    # Average Rate Calculation
    avg_rate = 0
    if closing_w != 0:
        avg_rate = closing_amt / closing_w
    c3.metric("Avg Rate", f"{avg_rate:.2f}")
    
    st.markdown("---")
    
    # Profit Distribution (Imran Ali & Salman Khan)
    st.subheader("💰 Profit Distribution")
    
    # Hardcoded Partners (Ya Sheet se bhi la saktay hain)
    partners = ["Imran Ali", "Salman Khan"]
    if closing_amt != 0:
        share = closing_amt / 2  # 50-50 Split
        
        cols = st.columns(2)
        for idx, p in enumerate(partners):
            cols[idx].success(f"**{p}**: Rs {share:,.2f}")
    else:
        st.info("Abhi koi profit nahi hua.")
