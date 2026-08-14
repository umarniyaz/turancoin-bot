from flask import Flask, request, jsonify
from flask_cors import CORS
from database.db import get_db, init_db
from utils.helpers import get_user, create_user, coin_to_tl, is_premium_active
from datetime import date

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
        
        # Aylık liderlik puanı
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
