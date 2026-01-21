import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("🕵️‍♂️ SI Traders - Connection Doctor")

# --- 1. CONNECTION CHECK ---
try:
    if "service_account" not in st.secrets:
        st.error("🚨 Secrets file khali hay ya missing hay!")
        st.stop()
        
    creds_dict = dict(st.secrets["service_account"])
    # Key Fixer
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").replace('\\', '') if creds_dict["private_key"].startswith('\\') else creds_dict["private_key"].replace("\\n", "\n")

    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    st.success("✅ Step 1: Google se Connection Jarr Gaya!")

except Exception as e:
    st.error(f"❌ Connection Fail: {e}")
    st.stop()

# --- 2. SHEET CHECK ---
try:
    sheet = client.open("SI Traders Data")
    st.success(f"✅ Step 2: '{sheet.title}' Sheet Mil Gayi!")
    
    # Tabs List Karo
    tabs = [ws.title for ws in sheet.worksheets()]
    st.info(f"📂 Aap ki Sheet mein yeh Tabs hain: {tabs}")
    
    target_tab = "Purchase"
    if target_tab not in tabs:
        st.error(f"❌ Masla Mil Gaya: Code '{target_tab}' dhoond raha hay, magar Sheet mein sirf {tabs} hain. Spelling theek karein!")
        st.stop()
    else:
        st.success(f"✅ Step 3: '{target_tab}' Tab bhi Mil Gaya!")

    # --- 3. WRITE TEST ---
    st.markdown("---")
    st.write("👇 Neechay wala button dabayen. Agar 'Success' aya tu masla hal!")
    
    if st.button("🔴 Test Data Save Karein (Write Test)"):
        ws = sheet.worksheet(target_tab)
        # Dummy data
        ws.append_row(["Test_Admin", "2025-01-01", "Checking System", 10, 50, 500, "Test Entry"])
        st.success("🎉 MUBARAK HO! Data Write Ho Gaya!")
        st.balloons()
        
        # Read Back
        data = ws.get_all_values()
        st.write("📋 Abhi Sheet mein yeh parra hay:", data)

except Exception as e:
    st.error(f"🚨 Aakhri Error: {e}")
