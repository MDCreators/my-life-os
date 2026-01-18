import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Seller OS Pro 🇵🇰", page_icon="📦", layout="wide")

# --- DATA SETUP (Session State) ---
if 'products' not in st.session_state:
    st.session_state.products = pd.DataFrame(columns=["Item ID", "Item Name", "Cost Price", "Sale Price", "Stock"])

if 'sales' not in st.session_state:
    st.session_state.sales = pd.DataFrame(columns=["Order ID", "Date", "Customer", "City", "Item", "Qty", "Sale Amt", "Delivery Charge", "Total Bill", "Status"])

if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("📦 Seller OS Pro")
    st.caption("Pakistani E-commerce Edition 🇵🇰")
    menu = st.radio("Menu", ["📊 Boss Dashboard", "🛒 New Order", "💸 Expenses & Ads", "📦 Inventory", "🚚 Order Management"])
    st.divider()
    
    # Quick Stats in Sidebar
    if not st.session_state.sales.empty:
        pending_orders = len(st.session_state.sales[st.session_state.sales['Status'] == 'Pending'])
        st.metric("Pending Orders", pending_orders)

# ==========================
# 📊 BOSS DASHBOARD (Real Profit)
# ==========================
if menu == "📊 Boss Dashboard":
    st.title("Business Snapshot 📈")
    
    # 1. Calculate Revenue
    total_revenue = st.session_state.sales['Total Bill'].sum() if not st.session_state.sales.empty else 0
    
    # 2. Calculate COGS (Product Cost)
    total_cogs = 0
    if not st.session_state.sales.empty:
        for index, row in st.session_state.sales.iterrows():
            # Find product cost
            product = st.session_state.products[st.session_state.products['Item Name'] == row['Item']]
            if not product.empty:
                cost = product.iloc[0]['Cost Price'] * row['Qty']
                total_cogs += cost

    # 3. Calculate Expenses (Ads + Packaging + Others)
    total_expenses = st.session_state.expenses['Amount'].sum() if not st.session_state.expenses.empty else 0
    
    # 4. Net Profit
    net_profit = total_revenue - total_cogs - total_expenses
    
    # Metrics Display
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"Rs {total_revenue:,.0f}")
    c2.metric("Product Cost (COGS)", f"Rs {total_cogs:,.0f}", delta_color="inverse")
    c3.metric("Total Expenses (Ads/Ops)", f"Rs {total_expenses:,.0f}", delta_color="inverse")
    c4.metric("🔥 NET PROFIT", f"Rs {net_profit:,.0f}", delta=f"Actual Bachat")
    
    st.divider()
    
    # Charts
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        st.subheader("💰 Expense Breakdown")
        if not st.session_state.expenses.empty:
            fig = px.pie(st.session_state.expenses, values='Amount', names='Category', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses added yet.")

    with c_chart2:
        st.subheader("🏙️ Top Cities")
        if not st.session_state.sales.empty:
            city_count = st.session_state.sales['City'].value_counts().reset_index()
            city_count.columns = ['City', 'Orders']
            fig2 = px.bar(city_count, x='City', y='Orders', template="plotly_dark", color='Orders')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No orders yet.")

# ==========================
# 🛒 NEW ORDER (With Delivery)
# ==========================
elif menu == "🛒 New Order":
    st.title("New Order Entry 📝")
    
    if st.session_state.products.empty:
        st.error("Please add products in Inventory first.")
    else:
        with st.form("order_form"):
            c1, c2, c3 = st.columns(3)
            cust_name = c1.text_input("Customer Name")
            cust_phone = c2.text_input("Phone Number")
            cust_city = c3.selectbox("City", ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Other"])
            
            st.divider()
            
            # Product Details
            product_list = st.session_state.products["Item Name"].tolist()
            col_prod, col_qty = st.columns([2, 1])
            selected_item = col_prod.selectbox("Select Product", product_list)
            qty = col_qty.number_input("Qty", min_value=1, value=1)
            
            # Fetch Price
            item_data = st.session_state.products[st.session_state.products["Item Name"] == selected_item].iloc[0]
            price = item_data["Sale Price"]
            
            st.divider()
            
            # Delivery & Calculation
            col_d1, col_d2 = st.columns(2)
            delivery_charges = col_d1.number_input("Delivery Charges (DC)", value=200)
            item_total = price * qty
            grand_total = item_total + delivery_charges
            
            col_d2.metric("Grand Total (Bill)", f"Rs {grand_total}")
            
            submit = st.form_submit_button("Confirm Order ✅")
            
            if submit:
                order_id = f"ORD-{len(st.session_state.sales) + 1001}"
                today = datetime.now().strftime("%Y-%m-%d")
                
                new_order = {
                    "Order ID": order_id,
                    "Date": today,
                    "Customer": cust_name,
                    "City": cust_city,
                    "Item": selected_item,
                    "Qty": qty,
                    "Sale Amt": item_total,
                    "Delivery Charge": delivery_charges,
                    "Total Bill": grand_total,
                    "Status": "Pending"
                }
                
                st.session_state.sales = pd.concat([st.session_state.sales, pd.DataFrame([new_order])], ignore_index=True)
                
                # Deduct Stock
                idx = st.session_state.products.index[st.session_state.products["Item Name"] == selected_item][0]
                st.session_state.products.at[idx, "Stock"] -= qty
                
                st.success(f"Order {order_id} Confirmed! Stock Updated.")

# ==========================
# 💸 EXPENSES & ADS (Crucial)
# ==========================
elif menu == "💸 Expenses & Ads":
    st.title("Expense Tracker 📉")
    st.info("Yahan har chota kharcha daalein taake Net Profit sahi aye.")
    
    with st.form("exp_form"):
        ec1, ec2 = st.columns(2)
        category = ec1.selectbox("Expense Category", ["Meta Ads (Facebook/Insta)", "Packaging Material", "Delivery/Courier Cost", "Rider Salary", "Internet/Bills", "Other"])
        amount = ec2.number_input("Amount (Rs)", min_value=0)
        desc = st.text_input("Description (Optional - e.g. Ad for Life OS)")
        date = st.date_input("Date")
        
        add_exp = st.form_submit_button("Add Expense")
        
        if add_exp:
            new_exp = {
                "Date": date,
                "Category": category,
                "Description": desc,
                "Amount": amount
            }
            st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_exp])], ignore_index=True)
            st.success("Expense Added!")

    st.divider()
    st.subheader("Recent Expenses")
    st.dataframe(st.session_state.expenses, use_container_width=True)

