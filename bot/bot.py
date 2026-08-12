from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config.config import BOT_TOKEN, ADMIN_ID
from bot.handlers import start, button_handler
from database.db import init_db, get_db
from telegram import Update
from telegram.ext import ContextTypes

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.text and update.message.text.startswith("TR"):
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        
        await update.message.reply_text(
            "✅ IBAN'ın alındı. Çekim talebin yöneticiye iletildi. Onay bekleniyor."
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💸 Yeni çekim talebi!\nKullanıcı: @{update.effective_user.username}\nIBAN: {update.message.text}"
        )
    
    elif update.message.text == "/panel" and str(user_id) == ADMIN_ID:
        conn = get_db()
        pending = conn.execute("SELECT COUNT(*) as count FROM withdrawals WHERE status='pending'").fetchone()
        users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        conn.close()
        
        await update.message.reply_text(
            f"🛡️ *Admin Panel*\n\n"
            f"👥 Toplam kullanıcı: {users['count']}\n"
            f"⏳ Bekleyen çekim: {pending['count']}",
            parse_mode="Markdown"
        )
    
    else:
        await update.message.reply_text(
            "Anlaşılmadı. Lütfen menüden bir seçenek seçin veya Mini App'i açın."
        )

def run_bot():
    init_db()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Turan Coin Bot başlatıldı!")
    
    app.run_polling()
