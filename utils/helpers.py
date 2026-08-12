from datetime import datetime, date
from config.config import NORMAL_COIN_VALUE, PREMIUM_COIN_VALUE, NORMAL_DAILY_AD_LIMIT
from database.db import get_db

def get_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name, ip_address):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, ip_address) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, ip_address)
    )
    conn.commit()
    conn.close()

def check_ip_limit(ip_address):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) as count FROM users WHERE ip_address = ?", (ip_address,)
    ).fetchone()["count"]
    conn.close()
    return count

def check_daily_ad_limit(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    today = date.today().isoformat()
    last_date = user["last_ad_time"][:10] if user["last_ad_time"] else None
    
    if last_date != today:
        conn = get_db()
        conn.execute("UPDATE users SET ads_watched_today = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return False
    
    return user["ads_watched_today"] >= NORMAL_DAILY_AD_LIMIT

def coin_to_tl(coins, is_premium=False):
    value = PREMIUM_COIN_VALUE if is_premium else NORMAL_COIN_VALUE
    return coins * value

def is_premium_active(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user or not user["is_premium"]:
        return False
    
    if user["premium_earned"] >= user["premium_expiry"]:
        return False
    
    return True

def check_auto_clicker(user_id, last_time):
    if last_time:
        diff = (datetime.now() - datetime.fromisoformat(last_time)).total_seconds()
        if diff < 5:  # 5 saniyeden hızlı izlenemez
            return True
    return False
