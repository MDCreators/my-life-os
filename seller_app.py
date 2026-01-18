import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. PAGE CONFIG (Wide & Dark) ---
st.set_page_config(page_title="Seller HQ Pro", page_icon="⚡", layout="wide")

# --- 2. CUSTOM CSS (THE MAGIC) ---
# Ye wo code hay jo App ko khoobsurat banaye ga
st.markdown("""
<style>
    /* Main Background Setup */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Metrics Cards (Glassmorphism) */
    div.css-1r6slb0, div.stMetric {
        background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
        border: 1px solid #444;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div.stMetric:hover {
        transform: scale(1.02);
        border-color: #00FF7F;
    }
    
    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00C853 0%, #B2FF59 100%);
        color: black;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px #00C853;
        color: white;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input {
        background-color: #262730;
        color: white;
        border-radius: 8px;
        border: 1px solid #444;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #333;
    }
    
    /* Titles with Gradient */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #00FF7F, #00E5FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA SETUP ---
if 'db_orders' not in st.session_state:
    st.session_state.db_orders = pd.DataFrame(columns=[
        "Order ID", "Date", "Customer Name", "Phone", "City", 
        "Address", "Item", "Qty", "Price", "DC", "Total", 
        "Cost Price", "Status", "Courier", "Tracking ID"
    ])

if 'db_products' not in st.session_state:
    st.session_state.db_products = pd.DataFrame(columns=[
        "SKU", "Product Name", "Cost Price", "Sale Price", "Stock", "Category"
    ])

if 'db_expenses' not in st.session_state:
    st.session_state.db_expenses = pd.DataFrame(columns=[
        "Date", "Type", "Description", "Amount"
    ])

# --- HELPER FUNCTIONS ---
def get_kpis():
    if st.session_state.db_orders.empty:
        return 0, 0, 0, 0
    
    valid_orders = st.session_state.db_orders[st.session_state.db_orders['Status'].isin(['Delivered', 'Dispatched', 'Payment Received'])]
    revenue = valid_orders['Total'].sum()
    cogs = (valid_orders['Cost Price'] * valid_orders['Qty']).sum()
    
    rto_orders = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Returned (RTO)']
    rto_loss = rto_orders['DC'].sum() * 2
    
    expenses = st.session_state.db_expenses['Amount'].sum()
    net_profit = revenue - cogs - expenses - rto_loss
    
    return revenue, cogs, expenses + rto_loss, net_profit

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png", width=60)
    st.title("SELLER OS")
    st.markdown("---")
    
    menu = st.radio("NAVIGATION", [
        "📊 Dashboard", 
        "🛒 New Order (POS)", 
        "📦 Stockroom", 
        "🚚 Dispatch Center", 
        "💸 Finance & Ads"
    ])
    
    st.markdown("---")
    pending_count = len(st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Pending'])
    if pending_count > 0:
        st.error(f"🚨 {pending_count} Pending Orders!")
    else:
        st.success("✅ All Caught Up")

# ==========================
# 📊 DASHBOARD (THE PRO LOOK)
# ==========================
if menu == "📊 Dashboard":
    st.markdown("## 📈 Business Overview")
    
    rev, cost, exp, profit = get_kpis()
    
    # Custom HTML Cards (Is se look change hogi)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Revenue", f"Rs {rev:,.0f}", "+12%")
    col2.metric("📦 Product Cost", f"Rs {cost:,.0f}", "COGS")
    col3.metric("🔥 Burn (Ads/Ops)", f"Rs {exp:,.0f}", "Expense")
    col4.metric("💎 NET PROFIT", f"Rs {profit:,.0f}", "Real Cash")
    
    st.markdown("---")
    
    # Modern Charts
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Sales Trend & Performance")
        if not st.session_state.db_orders.empty:
            df_chart = st.session_state.db_orders.groupby("Date")["Total"].sum().reset_index()
            fig = px.area(df_chart, x="Date", y="Total", template="plotly_dark", color_discrete_sequence=['#00FF7F'])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for sales data...")
            
    with c2:
        st.subheader("Expense Breakdown")
        if not st.session_state.db_expenses.empty:
            fig2 = px.pie(st.session_state.db_expenses, values='Amount', names='Type', hole=0.6, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Teal)
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No expenses recorded yet.")

# ==========================
# 🛒 NEW ORDER (Clean Form)
# ==========================
elif menu == "🛒 New Order (POS)":
    st.markdown("## 📝 Create New Order")
    
    col_main, col_side = st.columns([2, 1])
    
    with col_side:
        st.info("💡 **Pro Tip:** Number pehlay daalain to Fraud Check khud ho jaye ga.")
        phone_val = st.text_input("Customer Phone", placeholder="0300xxxxxxx")
        
        # Live Fraud Check
        if phone_val:
            hist = st.session_state.db_orders[st.session_state.db_orders['Phone'] == phone_val]
            if not hist.empty:
                rto = len(hist[hist['Status'] == 'Returned (RTO)'])
                if rto > 0:
                    st.error(f"⚠️ HIGH RISK! {rto} Returns.")
                else:
                    st.success("✅ Safe Customer.")

    with col_main:
        with st.form("clean_order_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Customer Name")
            city = c2.selectbox("City", ["Lahore", "Karachi", "Islamabad", "Faisalabad", "Multan", "Other"])
            addr = st.text_area("Delivery Address", height=80)
            
            st.markdown("### Cart Details")
            if st.session_state.db_products.empty:
                st.warning("Inventory is empty! Go to Stockroom.")
                st.stop()
                
            p_list = st.session_state.db_products['Product Name'].unique()
            item_sel = st.selectbox("Select Item", p_list)
            
            # Auto Data
            p_data = st.session_state.db_products[st.session_state.db_products['Product Name'] == item_sel].iloc[0]
            
            sc1, sc2, sc3 = st.columns(3)
            qty = sc1.number_input("Qty", 1, 100, 1)
            price = sc2.number_input("Sale Price", value=int(p_data['Sale Price']))
            dc = sc3.number_input("Delivery", value=200)
            
            total_bill = (price * qty) + dc
            
            st.markdown(f"""
            <div style="background-color: #004D40; padding: 10px; border-radius: 5px; text-align: center; margin-top: 10px;">
                <h3 style="color: white; margin:0;">Total: Rs {total_bill}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("🚀 PLACE ORDER")
            
            if submitted:
                new_entry = {
                    "Order ID": f"ORD-{len(st.session_state.db_orders)+1001}",
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Customer Name": name, "Phone": phone_val, "City": city,
                    "Address": addr, "Item": item_sel, "Qty": qty,
                    "Price": price, "DC": dc, "Total": total_bill,
                    "Cost Price": p_data['Cost Price'], "Status": "Pending"
                }
                st.session_state.db_orders = pd.concat([st.session_state.db_orders, pd.DataFrame([new_entry])], ignore_index=True)
                st.success("Order Confirmed!")

# ==========================
# 📦 STOCKROOM (Inventory)
# ==========================
elif menu == "📦 Stockroom":
    st.markdown("## 🏭 Inventory Management")
    
    tab1, tab2 = st.tabs(["📋 Current Stock", "➕ Add New Item"])
    
    with tab1:
        # Fancy DataFrame
        st.dataframe(
            st.session_state.db_products,
            use_container_width=True,
            column_config={
                "Stock": st.column_config.ProgressColumn("Stock Level", format="%f", min_value=0, max_value=100),
                "Sale Price": st.column_config.NumberColumn("Price (Rs)", format="Rs %d")
            }
        )
        
    with tab2:
        with st.form("add_stock"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Product Name")
            sku = c2.text_input("SKU")
            c3, c4, c5 = st.columns(3)
            cost = c3.number_input("Cost", 0)
            sale = c4.number_input("Sale Price", 0)
            stock = c5.number_input("Stock Qty", 0)
            
            if st.form_submit_button("Save Item"):
                new_prod = {"SKU": sku, "Product Name": name, "Cost Price": cost, "Sale Price": sale, "Stock": stock, "Category": "General"}
                st.session_state.db_products = pd.concat([st.session_state.db_products, pd.DataFrame([new_prod])], ignore_index=True)
                st.success(f"{name} added to stock!")

# ==========================
# 🚚 DISPATCH CENTER
# ==========================
elif menu == "🚚 Dispatch Center":
    st.markdown("## 🚛 Order Operations")
    
    st.markdown("#### Pending Orders")
    pending = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Pending']
    
    if not pending.empty:
        for idx, row in pending.iterrows():
            with st.expander(f"{row['Order ID']} | {row['Customer Name']} | Rs {row['Total']}"):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**Item:** {row['Item']} (x{row['Qty']})")
                c1.write(f"**Address:** {row['Address']}, {row['City']}")
                
                # Action Buttons
                col_btn1, col_btn2, col_btn3 = c2.columns(3)
                
                # WhatsApp
                wa_link = f"https://wa.me/92{str(row['Phone'])[1:]}?text=Salam {row['Customer Name']}, order confirm karein?"
                col_btn1.link_button("💬", wa_link)
                
                if col_btn2.button("✅", key=f"ok_{idx}"):
                    real_idx = st.session_state.db_orders[st.session_state.db_orders['Order ID'] == row['Order ID']].index[0]
                    st.session_state.db_orders.at[real_idx, 'Status'] = 'Dispatched'
                    st.rerun()
                    
                if col_btn3.button("❌", key=f"no_{idx}"):
                    real_idx = st.session_state.db_orders[st.session_state.db_orders['Order ID'] == row['Order ID']].index[0]
                    st.session_state.db_orders.at[real_idx, 'Status'] = 'Cancelled'
                    st.rerun()
    else:
        st.info("No pending orders. Chill karein! ☕")

# ==========================
# 💸 FINANCE (Ads Tracker)
# ==========================
elif menu == "💸 Finance & Ads":
    st.markdown("## 📉 Expense & Ads Tracker")
    
    with st.expander("➕ Add New Expense", expanded=True):
        with st.form("exp_input"):
            c1, c2, c3 = st.columns(3)
            date = c1.date_input("Date")
            cat = c2.selectbox("Category", ["Meta Ads", "Packaging", "Salary", "Food", "RTO Charges"])
            amt = c3.number_input("Amount", 100)
            
            if st.form_submit_button("Add Expense"):
                new_exp = {"Date": date, "Type": cat, "Description": "-", "Amount": amt}
                st.session_state.db_expenses = pd.concat([st.session_state.db_expenses, pd.DataFrame([new_exp])], ignore_index=True)
                st.success("Added!")
    
    if not st.session_state.db_expenses.empty:
        st.dataframe(st.session_state.db_expenses, use_container_width=True)
