import threading
import os
import asyncio
import api
from bot.bot import run_bot
from backup import restore_from_github, start_backup_loop

if __name__ == '__main__':
    # Önce veritabanını yedekten geri yükle
    restore_from_github()
    
    # API'yi ayrı thread'de başlat
    port = int(os.environ.get('PORT', 10000))
    api_thread = threading.Thread(target=api.app.run, kwargs={'host': '0.0.0.0', 'port': port})
    api_thread.daemon = True
    api_thread.start()
    
    # Yedekleme döngüsünü başlat
    start_backup_loop()
    
    # Botu ana thread'de başlat (asyncio uyumlu)
    run_bot()
