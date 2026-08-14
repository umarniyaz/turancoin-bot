from flask import Flask, request, jsonify
from flask_cors import CORS
from database.db import get_db, init_db
from utils.helpers import get_user, create_user, coin_to_tl, is_premium_active
from datetime import date
import time

app = Flask(__name__)
CORS(app)

def get_lig(total_ads):
    if total_ads >= 3001:
        return {'name': 'Efsane', 'rate': 0.25}
    elif total_ads >= 1501:
        return {'name': 'Elit', 'rate': 0.18}
    elif total_ads >= 701:
        return {'name': 'Platin', 'rate': 0.12}
    elif total_ads >= 301:
        return {'name': 'Altın', 'rate': 0.08}
    elif total_ads >= 101:
        return {'name': 'Gümüş', 'rate': 0.05}
    else:
        return {'name': 'Bronz', 'rate': 0.03}

def get_miner_duration(plan):
    if plan == 'pro':
        return 24 * 60 * 60
    elif plan == 'apex':
        return 30 * 24 * 60 * 60
    else:
        return 3 * 60 * 60

def get_miner_rate(plan):
    if plan == 'pro':
        return 3
    elif plan == 'apex':
        return 10
    else:
        return 1

@app.route('/api/get_user', methods=['POST'])
def get_user_data():
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    ip_address = request.remote_addr or '127.0.0.1'
    
    create_user(user_id, username, first_name, ip_address)
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    if user:
        is_prem = is_premium_active(user_id)
        total_ads = int(user['total_earned'])
        lig = get_lig(total_ads)
        
        if is_prem:
            lig['rate'] = lig['rate'] * 2
        
        return jsonify({
            'success': True,
            'balance': user['balance'],
            'total_earned': user['total_earned'],
            'ads_watched_today': user['ads_watched_today'],
            'is_premium': is_prem,
            'lig_name': lig['name'],
            'lig_rate': lig['rate']
        })
    return jsonify({'success': False})

@app.route('/api/add_coins', methods=['POST'])
def add_coins():
    data = request.json
    user_id = data.get('user_id')
    coins = data.get('coins', 0)
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    if user:
        new_balance = user['balance'] + coins
        new_total = user['total_earned'] + 1
        new_ads = user['ads_watched_today'] + 1
        
        conn.execute(
            "UPDATE users SET balance = ?, total_earned = ?, ads_watched_today = ?, last_ad_time = datetime('now') WHERE user_id = ?",
            (new_balance, new_total, new_ads, user_id)
        )
        
        current_month = date.today().strftime('%Y-%m')
        conn.execute('''
            INSERT INTO monthly_leaderboard (user_id, month, ads_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, month) DO UPDATE SET ads_count = ads_count + 1
        ''', (user_id, current_month))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_balance': new_balance, 'total_earned': new_total})
    
    conn.close()
    return jsonify({'success': False})

@app.route('/api/leaderboard', methods=['POST'])
def get_leaderboard():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db()
    current_month = date.today().strftime('%Y-%m')
    
    top_users = conn.execute('''
        SELECT ml.user_id, ml.ads_count, u.username, u.first_name
        FROM monthly_leaderboard ml
        JOIN users u ON ml.user_id = u.user_id
        WHERE ml.month = ?
        ORDER BY ml.ads_count DESC
        LIMIT 10
    ''', (current_month,)).fetchall()
    
    user_rank = conn.execute('''
        SELECT COUNT(*) as rank FROM monthly_leaderboard
        WHERE month = ? AND ads_count > (
            SELECT COALESCE(ads_count, 0) FROM monthly_leaderboard WHERE user_id = ? AND month = ?
        )
    ''', (current_month, user_id, current_month)).fetchone()
    
    user_ads = conn.execute('''
        SELECT ads_count FROM monthly_leaderboard WHERE user_id = ? AND month = ?
    ''', (user_id, current_month)).fetchone()
    
    conn.close()
    
    top_list = []
    for row in top_users:
        top_list.append({
            'user_id': row['user_id'],
            'ads_count': row['ads_count'],
            'username': row['username'] or 'Bilinmiyor',
            'first_name': row['first_name'] or 'Kullanıcı'
        })
    
    return jsonify({
        'success': True,
        'top_users': top_list,
        'user_rank': (user_rank['rank'] + 1) if user_rank else 1,
        'user_ads': user_ads['ads_count'] if user_ads else 0
    })

