import streamlit as st
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
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS whiteboard_settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL
            );
        """)

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
                is_demo BOOLEAN DEFAULT TRUE,
                system_type TEXT DEFAULT 'Single System'
            );
        """)
        
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM enterprise_hierarchy WHERE username = 'admin';")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO enterprise_hierarchy (role, name, email, phone, username, password, parent_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, ("OWNER", "System Owner", "admin@techpharma.com", "9999999999", "admin", "admin123", None))
            conn.commit()

        # Default Whiteboard Settings (Single & Multi-System Rates)
        defaults = [
            ('monthly_rate', '999'),
            ('yearly_rate', '9999'),
            ('multi_monthly_rate', '1999'),
            ('multi_yearly_rate', '19999')
        ]
        for key, val in defaults:
            cur.execute("SELECT COUNT(*) FROM whiteboard_settings WHERE key = %s;", (key,))
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO whiteboard_settings (key, value) VALUES (%s, %s);", (key, val))
                conn.commit()

    except Exception as e:
        st.error(f"Table Init Error: {e}")
    finally:
        cur.close()
        conn.close()
