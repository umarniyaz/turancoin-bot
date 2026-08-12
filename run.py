import threading
import os
import asyncio
import api
from bot.bot import run_bot

if __name__ == '__main__':
    # API'yi ayrı thread'de başlat
    port = int(os.environ.get('PORT', 10000))
    api_thread = threading.Thread(target=api.app.run, kwargs={'host': '0.0.0.0', 'port': port})
    api_thread.daemon = True
    api_thread.start()
    
    # Botu asyncio ile başlat
    asyncio.run(run_bot())
