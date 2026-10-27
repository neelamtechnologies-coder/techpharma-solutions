import streamlit as st
import psycopg2
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TechPharma Solutions",
    page_icon="💊",
    layout="wide"
)

# --- DATABASE CONNECTION ---
def get_db_connection():
    try:
        database_url = st.secrets["DATABASE_URL"]
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

# --- INITIALIZE TABLES ---
def init_db():
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    try:
        # Users / Hierarchy Table (v2 with all required columns)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hierarchy_users_v2 (
                id SERIAL PRIMARY KEY,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)
        
        # Whiteboard Settings Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS whiteboard_settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL
            );
        """)

        # Retailers Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS retailers (
                id SERIAL PRIMARY KEY,
                store_name TEXT NOT NULL,
                owner_name TEXT,
                gstin TEXT,
                phone TEXT,
                address TEXT
            );
        """)
        
        conn.commit()

        # Insert Default Super Admin if not exists
        cur.execute("SELECT COUNT(*) FROM hierarchy_users_v2 WHERE username = 'admin';")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO hierarchy_users_v2 (role, name, email, phone, username, password)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, ("SUPER_ADMIN", "System Owner", "admin@techpharma.com", "9999999999", "admin", "admin123"))
            conn.commit()

        # Insert Default Whiteboard Settings if not exists
        cur.execute("SELECT COUNT(*) FROM whiteboard_settings WHERE key = 'monthly_rate';")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO whiteboard_settings (key, value) VALUES ('monthly_rate', '999');")
            cur.execute("INSERT INTO whiteboard_settings (key, value) VALUES ('yearly_rate', '9999');")
            conn.commit()

    except Exception as e:
        st.error(f"Table Init Error: {e}")
    finally:
        cur.close()
        conn.close()

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
                cur.execute("SELECT role, password FROM hierarchy_users_v2 WHERE username = %s;", (username,))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user and user[1] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user[0]
                    st.success("Login Successful! Reloading...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
else:
    # --- SIDEBAR MENU ---
    st.sidebar.markdown(f"### User: {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {st.session_state.role}")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Navigation", ["Owner Central Command", "🛠️ Admin Whiteboard & Pricing", "Download Desktop Icon"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    # --- OWNER CENTRAL COMMAND (HIERARCHY & DASHBOARD) ---
    if menu == "Owner Central Command":
        st.subheader("🛡️ Owner Central Command (Global Enterprise)")
        
        tab1, tab2 = st.tabs(["🌍 All Hierarchy Nodes", "➕ Add Hierarchy Member"])
        
        with tab1:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT id, role, name, email, phone, username FROM hierarchy_users_v2;")
                members = cur.fetchall()
                
                st.markdown("### Hierarchy Members")
                if members:
                    df = pd.DataFrame(members, columns=["ID", "Role", "Name", "Email", "Phone", "Username"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No hierarchy members found.")

                st.markdown("### All Retailers")
                cur.execute("SELECT id, store_name, owner_name, gstin, phone, address FROM retailers;")
                retailers = cur.fetchall()
                if retailers:
                    df_ret = pd.DataFrame(retailers, columns=["ID", "Store Name", "Owner", "GSTIN", "Phone", "Address"])
                    st.dataframe(df_ret, use_container_width=True)
                else:
                    st.info("No retailers registered yet.")
                
                cur.close()
                conn.close()

        with tab2:
            st.markdown("### Add New Hierarchy Member")
            with st.form("add_member_form"):
                new_role = st.selectbox("Role", ["COUNTRY_HEAD", "ZONAL_MANAGER", "SALES_ENGINEER"])
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email")
                new_phone = st.text_input("Phone Number")
                new_uname = st.text_input("Username")
                new_upass = st.text_input("Password", type="password")
                
                add_sub = st.form_submit_button("Save Member")
                if add_sub:
                    if new_name and new_uname and new_upass:
                        conn = get_db_connection()
                        if conn:
                            cur = conn.cursor()
                            try:
                                cur.execute("""
                                    INSERT INTO hierarchy_users_v2 (role, name, email, phone, username, password)
                                    VALUES (%s, %s, %s, %s, %s, %s);
                                """, (new_role, new_name, new_email, new_phone, new_uname, new_upass))
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

    # --- ADMIN WHITEBOARD & PRICING PANEL ---
    elif menu == "🛠️ Admin Whiteboard & Pricing":
        st.subheader("🛠️ Admin Whiteboard & Settings")
        st.write("Yahan se aap subscription rates aur admin security settings manage kar sakte hain.")

        # Fetch current rates from DB
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
                        # Update rates
                        cur.execute("UPDATE whiteboard_settings SET value = %s WHERE key = 'monthly_rate';", (str(monthly_rate),))
                        cur.execute("UPDATE whiteboard_settings SET value = %s WHERE key = 'yearly_rate';", (str(yearly_rate),))
                        
                        # Update password if provided
                        if new_admin_pass:
                            cur.execute("UPDATE hierarchy_users_v2 SET password = %s WHERE username = 'admin';", (new_admin_pass,))
                        
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