# ============ MINER ENDPOINTLERİ ============

@app.route('/api/miner_start', methods=['POST'])
def miner_start():
    data = request.json
    user_id = data.get('user_id')
    plan = data.get('plan', 'temel')
    
    conn = get_db()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS miner_status (
            user_id INTEGER PRIMARY KEY,
            plan TEXT DEFAULT 'temel',
            start_time REAL,
            end_time REAL,
            total_coins REAL DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            last_check_time REAL
        )
    ''')
    
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False})
    
    current_time = time.time()
    duration = get_miner_duration(plan)
    
    conn.execute('''
        INSERT INTO miner_status (user_id, plan, start_time, end_time, total_coins, is_active, last_check_time)
        VALUES (?, ?, ?, ?, 0, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        plan = ?,
        start_time = ?,
        end_time = ?,
        is_active = 1,
        last_check_time = ?
    ''', (user_id, plan, current_time, current_time + duration, current_time, plan, current_time, current_time + duration, current_time))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'end_time': current_time + duration})

@app.route('/api/miner_status', methods=['POST'])
def miner_status():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS miner_status (
            user_id INTEGER PRIMARY KEY,
            plan TEXT DEFAULT 'temel',
            start_time REAL,
            end_time REAL,
            total_coins REAL DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            last_check_time REAL
        )
    ''')
    
    status = conn.execute("SELECT * FROM miner_status WHERE user_id = ?", (user_id,)).fetchone()
    
    if status and status['is_active'] == 1:
        current_time = time.time()
        
        if current_time >= status['end_time']:
            # Süre doldu, coinleri hesapla ve ana bakiyeye ekle
            elapsed = status['end_time'] - status['start_time']
            rate = get_miner_rate(status['plan'])
            miner_coin_rate = 8 / (3 * 60 * 60)
            earned = elapsed * miner_coin_rate * rate
            
            coins_int = int(earned)
            new_total = status['total_coins'] + earned
            
            if coins_int > 0:
                conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (coins_int, user_id))
            
            conn.execute('''
                UPDATE miner_status SET is_active = 0, total_coins = ? WHERE user_id = ?
            ''', (new_total, user_id))
            conn.commit()
            
            conn.close()
            return jsonify({
                'success': True,
                'is_active': False,
                'plan': status['plan'],
                'total_coins': new_total,
                'earned': earned
            })
        else:
            # Miner aktif, geçen süreyi hesapla
            elapsed = current_time - status['start_time']
            rate = get_miner_rate(status['plan'])
            miner_coin_rate = 8 / (3 * 60 * 60)
            earned = elapsed * miner_coin_rate * rate
            
            conn.close()
            return jsonify({
                'success': True,
                'is_active': True,
                'plan': status['plan'],
                'start_time': status['start_time'],
                'end_time': status['end_time'],
                'total_coins': status['total_coins'],
                'earned': earned,
                'remaining': status['end_time'] - current_time
            })
    
    conn.close()
    return jsonify({
        'success': True,
        'is_active': False,
        'plan': status['plan'] if status else 'temel',
        'total_coins': status['total_coins'] if status else 0,
        'earned': 0,
        'remaining': 0
    })

@app.route('/api/miner_stop', methods=['POST'])
def miner_stop():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db()
    status = conn.execute("SELECT * FROM miner_status WHERE user_id = ?", (user_id,)).fetchone()
    
    if status and status['is_active'] == 1:
        current_time = time.time()
        elapsed = current_time - status['start_time']
        rate = get_miner_rate(status['plan'])
        miner_coin_rate = 8 / (3 * 60 * 60)
        earned = elapsed * miner_coin_rate * rate
        
        coins_int = int(earned)
        new_total = status['total_coins'] + earned
        
        if coins_int > 0:
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (coins_int, user_id))
        
        conn.execute('''
            UPDATE miner_status SET is_active = 0, total_coins = ? WHERE user_id = ?
        ''', (new_total, user_id))
        conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'earned': earned, 'total_coins': new_total})
    
    conn.close()
    return jsonify({'success': False})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
