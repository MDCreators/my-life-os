import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# ==========================================
# 1. APP CONFIGURATION (Must be first)
# ==========================================
st.set_page_config(
    page_title="Seller OS: Enterprise",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED STYLING (CSS)
# ==========================================
st.markdown("""
<style>
    /* Main Theme */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Neon Cards */
    div[data-testid="metric-container"] {
        background-color: #111111;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 0 10px rgba(0, 255, 127, 0.1);
        transition: all 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(0, 255, 127, 0.4);
        border-color: #00FF7F;
    }
    
    /* Custom Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #222;
    }
    
    /* Gradient Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #FF0080, #7928CA);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        opacity: 0.9;
        box-shadow: 0 0 15px rgba(255, 0, 128, 0.5);
    }
    
    /* Success Messages */
    .stSuccess {
        background-color: rgba(0, 255, 127, 0.1);
        border-left: 5px solid #00FF7F;
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #333;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE (Database)
# ==========================================
if 'db_orders' not in st.session_state:
    # Sample Data for Demo
    sample_data = [
        {"Order ID": "ORD-1001", "Date": "2024-01-20", "Customer": "Ali Khan", "City": "Lahore", "Item": "Gaming Mouse", "Qty": 1, "Total": 2500, "Status": "Delivered", "Source": "Facebook"},
        {"Order ID": "ORD-1002", "Date": "2024-01-21", "Customer": "Sara Ahmed", "City": "Karachi", "Item": "Headphones", "Qty": 2, "Total": 6000, "Status": "Pending", "Source": "Instagram"},
    ]
    st.session_state.db_orders = pd.DataFrame(sample_data)

if 'db_products' not in st.session_state:
    st.session_state.db_products = pd.DataFrame([
        {"SKU": "GM-01", "Name": "Gaming Mouse", "Cost": 1500, "Price": 2500, "Stock": 15},
        {"SKU": "HP-02", "Name": "Headphones", "Cost": 2000, "Price": 3000, "Stock": 8},
        {"SKU": "KB-03", "Name": "RGB Keyboard", "Cost": 3500, "Price": 5500, "Stock": 3}, # Low Stock
    ])

if 'daily_target' not in st.session_state:
    st.session_state.daily_target = 50000

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.title("💎 Seller OS")
    st.caption("Enterprise Edition v2.0")
    
    # User Profile (Fake)
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="https://ui-avatars.com/api/?name=Dawood+Boss&background=random" style="border-radius: 50%; width: 40px; margin-right: 10px;">
        <div>
            <h4 style="margin:0;">Dawood</h4>
            <small style="color: #00FF7F;">● Online</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio("MAIN MENU", [
        "🚀 Command Center", 
        "🛒 New Order (POS)", 
        "📦 Inventory Hub", 
        "🚚 Order Operations", 
        "💰 Financials"
    ])
    
    st.divider()
    
    # 🎯 Daily Target Widget
    st.markdown("### 🎯 Today's Goal")
    today_sales = st.session_state.db_orders[st.session_state.db_orders['Date'] == datetime.now().strftime("%Y-%m-%d")]['Total'].sum()
    progress = min(today_sales / st.session_state.daily_target, 1.0)
    st.progress(progress)
    st.caption(f"PKR {today_sales:,} / {st.session_state.daily_target:,}")
    
    if progress >= 1.0:
        st.balloons()

# ==========================================
# 5. MAIN PAGES
# ==========================================

# --- 🚀 COMMAND CENTER (Dashboard) ---
if menu == "🚀 Command Center":
    st.markdown("# 🚀 Business Overview")
    st.markdown(f"**{datetime.now().strftime('%A, %d %B %Y')}**")
    
    # Top Stats Cards
    total_rev = st.session_state.db_orders['Total'].sum()
    total_orders = len(st.session_state.db_orders)
    pending_orders = len(st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Pending'])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Revenue", f"PKR {total_rev:,}", "+15%")
    c2.metric("📦 Total Orders", total_orders, "+4")
    c3.metric("⏳ Pending Dispatch", pending_orders, delta_color="inverse")
    c4.metric("🔥 Conversion Rate", "3.2%", "+0.5%")
    
    st.divider()
    
    # Charts Section
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("📈 Sales Performance")
        # Fake hourly data generation for graph feel
        chart_data = pd.DataFrame({
            "Time": ["9 AM", "12 PM", "3 PM", "6 PM", "9 PM"],
            "Sales": [5000, 12000, 8000, 25000, 15000]
        })
        fig = px.area(chart_data, x="Time", y="Sales", template="plotly_dark", color_discrete_sequence=["#00FF7F"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
    with col_chart2:
        st.subheader("🏙️ Top Cities")
        if not st.session_state.db_orders.empty:
            city_counts = st.session_state.db_orders['City'].value_counts()
            fig2 = px.pie(values=city_counts.values, names=city_counts.index, hole=0.6, template="plotly_dark")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

# --- 🛒 NEW ORDER (POS Style) ---
elif menu == "🛒 New Order (POS)":
    st.markdown("# 🛒 Create Order")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_right:
        st.info("💡 **Customer Insights**")
        phone = st.text_input("📞 Phone Number", placeholder="0300-1234567")
        if phone:
            st.success("✅ New Customer (No Fraud History)")
            # Agar purana customer hota to yahan history aati
            
    with col_left:
        with st.form("pos_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("👤 Customer Name")
            city = c2.selectbox("🏙️ City", ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Peshawar", "Other"])
            address = st.text_area("🏠 Complete Address")
            
            st.markdown("---")
            st.subheader("🛍️ Cart")
            
            # Product Selector
            prod_names = st.session_state.db_products['Name'].tolist()
            selected_prod = st.selectbox("Select Product", prod_names)
            
            # Auto-Fetch Details
            p_details = st.session_state.db_products[st.session_state.db_products['Name'] == selected_prod].iloc[0]
            
            qc1, qc2, qc3 = st.columns(3)
            qty = qc1.number_input("Quantity", 1, 10, 1)
            price = qc2.number_input("Unit Price", value=int(p_details['Price']))
            dc = qc3.number_input("Delivery Charges", value=200)
            
            total = (price * qty) + dc
            
            # Big Total Display
            st.markdown(f"""
            <div style="background:#222; padding:15px; border-radius:10px; text-align:center; border: 1px solid #444;">
                <h2 style="color:#00FF7F; margin:0;">TOTAL: PKR {total:,}</h2>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            
            if st.form_submit_button("✅ CONFIRM ORDER"):
                new_order = {
                    "Order ID": f"ORD-{random.randint(2000, 9999)}",
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Customer": name, "City": city, "Item": selected_prod,
                    "Qty": qty, "Total": total, "Status": "Pending", "Source": "Manual"
                }
                st.session_state.db_orders = pd.concat([st.session_state.db_orders, pd.DataFrame([new_order])], ignore_index=True)
                st.balloons()
                st.success("Order Placed Successfully!")

# --- 📦 INVENTORY HUB ---
elif menu == "📦 Inventory Hub":
    st.markdown("# 📦 Inventory Management")
    
    # Low Stock Alert
    low_stock = st.session_state.db_products[st.session_state.db_products['Stock'] < 5]
    if not low_stock.empty:
        st.error(f"⚠️ Warning: {len(low_stock)} Items are Low on Stock!")
        st.dataframe(low_stock)
    
    tab1, tab2 = st.tabs(["📋 View Stock", "➕ Add Product"])
    
    with tab1:
        st.dataframe(
            st.session_state.db_products,
            use_container_width=True,
            column_config={
                "Stock": st.column_config.ProgressColumn("Stock Level", min_value=0, max_value=20, format="%d"),
                "Price": st.column_config.NumberColumn("Sale Price", format="PKR %d")
            }
        )
        
    with tab2:
        with st.form("add_prod"):
            c1, c2 = st.columns(2)
            n_sku = c1.text_input("SKU Code")
            n_name = c2.text_input("Product Name")
            c3, c4, c5 = st.columns(3)
            n_cost = c3.number_input("Cost", 0)
            n_price = c4.number_input("Sale Price", 0)
            n_stock = c5.number_input("Opening Stock", 0)
            
            if st.form_submit_button("Add to Inventory"):
                new_prod = {"SKU": n_sku, "Name": n_name, "Cost": n_cost, "Price": n_price, "Stock": n_stock}
                st.session_state.db_products = pd.concat([st.session_state.db_products, pd.DataFrame([new_prod])], ignore_index=True)
                st.success("Product Added!")

# --- 🚚 ORDER OPERATIONS (The Cool Part) ---
elif menu == "🚚 Order Operations":
    st.markdown("# 🚚 Dispatch Center")
    
    filter_status = st.radio("Filter Orders:", ["Pending", "Dispatched", "All"], horizontal=True)
    
    if filter_status == "All":
        filtered_df = st.session_state.db_orders
    else:
        filtered_df = st.session_state.db_orders[st.session_state.db_orders['Status'] == filter_status]
    
    if filtered_df.empty:
        st.info("No orders found in this category.")
    else:
        for index, row in filtered_df.iterrows():
            with st.expander(f"{row['Order ID']} | {row['Customer']} | PKR {row['Total']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Item:** {row['Item']} (x{row['Qty']})")
                    st.write(f"**City:** {row['City']}")
                    st.caption(f"Date: {row['Date']}")
                
                with col2:
                    st.markdown("##### Actions")
                    if row['Status'] == 'Pending':
                        if st.button("📦 Mark Dispatched", key=f"disp_{index}"):
                            st.session_state.db_orders.at[index, 'Status'] = 'Dispatched'
                            st.rerun()
                    
                    if st.button("🖨️ Print Invoice", key=f"prt_{index}"):
                        # Simulated Invoice
                        st.markdown(f"""
                        <div style="background:white; color:black; padding:20px; border-radius:10px;">
                            <h3 style="text-align:center;">INVOICE</h3>
                            <p><b>Order:</b> {row['Order ID']}</p>
                            <p><b>Customer:</b> {row['Customer']}</p>
                            <hr>
                            <p>{row['Item']} x {row['Qty']} = {row['Total']}</p>
                            <h4 style="text-align:right;">Total: {row['Total']}</h4>
                        </div>
                        """, unsafe_allow_html=True)

# --- 💰 FINANCIALS ---
elif menu == "💰 Financials":
    st.markdown("# 💰 Financial Health")
    
    # Cash Flow Logic
    delivered_sales = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Delivered']['Total'].sum()
    pending_cod = st.session_state.db_orders[st.session_state.db_orders['Status'] != 'Delivered']['Total'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="padding:20px; background:#1E1E1E; border-radius:10px; border-left: 5px solid #00FF7F;">
            <h3 style="margin:0; color:#888;">Cash In Hand (Bank)</h3>
            <h1 style="margin:0; color:white;">PKR {:,}</h1>
        </div>
        """.format(delivered_sales), unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="padding:20px; background:#1E1E1E; border-radius:10px; border-left: 5px solid #FFA500;">
            <h3 style="margin:0; color:#888;">Pending at Courier</h3>
            <h1 style="margin:0; color:white;">PKR {:,}</h1>
        </div>
        """.format(pending_cod), unsafe_allow_html=True)
        
    st.divider()
    st.subheader("Expense Tracker")
    
    with st.expander("➕ Add Expense"):
        ce1, ce2, ce3 = st.columns(3)
        ce1.date_input("Date")
        ce2.text_input("Description (Ads, Packaging, etc)")
        ce3.number_input("Amount", 0)
        st.button("Save Expense")
        
    st.info("Feature coming soon: Auto-Calculate Net Profit based on COGS + Expenses.")
