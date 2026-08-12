from flask import Flask, request, jsonify
from database.db import get_db, init_db
from utils.helpers import get_user, create_user, coin_to_tl, is_premium_active
import json

app = Flask(__name__)

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
        return jsonify({
            'success': True,
            'balance': user['balance'],
            'total_earned': user['total_earned'],
            'ads_watched_today': user['ads_watched_today'],
            'is_premium': is_prem
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
        new_total = user['total_earned'] + coins
        new_ads = user['ads_watched_today'] + 1
        
        conn.execute(
            "UPDATE users SET balance = ?, total_earned = ?, ads_watched_today = ?, last_ad_time = datetime('now') WHERE user_id = ?",
            (new_balance, new_total, new_ads, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_balance': new_balance})
    
    conn.close()
    return jsonify({'success': False})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
