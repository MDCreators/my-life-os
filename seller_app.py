import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Seller HQ 🇵🇰", page_icon="🚀", layout="wide")

# --- CUSTOM CSS (Thora style) ---
st.markdown("""
<style>
    div.stMetric {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 5px;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00FF7F;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP (Auto-Structure) ---
# Hum columns ko Excel ki bajaye Best Practices par rakhain ge
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
def get_profit_data():
    if st.session_state.db_orders.empty:
        return 0, 0, 0, 0
    
    # Revenue (Sirf Delivered ya Dispatched orders ka)
    valid_orders = st.session_state.db_orders[st.session_state.db_orders['Status'].isin(['Delivered', 'Dispatched', 'Payment Received'])]
    revenue = valid_orders['Total'].sum()
    
    # COGS (Product Cost)
    product_cost = (valid_orders['Cost Price'] * valid_orders['Qty']).sum()
    
    # RTO Loss (Return orders ke delivery charges zaya huye)
    rto_orders = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Returned (RTO)']
    rto_loss = rto_orders['DC'].sum() * 2  # Aana aur Jana dono ke charges (Roughly)
    
    # Marketing & Ops
    expenses = st.session_state.db_expenses['Amount'].sum()
    
    net_profit = revenue - product_cost - expenses - rto_loss
    return revenue, product_cost, expenses + rto_loss, net_profit

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚀 Seller HQ")
    st.caption("Powering Pakistani Brands")
    menu = st.radio("Menu", [
        "📊 Profit Dashboard", 
        "🛒 New Order (POS)", 
        "📦 Inventory Manager", 
        "🚚 Order Operations", 
        "💸 Marketing & Expenses"
    ])
    st.divider()
    
    # Quick Status
    pending = len(st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Pending'])
    st.metric("Orders to Pack", pending, delta_color="inverse")

# ==========================
# 📊 PROFIT DASHBOARD
# ==========================
if menu == "📊 Profit Dashboard":
    st.title("Business Health 🏥")
    st.markdown("Yahan asli doodh ka doodh aur pani ka pani hoga.")
    
    rev, cogs, exp, profit = get_profit_data()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales (Revenue)", f"Rs {rev:,.0f}")
    c2.metric("Product Cost", f"Rs {cogs:,.0f}", delta="-Cost")
    c3.metric("Ads + RTO Loss", f"Rs {exp:,.0f}", delta="-Expense")
    c4.metric("💰 NET PROFIT", f"Rs {profit:,.0f}", delta="Jaib Mein Aye")
    
    st.divider()
    
    # Analytics
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("City-wise Sales 🏙️")
        if not st.session_state.db_orders.empty:
            city_data = st.session_state.db_orders['City'].value_counts()
            st.bar_chart(city_data)
        else:
            st.info("No data yet.")

    with col_chart2:
        st.subheader("Order Status Ratio 📦")
        if not st.session_state.db_orders.empty:
            fig = px.pie(st.session_state.db_orders, names='Status', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # RTO Warning
            total_orders = len(st.session_state.db_orders)
            returns = len(st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Returned (RTO)'])
            if total_orders > 0:
                rto_rate = (returns / total_orders) * 100
                st.caption(f"Current Return Rate: **{rto_rate:.1f}%** (Isay 10% se neechay rakhein)")

# ==========================
# 🛒 NEW ORDER (Fraud Check)
# ==========================
elif menu == "🛒 New Order (POS)":
    st.title("Manual Order Entry 📝")
    
    # 1. Check Customer History (Fraud Check)
    phone_check = st.text_input("Enter Phone Number first (to check history)", placeholder="03001234567")
    
    if phone_check:
        history = st.session_state.db_orders[st.session_state.db_orders['Phone'] == phone_check]
        if not history.empty:
            returned = len(history[history['Status'] == 'Returned (RTO)'])
            delivered = len(history[history['Status'] == 'Delivered'])
            if returned > 0:
                st.error(f"⚠️ WARNING: Is customer ne pehlay **{returned}** orders wapis kiye hain!")
            else:
                st.success(f"✅ Safe Customer (Previously {delivered} Delivered)")
        else:
            st.info("🆕 New Customer")

    with st.form("new_order"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Customer Name")
        city = c2.selectbox("City", ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Peshawar", "Quetta", "Other"])
        address = st.text_area("Full Address")
        
        st.divider()
        
        if st.session_state.db_products.empty:
            st.error("No products in inventory.")
            st.stop()
            
        prod_names = st.session_state.db_products['Product Name'].tolist()
        item = st.selectbox("Select Product", prod_names)
        
        # Auto Fetch Prices
        prod_details = st.session_state.db_products[st.session_state.db_products['Product Name'] == item].iloc[0]
        base_price = prod_details['Sale Price']
        cost_price = prod_details['Cost Price']
        
        c3, c4, c5 = st.columns(3)
        qty = c3.number_input("Quantity", min_value=1, value=1)
        price = c4.number_input("Sale Price (Editable)", value=base_price)
        dc = c5.number_input("Delivery Charges", value=200)
        
        total = (price * qty) + dc
        st.markdown(f"### Total Bill: **Rs {total}**")
        
        if st.form_submit_button("Confirm Order 🚀"):
            new_id = f"ORD-{len(st.session_state.db_orders)+1001}"
            new_entry = {
                "Order ID": new_id,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Customer Name": name,
                "Phone": phone_check,
                "City": city,
                "Address": address,
                "Item": item,
                "Qty": qty,
                "Price": price,
                "DC": dc,
                "Total": total,
                "Cost Price": cost_price,
                "Status": "Pending",
                "Courier": "Pending",
                "Tracking ID": ""
            }
            st.session_state.db_orders = pd.concat([st.session_state.db_orders, pd.DataFrame([new_entry])], ignore_index=True)
            
            # Stock Deduct
            idx = st.session_state.db_products.index[st.session_state.db_products['Product Name'] == item][0]
            st.session_state.db_products.at[idx, 'Stock'] -= qty
            
            st.success("Order Placed Successfully!")

# ==========================
# 📦 INVENTORY
# ==========================
elif menu == "📦 Inventory Manager":
    st.title("Stockroom 🏭")
    
    with st.expander("Add New Item"):
        with st.form("add_prod"):
            c1, c2 = st.columns(2)
            p_name = c1.text_input("Product Name (e.g. Life OS Planner)")
            p_sku = c2.text_input("SKU Code (e.g. PLAN-01)")
            
            c3, c4, c5 = st.columns(3)
            p_cost = c3.number_input("Making Cost (Khareed)", min_value=0)
            p_sale = c4.number_input("Selling Price", min_value=0)
            p_stock = c5.number_input("Stock Qty", min_value=0)
            
            if st.form_submit_button("Save Item"):
                new_prod = pd.DataFrame([{
                    "SKU": p_sku, "Product Name": p_name, "Cost Price": p_cost, 
                    "Sale Price": p_sale, "Stock": p_stock, "Category": "General"
                }])
                st.session_state.db_products = pd.concat([st.session_state.db_products, new_prod], ignore_index=True)
                st.success("Item Added!")

    # Editable Table
    st.subheader("Current Stock")
    edited_stock = st.data_editor(st.session_state.db_products, num_rows="dynamic", use_container_width=True)
    st.session_state.db_products = edited_stock

# ==========================
# 🚚 ORDER OPERATIONS (The Powerhouse)
# ==========================
elif menu == "🚚 Order Operations":
    st.title("Operations Hub 🚛")
    
    # Filter Tabs
    tab1, tab2, tab3 = st.tabs(["Pending (Call Karo)", "Dispatched (Courier)", "All Orders"])
    
    with tab1:
        st.info("In logon ko call kar ke confirm karein.")
        pending_orders = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Pending']
        
        if not pending_orders.empty:
            for i, row in pending_orders.iterrows():
                with st.expander(f"{row['Customer Name']} - {row['City']} (Rs {row['Total']})"):
                    c1, c2, c3 = st.columns(3)
                    # WhatsApp Link Generator
                    wa_msg = f"Salam {row['Customer Name']}! 👋 Hum Prime Tutors/Store se baat kar rahay hain. Apne order {row['Item']} confirm karne ke liye reply karein."
                    wa_link = f"https://wa.me/92{row['Phone'][1:]}?text={wa_msg.replace(' ', '%20')}"
                    
                    c1.markdown(f"[💬 WhatsApp Karo]({wa_link})")
                    
                    if c2.button("✅ Confirm", key=f"conf_{i}"):
                        idx = st.session_state.db_orders[st.session_state.db_orders['Order ID'] == row['Order ID']].index[0]
                        st.session_state.db_orders.at[idx, 'Status'] = 'Confirmed'
                        st.experimental_rerun()
                        
                    if c3.button("❌ Cancel", key=f"can_{i}"):
                        idx = st.session_state.db_orders[st.session_state.db_orders['Order ID'] == row['Order ID']].index[0]
                        st.session_state.db_orders.at[idx, 'Status'] = 'Cancelled'
                        st.experimental_rerun()
        else:
            st.success("No Pending Orders! Good job.")

    with tab2:
        st.subheader("Courier Bulk Upload Generator")
        st.write("Trax/Leopards/TCS ke portal par upload karne ke liye file download karein.")
        
        confirmed_orders = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Confirmed']
        if not confirmed_orders.empty:
            # Create a CSV format that couriers usually accept
            courier_csv = confirmed_orders[['Customer Name', 'Phone', 'Address', 'City', 'Total', 'Item', 'Qty', 'Order ID']]
            courier_csv.columns = ['Consignee Name', 'Consignee Phone', 'Address', 'City', 'COD Amount', 'Product', 'Pieces', 'Order Ref']
            
            csv = courier_csv.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "⬇️ Download Courier CSV",
                csv,
                "trax_bulk_upload.csv",
                "text/csv",
                key='download-csv'
            )
            
            if st.button("Mark All as Dispatched"):
                # Bulk update status
                indices = st.session_state.db_orders[st.session_state.db_orders['Status'] == 'Confirmed'].index
                st.session_state.db_orders.loc[indices, 'Status'] = 'Dispatched'
                st.success("Orders marked as Dispatched!")
                st.experimental_rerun()
        else:
            st.warning("Pehle orders ko 'Pending' tab mein Confirm karein.")

    with tab3:
        st.dataframe(st.session_state.db_orders)

# ==========================
# 💸 MARKETING & EXPENSES
# ==========================
elif menu == "💸 Marketing & Expenses":
    st.title("Expense Tracker 📉")
    
    with st.form("add_exp"):
        c1, c2, c3 = st.columns(3)
        date = c1.date_input("Date")
        category = c2.selectbox("Type", ["Meta Ads", "Packaging", "Salary", "Food/Misc", "RTO Charges"])
        amount = c3.number_input("Amount (Rs)", min_value=0)
        desc = st.text_input("Description (e.g. Adset Testing)")
        
        if st.form_submit_button("Add Expense"):
            new_exp = pd.DataFrame([{"Date": date, "Type": category, "Description": desc, "Amount": amount}])
            st.session_state.db_expenses = pd.concat([st.session_state.db_expenses, new_exp], ignore_index=True)
            st.success("Kharcha Note Ho Gaya!")

    st.divider()
    
    # Ad Spend Analysis
    if not st.session_state.db_expenses.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Expense Breakdown")
            fig = px.pie(st.session_state.db_expenses, values='Amount', names='Type', template="plotly_dark")
            st.plotly_chart(fig)
            
        with col2:
            # Calculate CPA (Cost Per Acquisition)
            total_ads = st.session_state.db_expenses[st.session_state.db_expenses['Type'] == 'Meta Ads']['Amount'].sum()
            total_orders = len(st.session_state.db_orders)
            if total_orders > 0:
                cpa = total_ads / total_orders
                st.metric("CPA (Cost Per Order)", f"Rs {cpa:.0f}", help="Aik order lanay par kitna kharcha hua")
            else:
                st.metric("CPA", "N/A")
