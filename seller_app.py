elif menu == "🚚 Orders":
    st.title("Order Manager")
    orders = get_orders(current_owner)
    for o in orders:
        with st.expander(f"{o.get('date','')} | {o.get('customer','Unknown')} | Rs {o['total']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write("**Items:**")
                for i in o['items']:
                    d_per = i.get('discount_percent', 0)
                    price_show = i.get('final_price', i.get('price', 0))
                    
                    if d_per > 0:
                        st.write(f"- {i['name']} x{i['qty']} (Disc: {d_per}%) = Rs {price_show * i['qty']}")
                    else:
                        st.write(f"- {i['name']} x{i['qty']} = Rs {price_show * i['qty']}")
                        
                st.caption(f"Address: {o.get('address')} | Phone: {o.get('phone')}")
                new_stat = st.selectbox("Status", ["Pending", "Shipped", "Delivered", "Returned", "Cancelled"], key=f"s_{o['id']}", index=["Pending", "Shipped", "Delivered", "Returned", "Cancelled"].index(o.get('status', 'Pending')))
                if new_stat != o.get('status'):
                    db.collection("orders").document(o['id']).update({"status": new_stat})
                    st.rerun()
            
            with c2:
                if st.button("🧾 Invoice", key=f"inv_{o['id']}"):
                    st.markdown("---")
                    
                    # --- Invoice Rows Generation ---
                    rows_html = ""
                    for i in o['items']:
                        d_per = i.get('discount_percent', 0)
                        f_price = i.get('final_price', i.get('price'))
                        row_total = f_price * i['qty']
                        
                        disc_badge = f"<span style='color:red; font-size:12px;'>(-{d_per}%)</span>" if d_per > 0 else ""
                        rows_html += f"""<tr><td>{i['name']} {disc_badge}</td><td>{i['qty']}</td><td>{f_price}</td><td style='text-align:right;'>{row_total}</td></tr>"""
                    
                    # Global Discount Row
                    g_disc = o.get('global_discount', 0)
                    g_disc_html = ""
                    if g_disc > 0:
                        g_disc_html = f"<tr><td colspan='3'>Extra Discount</td><td style='text-align:right; color:red;'>- {g_disc}</td></tr>"

                    # 🔥 FIX: Removing indentation to prevent code block rendering
                    inv_html = f"""<div class="invoice-box">
<h2 style="color:black; margin-top:0;">INVOICE</h2>
<p><b>Merchant:</b> {current_biz_name}<br><b>Date:</b> {o['date'].split('.')[0]}</p>
<hr>
<p><b>Bill To:</b><br>{o['customer']}<br>{o.get('phone','')}<br>{o.get('address','')}</p>
<table class="invoice-table">
<thead><tr style="background:#eee;"><th>Item</th><th>Qty</th><th>Price</th><th style="text-align:right;">Total</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
<br>
<div style="float:right; width:40%;">
<table style="width:100%">
<tr><td>Subtotal:</td><td style="text-align:right;">{o.get('subtotal',0)}</td></tr>
{g_disc_html}
<tr><td>Delivery:</td><td style="text-align:right;">{o.get('delivery',0)}</td></tr>
<tr style="font-weight:bold; font-size:18px;"><td>TOTAL:</td><td style="text-align:right;">Rs {o['total']}</td></tr>
</table>
</div>
<div style="clear:both;"></div>
</div>"""
                    st.markdown(inv_html, unsafe_allow_html=True)
