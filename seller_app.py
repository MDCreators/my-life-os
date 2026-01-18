import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Seller OS", page_icon="📦", layout="wide")

# --- DATA SETUP (Temporary Memory) ---
# Yahan hum check kar rahe hain ke data pehle se majood hai ya nahi
if 'products' not in st.session_state:
    # Aapki 'DATABASE' sheet wala structure
    st.session_state.products = pd.DataFrame(columns=["Item ID", "Item Name", "Purchase Price", "Sale Price", "Stock"])

if 'sales' not in st.session_state:
    # Aapki 'SALE ENTRY' sheet wala structure
    st.session_state.sales = pd.DataFrame(columns=["Order ID", "Date", "Customer", "Phone", "Item Name", "Qty", "Total", "Profit", "Status"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("📦 Seller OS")
    menu = st.radio("Navigate", ["📊 Dashboard", "🛒 New Order", "📦 Inventory", "🧾 Invoice"])
    st.write("---")
    st.info("E-commerce Manager v1.0")

# ==========================
# 📊 DASHBOARD TAB
# ==========================
if menu == "📊 Dashboard":
    st.title("Business Dashboard 📈")
    
    # Calculate Metrics
    total_sales = st.session_state.sales['Total'].sum() if not st.session_state.sales.empty else 0
    total_profit = st.session_state.sales['Profit'].sum() if not st.session_state.sales.empty else 0
    total_orders = len(st.session_state.sales)
    
    # KPI Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"Rs {total_sales:,.0f}")
    c2.metric("Total Profit", f"Rs {total_profit:,.0f}", delta_color="normal")
    c3.metric("Total Orders", total_orders)
    
    st.divider()
    
    # Charts (Agar data ho to)
    if not st.session_state.sales.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        # Sales Trend
        with col_chart1:
            st.subheader("Sales Trend")
            daily_sales = st.session_state.sales.groupby("Date")["Total"].sum().reset_index()
            fig = px.bar(daily_sales, x="Date", y="Total", template="plotly_dark", color_discrete_sequence=['#00FF7F'])
            st.plotly_chart(fig, use_container_width=True)
            
        # Top Products
        with col_chart2:
            st.subheader("Top Selling Products")
            top_products = st.session_state.sales.groupby("Item Name")["Qty"].sum().reset_index()
            fig2 = px.pie(top_products, values="Qty", names="Item Name", hole=0.5, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Abhi koi sales data nahi hay. 'New Order' mein ja kar entry karein.")

# ==========================
# 🛒 NEW ORDER (SALE ENTRY)
# ==========================
elif menu == "🛒 New Order":
    st.title("New Order Entry 📝")
    
    # Pehle check karo Inventory mein maal hai ya nahi
    if st.session_state.products.empty:
        st.error("Pehle 'Inventory' tab mein ja kar Products add karein!")
    else:
        with st.form("order_form"):
            c1, c2 = st.columns(2)
            customer_name = c1.text_input("Customer Name")
            customer_phone = c2.text_input("Phone Number")
            address = st.text_area("Delivery Address")
            
            st.divider()
            
            # Product Selection
            product_list = st.session_state.products["Item Name"].tolist()
            selected_item = st.selectbox("Select Product", product_list)
            
            # Auto-fetch Price
            item_data = st.session_state.products[st.session_state.products["Item Name"] == selected_item].iloc[0]
            price = item_data["Sale Price"]
            cost = item_data["Purchase Price"]
            
            c3, c4, c5 = st.columns(3)
            qty = c3.number_input("Quantity", min_value=1, value=1)
            c4.info(f"Price: Rs {price}")
            total_amt = price * qty
            c5.success(f"Total: Rs {total_amt}")
            
            status = st.selectbox("Order Status", ["Pending", "Packed", "Shipped", "Delivered"])
            
            submitted = st.form_submit_button("Confirm Order 🚀")
            
            if submitted:
                # Logic: Save to Sales DataFrame
                order_id = f"ORD-{len(st.session_state.sales) + 1001}"
                profit = total_amt - (cost * qty)
                today = datetime.now().strftime("%Y-%m-%d")
                
                new_sale = {
                    "Order ID": order_id,
                    "Date": today,
                    "Customer": customer_name,
                    "Phone": customer_phone,
                    "Item Name": selected_item,
                    "Qty": qty,
                    "Total": total_amt,
                    "Profit": profit,
                    "Status": status
                }
                
                # Append to Sales DataFrame
                st.session_state.sales = pd.concat([st.session_state.sales, pd.DataFrame([new_sale])], ignore_index=True)
                
                # Stock Update Logic (Simple Deduction)
                idx = st.session_state.products.index[st.session_state.products["Item Name"] == selected_item][0]
                st.session_state.products.at[idx, "Stock"] -= qty
                
                st.success(f"Order {order_id} Saved! Stock Updated.")

# ==========================
# 📦 INVENTORY (DATABASE)
# ==========================
elif menu == "📦 Inventory":
    st.title("Stock Management 🏭")
    
    # Add New Product Form
    with st.expander("➕ Add New Product", expanded=False):
        with st.form("add_product"):
            c1, c2 = st.columns(2)
            p_name = c1.text_input("Item Name")
            p_id = c2.text_input("Item ID (e.g., A-001)")
            
            c3, c4, c5 = st.columns(3)
            p_buy = c3.number_input("Purchase Price (Cost)", min_value=0)
            p_sell = c4.number_input("Selling Price", min_value=0)
            p_stock = c5.number_input("Initial Stock", min_value=0)
            
            add_btn = st.form_submit_button("Add to Database")
            
            if add_btn:
                new_prod = {
                    "Item ID": p_id,
                    "Item Name": p_name,
                    "Purchase Price": p_buy,
                    "Sale Price": p_sell,
                    "Stock": p_stock
                }
                st.session_state.products = pd.concat([st.session_state.products, pd.DataFrame([new_prod])], ignore_index=True)
                st.success(f"{p_name} Added!")
    
    # Show Stock Table
    st.subheader("Current Stock Report")
    if not st.session_state.products.empty:
        # Highlight Low Stock
        st.dataframe(st.session_state.products.style.applymap(lambda x: 'background-color: #ff4b4b' if isinstance(x, int) and x < 5 else '', subset=['Stock']), use_container_width=True)
    else:
        st.info("Database empty. Add products above.")

# ==========================
# 🧾 INVOICE GENERATOR
# ==========================
elif menu == "🧾 Invoice":
    st.title("Generate Invoice 🖨️")
    
    if st.session_state.sales.empty:
        st.warning("No orders available to generate invoice.")
    else:
        # Select Order
        order_list = st.session_state.sales["Order ID"].tolist()
        sel_order_id = st.selectbox("Select Order ID", order_list)
        
        # Get Order Details
        order_det = st.session_state.sales[st.session_state.sales["Order ID"] == sel_order_id].iloc[0]
        
        # Display Invoice View (Simple Receipt)
        st.markdown("---")
        st.markdown(f"""
        <div style="background-color: white; color: black; padding: 20px; border-radius: 10px; border: 1px solid #ccc;">
            <h2 style="text-align: center;">INVOICE</h2>
            <p style="text-align: center;"><b>Order ID:</b> {order_det['Order ID']} | <b>Date:</b> {order_det['Date']}</p>
            <hr>
            <p><b>Customer:</b> {order_det['Customer']}</p>
            <p><b>Phone:</b> {order_det['Phone']}</p>
            <table style="width:100%">
                <tr>
                    <th style="text-align:left">Item</th>
                    <th style="text-align:right">Qty</th>
                    <th style="text-align:right">Total</th>
                </tr>
                <tr>
                    <td>{order_det['Item Name']}</td>
                    <td style="text-align:right">{order_det['Qty']}</td>
                    <td style="text-align:right">Rs {order_det['Total']}</td>
                </tr>
            </table>
            <hr>
            <h3 style="text-align: right;">Total Due: Rs {order_det['Total']}</h3>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Tip: Aap Ctrl+P daba kar is page ko Print kar saktay hain ya screenshot le saktay hain.")