# ==========================
# 📦 INVENTORY
# ==========================
elif menu == "📦 Inventory":
    st.title("Stock Management 🏭")
    
    with st.form("add_prod"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Product Name")
        sku = c2.text_input("SKU / ID")
        c3, c4, c5 = st.columns(3)
        cost = c3.number_input("Cost Price (Khareed)", min_value=0)
        sale = c4.number_input("Sale Price (Bech)", min_value=0)
        stock = c5.number_input("Stock Qty", min_value=0)
        
        if st.form_submit_button("Add Product"):
            new_prod = {"Item ID": sku, "Item Name": name, "Cost Price": cost, "Sale Price": sale, "Stock": stock}
            st.session_state.products = pd.concat([st.session_state.products, pd.DataFrame([new_prod])], ignore_index=True)
            st.success("Product Added!")

    st.dataframe(st.session_state.products, use_container_width=True)

# ==========================
# 🚚 ORDER MANAGEMENT
# ==========================
elif menu == "🚚 Order Management":
    st.title("Manage Orders 🚚")
    
    if not st.session_state.sales.empty:
        # Show Data Editor (Editable Table)
        edited_df = st.data_editor(
            st.session_state.sales,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Order Status",
                    options=["Pending", "Dispatched", "Delivered", "Returned (RTO)", "Cancelled"],
                    required=True
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Save Changes Logic (In real database, this would be auto-saved)
        st.session_state.sales = edited_df
        st.caption("Status change karne ke liye cell par click karein.")
        
    else:
        st.info("No orders found.")
