import sqlite3

def get_db():
    conn = sqlite3.connect("database/turancoin.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Kullanıcı tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            total_earned REAL DEFAULT 0,
            ads_watched_today INTEGER DEFAULT 0,
            last_ad_time TEXT,
            is_premium INTEGER DEFAULT 0,
            premium_earned REAL DEFAULT 0,
            premium_expiry TEXT,
            ip_address TEXT,
            banned INTEGER DEFAULT 0,
            join_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Referans tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id INTEGER,
            invited_id INTEGER,
            reward_given INTEGER DEFAULT 0,
            date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Çekim talepleri
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            iban TEXT,
            status TEXT DEFAULT 'pending',
            request_date TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
