import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 0. LOGIN SYSTEM ---
def check_password():
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            st.session_state["logged_in_user"] = st.session_state["username"]
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align:center; color:#4CAF50;'>🇵🇰 Dukaan Pro Login</h1>", unsafe_allow_html=True)
        st.text_input("Mobile / Email", key="username")
        st.text_input("Pin Code", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Mobile / Email", key="username")
        st.text_input("Pin Code", type="password", on_change=password_entered, key="password")
        st.error("🔒 Galat Password")
        return False
    else:
        return True

# --- 1. CONFIG & AUTH ---
st.set_page_config(page_title="Dukaan Pro", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

if not check_password():
    st.stop()

current_user = st.session_state["logged_in_user"]

# --- 2. FIREBASE CONNECTION ---
if not firebase_admin._apps:
    try:
        key_content = st.secrets["firebase"]["my_key"]
        key_dict = json.loads(key_content)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"🚨 DB Error: {e}")
        st.stop()

db = firestore.client()

# --- 3. DATABASE FUNCTIONS (UPDATED) ---
def get_products():
    docs = db.collection("products").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def add_product(name, price, cost, stock, category):
    db.collection("products").add({
        "name": name, "price": int(price), "cost": int(cost), 
        "stock": int(stock), "category": category
    })

def update_stock(product_id, qty_sold):
    ref = db.collection("products").document(product_id)
    curr = ref.get().to_dict()
    if curr and 'stock' in curr:
        new_stock = int(curr['stock']) - int(qty_sold)
        ref.update({"stock": new_stock})

def log_sale(items, subtotal, discount, final_total, profit, customer, payment_mode):
    tz = pytz.timezone('Asia/Karachi')
    db.collection("sales").add({
        "date": str(datetime.now(tz)),
        "items": items,
        "subtotal": int(subtotal),
        "discount": int(discount),
        "total": int(final_total),
        "profit": int(profit),
        "customer": customer,
        "mode": payment_mode, # Cash or Udhaar
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def log_expense(desc, amount, category):
    tz = pytz.timezone('Asia/Karachi')
    db.collection("expenses").add({
        "date": str(datetime.now(tz)),
        "desc": desc,
        "amount": int(amount),
        "category": category,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_sales():
    docs = db.collection("sales").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def get_expenses():
    docs = db.collection("expenses").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# --- 4. DESI UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap');
    
    .stApp { background-color: #f0f2f6; font-family: 'Poppins', sans-serif; color: #333; }
    
    .metric-card {
        background: white;
        padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-top: 5px solid #4CAF50;
        margin-bottom: 20px; text-align: center;
    }
    .metric-title { font-size: 14px; color: #666; font-weight: 500; }
    .metric-val { font-size: 28px; font-weight: 700; color: #2E7D32; }
    
    .sidebar-text { font-size: 18px; font-weight: bold; color: #1E88E5; }
    
    .stButton>button { 
        background: linear-gradient(90deg, #4CAF50 0%, #2E7D32 100%);
        color: white; border: none; border-radius: 10px; height: 50px; font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { transform: scale(1.02); }
    
    /* Input Fields */
    .stTextInput>div>div>input { border-radius: 10px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("## 🏪 Dukaan Pro")
    st.caption(f"Manager: {current_user.split('@')[0]}")
    st.write("---")
    menu = st.radio("Main Menu", 
        ["📊 Karobaar (Dashboard)", 
         "🛒 Sale Point (POS)", 
         "📒 Udhaar Khata", 
         "📦 Maal (Inventory)", 
         "💸 Kharcha (Expenses)"])
    
    st.write("---")
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- 6. APP MODULES ---

# === DASHBOARD (KAROBAAR) ===
if menu == "📊 Karobaar (Dashboard)":
    st.subheader("Aaj ki Situation 📈")
    
    sales_data = get_sales()
    expenses_data = get_expenses()
    
    total_rev = 0
    total_profit = 0
    total_udhaar = 0
    total_expense = 0
    
    if sales_data:
        df_sales = pd.DataFrame(sales_data)
        total_rev = df_sales['total'].sum()
        total_profit = df_sales['profit'].sum()
        # Calculate Udhaar
        udhaar_df = df_sales[df_sales['mode'] == 'Udhaar']
        if not udhaar_df.empty:
            total_udhaar = udhaar_df['total'].sum()

    if expenses_data:
        df_exp = pd.DataFrame(expenses_data)
        total_expense = df_exp['amount'].sum()
        
    net_profit = total_profit - total_expense

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><div class='metric-title'>Total Galla (Sales)</div><div class='metric-val'>Rs {total_rev:,}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card' style='border-color:#F44336;'><div class='metric-title'>Market Udhaar</div><div class='metric-val' style='color:#F44336;'>Rs {total_udhaar:,}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='border-color:#FFC107;'><div class='metric-title'>Dukaan Kharcha</div><div class='metric-val' style='color:#FFC107;'>Rs {total_expense:,}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><div class='metric-title'>Asal Munafa (Net)</div><div class='metric-val'>Rs {net_profit:,}</div></div>", unsafe_allow_html=True)

    st.write("### 📅 Sales Trend")
    if sales_data:
        # Group by Date
        df_sales['date_only'] = df_sales['date'].apply(lambda x: x.split(" ")[0])
        daily_sales = df_sales.groupby('date_only')['total'].sum().reset_index()
        fig = px.bar(daily_sales, x='date_only', y='total', color_discrete_sequence=['#4CAF50'])
        st.plotly_chart(fig, use_container_width=True)

# === POS (SALE POINT) ===
elif menu == "🛒 Sale Point (POS)":
    st.subheader("Nayi Sale Lagayen 🧾")
    
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    products = get_products()
    p_names = [p['name'] for p in products if p['stock'] > 0]
    
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        with st.container(border=True):
            st.markdown("##### 🛍️ Add Item")
            sel_p_name = st.selectbox("Product", ["Select..."] + p_names)
            
            if sel_p_name != "Select...":
                sel_p = next(p for p in products if p['name'] == sel_p_name)
                st.caption(f"Price: {sel_p['price']} | Stock: {sel_p['stock']}")
                qty = st.number_input("Tadaad (Qty)", min_value=1, max_value=int(sel_p['stock']), value=1)
                
                if st.button("Cart main daalen ➕"):
                    st.session_state.cart.append({
                        "id": sel_p['id'], "name": sel_p['name'], 
                        "price": int(sel_p['price']), "cost": int(sel_p['cost']), "qty": int(qty),
                        "subtotal": int(sel_p['price']) * int(qty),
                        "profit_item": (int(sel_p['price']) - int(sel_p['cost'])) * int(qty)
                    })
                    st.success(f"{qty} {sel_p['name']} added!")

    with c2:
        with st.container(border=True):
            st.markdown("##### 🧾 Bill Detail")
            if st.session_state.cart:
                cart_df = pd.DataFrame(st.session_state.cart)
                st.dataframe(cart_df[['name', 'qty', 'subtotal']], hide_index=True)
                
                # Calculation
                sub_total = int(cart_df['subtotal'].sum())
                profit_gross = int(cart_df['profit_item'].sum())
                
                discount = st.number_input("Discount (Kam kiye)", min_value=0, max_value=sub_total)
                final_total = sub_total - discount
                final_profit = profit_gross - discount # Profit kam hoga discount se
                
                st.markdown(f"### Total: Rs {final_total}")
                
                # Payment Mode
                pay_mode = st.radio("Payment Type", ["Cash 💵", "Udhaar 📕"], horizontal=True)
                cust_name = st.text_input("Customer Name (Zaroori for Udhaar)")
                
                if st.button("✅ Sale Complete Karein"):
                    if pay_mode == "Udhaar 📕" and not cust_name:
                        st.error("Udhaar ke liye naam likhna zaroori hay!")
                    else:
                        # 1. Stock Update
                        for item in st.session_state.cart:
                            update_stock(item['id'], item['qty'])
                        
                        # 2. Sale Log
                        log_sale(st.session_state.cart, sub_total, discount, final_total, final_profit, cust_name, "Udhaar" if "Udhaar" in pay_mode else "Cash")
                        
                        # 3. WhatsApp Link Logic
                        msg_text = f"Salam {cust_name}! Apka bill Rs {final_total} hay. Shukriya!"
                        wa_link = f"https://wa.me/?text={msg_text}"
                        
                        st.session_state.cart = []
                        st.balloons()
                        st.success("Sale Ho Gayi!")
                        st.markdown(f"[📲 Send Bill on WhatsApp]({wa_link})")
                        time.sleep(2)
                        st.rerun()
                
                if st.button("❌ Cancel"):
                    st.session_state.cart = []
                    st.rerun()
            else:
                st.info("Cart khali hay.")

# === UDHAAR KHATA ===
elif menu == "📒 Udhaar Khata":
    st.subheader("Udhaar Ki List 📕")
    
    sales = get_sales()
    if sales:
        df = pd.DataFrame(sales)
        udhaar_only = df[df['mode'] == 'Udhaar']
        
        if not udhaar_only.empty:
            # Group by Customer to see total pending
            summary = udhaar_only.groupby('customer')['total'].sum().reset_index()
            summary.columns = ['Customer Name', 'Pending Amount']
            
            st.dataframe(summary, use_container_width=True)
            
            st.write("### Recent Udhaar Transactions")
            st.dataframe(udhaar_only[['date', 'customer', 'total', 'items']], hide_index=True)
        else:
            st.success("Koi Udhaar baqi nahi! Zabardast.")
    else:
        st.info("No data.")

# === INVENTORY ===
elif menu == "📦 Maal (Inventory)":
    st.subheader("Dukaan Ka Maal 📦")
    
    with st.expander("Naya Maal Add Karein (New Stock)"):
        with st.form("add_stock"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Cheez ka Naam")
            cat = c2.selectbox("Category", ["Rashan", "Electronics", "General", "Mobile"])
            price = c1.number_input("Bechni Kitne ki? (Sale Price)", min_value=0)
            cost = c2.number_input("Aayi Kitne ki? (Cost Price)", min_value=0)
            stock = st.number_input("Tadaad (Qty)", min_value=1)
            
            if st.form_submit_button("Save Stock"):
                add_product(name, price, cost, stock, cat)
                st.success(f"{name} added!")
                time.sleep(1)
                st.rerun()
    
    products = get_products()
    if products:
        df = pd.DataFrame(products)
        # Low Stock Warning
        low_stock = df[df['stock'] < 5]
        if not low_stock.empty:
            st.error(f"⚠️ Warning: {len(low_stock)} items khatam honay walay hain!")
        
        st.dataframe(df, use_container_width=True)

# === EXPENSES ===
elif menu == "💸 Kharcha (Expenses)":
    st.subheader("Roznamcha (Daily Expenses) 💸")
    
    with st.form("add_exp"):
        c1, c2 = st.columns(2)
        desc = c1.text_input("Kahan kharch hua? (e.g. Chai, Bill)")
        amt = c2.number_input("Amount", min_value=1)
        cat = st.selectbox("Type", ["Food/Chai", "Shop Rent", "Electricity", "Load/Net", "Other"])
        
        if st.form_submit_button("Add Kharcha"):
            log_expense(desc, amt, cat)
            st.success("Expense Added")
            time.sleep(1)
            st.rerun()
            
    st.write("### Recent Expenses")
    exps = get_expenses()
    if exps:
        st.dataframe(pd.DataFrame(exps)[['date', 'desc', 'amount', 'category']], use_container_width=True)
