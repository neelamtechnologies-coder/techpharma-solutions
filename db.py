import os
import hashlib
import psycopg2
import streamlit as st

def get_db_connection():
    db_url = st.secrets.get("DATABASE_URL", "")
    if not db_url:
        st.error("DATABASE_URL is missing in Streamlit Secrets! Please add your Supabase connection string.")
        st.stop()
    conn = psycopg2.connect(db_url, sslmode='require')import streamlit as st
import psycopg2

def get_db_connection():
    try:
        database_url = st.secrets["DATABASE_URL"]
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    try:
        # Hierarchy Users Table supporting exact enterprise chain with parent references
        cur.execute("""
            CREATE TABLE IF NOT EXISTS enterprise_hierarchy (
                id SERIAL PRIMARY KEY,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                parent_id INTEGER REFERENCES enterprise_hierarchy(id) ON DELETE SET NULL
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

        # Retailers & Terminals Table with Demo & Validity tracking
        cur.execute("""
            CREATE TABLE IF NOT EXISTS enterprise_retailers (
                id SERIAL PRIMARY KEY,
                store_name TEXT NOT NULL,
                owner_name TEXT,
                gstin TEXT,
                phone TEXT,
                address TEXT,
                sse_id INTEGER REFERENCES enterprise_hierarchy(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_expiry TIMESTAMP,
                is_demo BOOLEAN DEFAULT TRUE
            );
        """)
        
        conn.commit()

        # Insert Default Super Admin if not exists
        cur.execute("SELECT COUNT(*) FROM enterprise_hierarchy WHERE username = 'admin';")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO enterprise_hierarchy (role, name, email, phone, username, password, parent_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, ("OWNER", "System Owner", "admin@techpharma.com", "9999999999", "admin", "admin123", None))
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
        conn.close()    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS system_config (
            id SERIAL PRIMARY KEY, 
            company_name TEXT DEFAULT 'Neelam Technologies', 
            super_admin_username TEXT DEFAULT 'admin', 
            super_admin_password_hash TEXT DEFAULT '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 
            upi_id TEXT DEFAULT 'neelamtech@upi', 
            admin_phone TEXT DEFAULT '919876543210',
            gemini_api_key TEXT DEFAULT ''
        );""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS hierarchy_users (
            id SERIAL PRIMARY KEY,
            parent_id INTEGER,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")

        c.execute("""CREATE TABLE IF NOT EXISTS retailers (
            id SERIAL PRIMARY KEY, 
            assigned_sse_id INTEGER, 
            store_name TEXT NOT NULL, 
            owner_name TEXT, 
            email TEXT UNIQUE NOT NULL, 
            phone TEXT, 
            username TEXT UNIQUE NOT NULL, 
            password_hash TEXT NOT NULL, 
            store_type TEXT DEFAULT 'SINGLE', 
            subscription_status TEXT DEFAULT 'TRIAL', 
            plan_expiry_date TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'), 
            payment_status TEXT DEFAULT 'ACTIVE',
            gstin TEXT DEFAULT '27AAAAA0000A1Z5'
        );""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS store_terminals (
            id SERIAL PRIMARY KEY, 
            retailer_id INTEGER, 
            terminal_name TEXT NOT NULL, 
            terminal_type TEXT DEFAULT 'CLIENT', 
            username TEXT UNIQUE NOT NULL, 
            password_hash TEXT NOT NULL
        );""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY, 
            retailer_id INTEGER, 
            name TEXT NOT NULL, 
            batch TEXT, 
            quantity INTEGER, 
            price REAL DEFAULT 0.0,
            barcode TEXT DEFAULT '',
            gst_rate REAL DEFAULT 12.0
        );""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY, 
            retailer_id INTEGER, 
            invoice_number TEXT NOT NULL, 
            total_amount REAL NOT NULL, 
            cgst REAL DEFAULT 0.0,
            sgst REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")

        c.execute("""CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            retailer_id INTEGER,
            supplier_name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            gstin TEXT,
            outstanding_balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")

        c.execute("""CREATE TABLE IF NOT EXISTS purchase_orders (
            id SERIAL PRIMARY KEY,
            retailer_id INTEGER,
            supplier_id INTEGER,
            po_number TEXT NOT NULL,
            items_summary TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")

        c.execute("""CREATE TABLE IF NOT EXISTS schedule_h1_register (
            id SERIAL PRIMARY KEY,
            retailer_id INTEGER,
            patient_name TEXT NOT NULL,
            patient_address TEXT,
            doctor_name TEXT NOT NULL,
            doctor_qualification TEXT,
            medicine_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            prescription_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
        
        conn.commit()

        c.execute("SELECT COUNT(*) FROM system_config;")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO system_config (company_name, super_admin_username, super_admin_password_hash) VALUES ('Neelam Technologies', 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918');")
            conn.commit()

        conn.close()
    except Exception as e:
        st.error(f"Database Init Error: {e}")

def setup_local_environment():
    pass
