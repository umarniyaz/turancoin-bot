import os
import base64
import requests
import time
import threading

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
DB_REPO = os.environ.get('DB_REPO', '')
DB_PATH = 'database/turancoin.db'

def backup_to_github():
    if not GITHUB_TOKEN or not DB_REPO:
        print("Backup: Token veya repo bilgisi eksik")
        return
    
    if not os.path.exists(DB_PATH):
        print("Backup: Veritabanı dosyası bulunamadı")
        return
    
    try:
        with open(DB_PATH, 'rb') as f:
            content = base64.b64encode(f.read()).decode()
        
        url = f"https://api.github.com/repos/{DB_REPO}/contents/turancoin.db"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Mevcut dosyayı kontrol et
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Dosya var, güncelle
            sha = response.json()['sha']
            data = {
                'message': f'Backup {time.strftime("%Y-%m-%d %H:%M:%S")}',
                'content': content,
                'sha': sha
            }
        else:
            # Dosya yok, oluştur
            data = {
                'message': f'Backup {time.strftime("%Y-%m-%d %H:%M:%S")}',
                'content': content
            }
        
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print(f"✅ Backup başarılı: {time.strftime('%H:%M:%S')}")
        else:
            print(f"❌ Backup hatası: {response.status_code}")
            
    except Exception as e:
        print(f"Backup hatası: {e}")

def restore_from_github():
    if not GITHUB_TOKEN or not DB_REPO:
        print("Restore: Token veya repo bilgisi eksik")
        return
    
    try:
        url = f"https://api.github.com/repos/{DB_REPO}/contents/turancoin.db"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content = response.json()['content']
            db_data = base64.b64decode(content)
            
            os.makedirs('database', exist_ok=True)
            with open(DB_PATH, 'wb') as f:
                f.write(db_data)
            
            print("✅ Veritabanı GitHub'dan geri yüklendi")
            return True
        else:
            print("GitHub'da yedek bulunamadı")
            return False
            
    except Exception as e:
        print(f"Restore hatası: {e}")
        return False

def start_backup_loop():
    def loop():
        while True:
            time.sleep(300)  # 5 dakikada bir yedekle
            backup_to_github()
    
    thread = threading.Thread(target=loop)
    thread.daemon = True
    thread.start()
