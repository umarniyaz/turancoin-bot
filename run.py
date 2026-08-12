import threading
import api
from bot.bot import run_bot

if __name__ == '__main__':
    # API'yi ayrı thread'de başlat
    api_thread = threading.Thread(target=api.app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    api_thread.daemon = True
    api_thread.start()
    
    # Botu başlat
    run_bot()
