import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from db import get_db_connection, init_db

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TechPharma Solutions",
    page_icon="💊",
    layout="wide"
)

# Initialize Database & Tables
init_db()

# --- HEADER SECTION ---
st.markdown("""
    <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;'>
        <h1 style='color: #0066cc; margin: 0;'>💊 TechPharma Solutions</h1>
        <p style='color: #555; font-style: italic; margin-top: 5px;'>“The Smart Way to Manage Your Pharmacy – Fast Billing, Zero Expiry Stress.”</p>
        <p style='color: #888; font-size: 12px; font-weight: bold; letter-spacing: 1px;'>POWERED BY NEELAM TECHNOLOGIES</p>
    </div>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.user_id = None

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.subheader("🔐 Login to TechPharma Portal")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT id, role, password FROM enterprise_hierarchy WHERE username = %s;", (username,))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user and user[2] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = username
                    st.session_state.role = user[1]
                    st.success("Login Successful! Reloading...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
else:
    # --- SIDEBAR MENU ---
    st.sidebar.markdown(f"### User: {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {st.session_state.role}")
    st.sidebar.markdown("---")
    
    menu_options = ["Enterprise Dashboard", "➕ Add Subordinate / Retailer", "🔄 Hierarchy & Subordinate Transfers", "🗑️ Manage & Deletion Rules"]
    if st.session_state.role == "OWNER":
        menu_options.append("🛠️ Admin Whiteboard & Pricing")
    
    menu_options.append("Download Desktop Icon")
    menu = st.sidebar.radio("Navigation", menu_options)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.user_id = None
        st.rerun()

    # --- 1. ENTERPRISE DASHBOARD ---
    if menu == "Enterprise Dashboard":
        st.subheader(f"🛡️ Enterprise Network Dashboard ({st.session_state.role})")
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            cur.execute("SELECT id, role, name, email, phone, username FROM enterprise_hierarchy;")
            members = cur.fetchall()
            
            st.markdown("### 🏢 Full Hierarchy Network (Owner ➔ Country Head ➔ State Head ➔ Zonal Manager ➔ SSE)")
            if members:
                df = pd.DataFrame(members, columns=["ID", "Role", "Name", "Email", "Phone", "Username"])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hierarchy members found.")

            st.markdown("### 🏪 Retailers & Terminals Network")
            cur.execute("""
                SELECT r.id, r.store_name, r.owner_name, r.gstin, r.phone, r.address, 
                       h.name as sse_name, r.is_demo, r.subscription_expiry, r.created_at
                FROM enterprise_retailers r
                LEFT JOIN enterprise_hierarchy h ON r.sse_id = h.id;
            """)
            retailers = cur.fetchall()
            if retailers:
                df_ret = pd.DataFrame(retailers, columns=["ID", "Store Name", "Owner", "GSTIN", "Phone", "Address", "Assigned SSE", "Demo Mode", "Expiry Date", "Created Date"])
                st.dataframe(df_ret, use_container_width=True)
            else:
                st.info("No retailers registered yet.")
            
            cur.close()
            conn.close()

    # --- 2. ADD SUBORDINATE / RETAILER ---
    elif menu == "➕ Add Subordinate / Retailer":
        st.subheader("➕ Register New Member or Retailer Terminal")
        
        tab_choice = st.radio("Select Type to Add", ["Hierarchy Member", "Retailer / Terminal"])
        
        if tab_choice == "Hierarchy Member":
            with st.form("add_member_form"):
                allowed_roles = ["COUNTRY_HEAD", "STATE_HEAD", "ZONAL_MANAGER", "SALES_ENGINEER"]
                new_role = st.selectbox("Role", allowed_roles)
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email")
                new_phone = st.text_input("Phone Number")
                new_uname = st.text_input("Username")
                new_upass = st.text_input("Password", type="password")
                
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT id, name, role FROM enterprise_hierarchy;")
                all_sup = cur.fetchall()
                cur.close()
                conn.close()
                
                sup_dict = {f"{s[1]} ({s[2]})": s[0] for s in all_sup}
                parent_label = st.selectbox("Assign Under Supervisor", list(sup_dict.keys()) if sup_dict else ["None"])
                parent_id = sup_dict.get(parent_label, None)
                
                add_sub = st.form_submit_button("Save Member")
                if add_sub:
                    if new_name and new_uname and new_upass:
                        conn = get_db_connection()
                        if conn:
                            cur = conn.cursor()
                            try:
                                cur.execute("""
                                    INSERT INTO enterprise_hierarchy (role, name, email, phone, username, password, parent_id)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                                """, (new_role, new_name, new_email, new_phone, new_uname, new_upass, parent_id))
                                conn.commit()
                                st.success(f"Successfully added {new_name} as {new_role}!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error: {ex}")
                            finally:
                                cur.close()
                                conn.close()
                    else:
                        st.warning("Please fill all required fields!")
        else:
            with st.form("add_retailer_form"):
                store_name = st.text_input("Store Name")
                owner_name = st.text_input("Owner Name")
                gstin = st.text_input("GSTIN")
                phone = st.text_input("Phone Number")
                address = st.text_input("Address")
                
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM enterprise_hierarchy WHERE role = 'SALES_ENGINEER';")
                sses = cur.fetchall()
                cur.close()
                conn.close()
                
                sse_dict = {s[1]: s[0] for s in sses}
                sse_label = st.selectbox("Assign to Sales & Service Engineer (SSE)", list(sse_dict.keys()) if sse_dict else ["None"])
                sse_id = sse_dict.get(sse_label, None)
                
                is_demo = st.checkbox("7-Day Demo Mode", value=True)
                
                add_ret = st.form_submit_button("Save Retailer & Terminal")
                if add_ret:
                    if store_name and sse_id:
                        expiry = datetime.now() + timedelta(days=7) if is_demo else datetime.now() + timedelta(days=365)
                        conn = get_db_connection()
                        if conn:
                            cur = conn.cursor()
                            try:
                                cur.execute("""
                                    INSERT INTO enterprise_retailers (store_name, owner_name, gstin, phone, address, sse_id, subscription_expiry, is_demo)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                                """, (store_name, owner_name, gstin, phone, address, sse_id, expiry, is_demo))
                                conn.commit()
                                st.success("Retailer terminal registered successfully!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error: {ex}")
                            finally:
                                cur.close()
                                conn.close()
                    else:
                        st.warning("Store Name and SSE assignment are mandatory!")

    # --- 3. HIERARCHY & SUBORDINATE TRANSFERS ---
    elif menu == "🔄 Hierarchy & Subordinate Transfers":
        st.subheader("🔄 Multi-Tier Transfer & Re-assignment Module")
        st.write("Transfer staff members or shift subordinates across the enterprise chain.")
        
        transfer_type = st.selectbox("Select Transfer Level", [
            "Transfer Zonal Manager (Reassign SSEs)",
            "Transfer SSE (Reassign Retailers)"
        ])
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if "Zonal Manager" in transfer_type:
            cur.execute("SELECT id, name, username FROM enterprise_hierarchy WHERE role = 'ZONAL_MANAGER';")
            zm_list = cur.fetchall()
            cur.execute("SELECT id, name, username FROM enterprise_hierarchy WHERE role = 'ZONAL_MANAGER';")
            target_zm = cur.fetchall()
            cur.close()
            conn.close()
            
            if zm_list:
                zm_dict = {f"{z[1]} ({z[2]})": z[0] for z in zm_list}
                selected_zm = st.selectbox("Select Zonal Manager to Transfer / Replace", list(zm_dict.keys()))
                from_id = zm_dict[selected_zm]
                
                target_dict = {f"{t[1]} ({t[2]})": t[0] for t in target_zm if t[0] != from_id}
                if target_dict:
                    to_zm_label = st.selectbox("Shift Under New Zonal Manager", list(target_dict.keys()))
                    to_id = target_dict[to_zm_label]
                    
                    if st.button("Execute Zonal Manager Transfer (Shift SSEs)"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE enterprise_hierarchy SET parent_id = %s WHERE parent_id = %s AND role = 'SALES_ENGINEER';", (to_id, from_id))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("All SSEs successfully shifted to the new Zonal Manager!")
                        st.rerun()
                else:
                    st.info("No alternative Zonal Manager available.")
            else:
                st.info("No Zonal Managers found.")

        elif "SSE" in transfer_type:
            cur.execute("SELECT id, name, username FROM enterprise_hierarchy WHERE role = 'SALES_ENGINEER';")
            sse_list = cur.fetchall()
            cur.execute("SELECT id, name, username FROM enterprise_hierarchy WHERE role = 'SALES_ENGINEER';")
            target_sse = cur.fetchall()
            cur.close()
            conn.close()
            
            if sse_list:
                sse_dict = {f"{s[1]} ({s[2]})": s[0] for s in sse_list}
                selected_sse = st.selectbox("Select SSE to Transfer", list(sse_dict.keys()))
                from_sse_id = sse_dict[selected_sse]
                
                target_sse_dict = {f"{t[1]} ({t[2]})": t[0] for t in target_sse if t[0] != from_sse_id}
                if target_sse_dict:
                    to_sse_label = st.selectbox("Shift Retailers Under New SSE", list(target_sse_dict.keys()))
                    to_sse_id = target_sse_dict[to_sse_label]
                    
                    if st.button("Execute SSE Transfer (Shift Retailers)"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE enterprise_retailers SET sse_id = %s WHERE sse_id = %s;", (to_sse_id, from_sse_id))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("All Retailer Terminals successfully shifted to the new SSE!")
                        st.rerun()
                else:
                    st.info("No alternative SSE available.")
            else:
                st.info("No Sales Engineers found.")

    # --- 4. MANAGE & DELETION RULES ---
    elif menu == "🗑️ Manage & Deletion Rules":
        st.subheader("🗑️ Manage & Security Deletion Rules")
        st.write("Retailer deletion is strictly protected: accounts can ONLY be deleted if they are in **7-day demo mode** or their **subscription validity has expired**.")
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, store_name, owner_name, is_demo, subscription_expiry FROM enterprise_retailers;")
        retailers = cur.fetchall()
        cur.close()
        conn.close()
        
        if retailers:
            ret_dict = {f"{r[1]} (Owner: {r[2]})": {"id": r[0], "is_demo": r[3], "expiry": r[4]} for r in retailers}
            selected_ret_label = st.selectbox("Select Retailer Terminal", list(ret_dict.keys()))
            ret_info = ret_dict[selected_ret_label]
            
            st.info(f"Demo Mode: {ret_info['is_demo']} | Expiry Date: {ret_info['expiry']}")
            
            if st.button("🗑️ Delete Retailer Terminal", type="primary"):
                now = datetime.now()
                is_expired = ret_info['expiry'] and ret_info['expiry'] < now
                
                if ret_info['is_demo'] or is_expired:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM enterprise_retailers WHERE id = %s;", (ret_info['id'],))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("Retailer terminal deleted successfully under allowed validity rules!")
                    st.rerun()
                else:
                    st.error("Deletion Blocked! Active paid subscription accounts cannot be deleted until their validity expires.")
        else:
            st.info("No retailers available.")

    # --- ADMIN WHITEBOARD & PRICING PANEL ---
    elif menu == "🛠️ Admin Whiteboard & Pricing":
        st.subheader("🛠️ Admin Whiteboard & Settings")
        st.write("Yahan se aap subscription rates aur admin security settings manage kar sakte hain.")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM whiteboard_settings WHERE key = 'monthly_rate';")
        m_rate = cur.fetchone()
        cur.execute("SELECT value FROM whiteboard_settings WHERE key = 'yearly_rate';")
        y_rate = cur.fetchone()
        cur.close()
        conn.close()

        current_monthly = int(m_rate[0]) if m_rate else 999
        current_yearly = int(y_rate[0]) if y_rate else 9999

        with st.form("whiteboard_form"):
            st.markdown("### 💰 Subscription Rates Management")
            monthly_rate = st.number_input("Monthly Subscription Rate (₹)", value=current_monthly, step=50)
            yearly_rate = st.number_input("Yearly Subscription Rate (₹)", value=current_yearly, step=500)
            
            st.markdown("### 🔐 Admin Password Update")
            new_admin_pass = st.text_input("New Admin Password (Leave blank if not changing)", type="password")
            
            submitted = st.form_submit_button("Save Whiteboard Settings")
            if submitted:
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    try:
                        cur.execute("UPDATE whiteboard_settings SET value = %s WHERE key = 'monthly_rate';", (str(monthly_rate),))
                        cur.execute("UPDATE whiteboard_settings SET value = %s WHERE key = 'yearly_rate';", (str(yearly_rate),))
                        
                        if new_admin_pass:
                            cur.execute("UPDATE enterprise_hierarchy SET password = %s WHERE username = 'admin';", (new_admin_pass,))
                        
                        conn.commit()
                        st.success("Whiteboard settings successfully updated and saved to Cloud Database! 🎉")
                    except Exception as ex:
                        st.error(f"Update Error: {ex}")
                    finally:
                        cur.close()
                        conn.close()

    # --- DOWNLOAD DESKTOP ICON ---
    elif menu == "Download Desktop Icon":
        st.subheader("💻 Download Desktop Shortcut")
        st.write("Apne desktop par is app ka shortcut banane ke liye niche diye gaye button par click karein:")
        
        desktop_shortcut_code = """[InternetShortcut]
URL=https://ampgpaejyolqvkizuiye.streamlit.app/
IconIndex=0
"""
        st.download_button(
            label="📥 Download .URL Shortcut",
            data=desktop_shortcut_code,
            file_name="TechPharma_Solutions.url",
            mime="text/plain"
        )
