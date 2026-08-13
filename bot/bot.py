import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config.config import BOT_TOKEN, ADMIN_ID, MIN_WITHDRAWAL
from bot.handlers import start, button_handler
from database.db import init_db, get_db
from telegram import Update
from telegram.ext import ContextTypes

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.text and update.message.text.startswith("TR"):
        await update.message.reply_text(
            "✅ IBAN'ın alındı. Çekim talebin yöneticiye iletildi. Onay bekleniyor."
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💸 Yeni çekim talebi!\nKullanıcı: @{update.effective_user.username}\nID: {user_id}\nIBAN: {update.message.text}"
        )
    
    else:
        await update.message.reply_text(
            "Anlaşılmadı. Lütfen menüden bir seçenek seçin veya Mini App'i açın."
        )

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    conn = get_db()
    users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
    premium = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_premium = 1").fetchone()
    conn.close()
    
    await update.message.reply_text(
        f"🛡️ *Admin Panel*\n\n"
        f"👥 Toplam kullanıcı: {users['count']}\n"
        f"👑 Premium kullanıcı: {premium['count']}\n\n"
        f"Komutlar:\n"
        f"/kontrol ID - Kullanıcı detayı\n"
        f"/premium_onay ID - Premium ver\n"
        f"/premium_iptal ID - Premium al\n"
        f"/kart_onay ID - İstanbulkart onayla\n"
        f"/kart_red ID - İstanbulkart reddet",
        parse_mode="Markdown"
    )

async def kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("Kullanım: /kontrol KULLANICI_ID")
        return
    
    target_id = int(context.args[0])
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    
    if not user:
        await update.message.reply_text("❌ Kullanıcı bulunamadı.")
        return
    
    premium_durum = "✅ Aktif" if user['is_premium'] else "❌ Pasif"
    
    await update.message.reply_text(
        f"👤 *Kullanıcı Detayı*\n\n"
        f"🆔 ID: {user['user_id']}\n"
        f"👤 İsim: {user['first_name']}\n"
        f"📛 Kullanıcı adı: @{user['username']}\n"
        f"🪙 Bakiye: {user['balance']} coin\n"
        f"💰 Toplam kazanç: {user['total_earned']} coin\n"
        f"📊 Bugün izlenen: {user['ads_watched_today']}\n"
        f"👑 Premium: {premium_durum}\n"
        f"📅 Kayıt: {user['join_date']}",
        parse_mode="Markdown"
    )

async def premium_onay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("Kullanım: /premium_onay KULLANICI_ID")
        return
    
    target_id = int(context.args[0])
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone()
    
    if not user:
        conn.close()
        await update.message.reply_text("❌ Kullanıcı bulunamadı.")
        return
    
    conn.execute(
        "UPDATE users SET is_premium = 1, premium_expiry = '2099-01-01' WHERE user_id = ?",
        (target_id,)
    )
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ {target_id} ID'li kullanıcıya premium verildi!")
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="🎉 *Premium Üyeliğiniz Aktif!*\n\nArtık reklam başına 0.5 TL kazanıyorsunuz!",
            parse_mode="Markdown"
        )
    except:
        pass

async def premium_iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("Kullanım: /premium_iptal KULLANICI_ID")
        return
    
    target_id = int(context.args[0])
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone()
    
    if not user:
        conn.close()
        await update.message.reply_text("❌ Kullanıcı bulunamadı.")
        return
    
    conn.execute("UPDATE users SET is_premium = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ {target_id} ID'li kullanıcının premiumu iptal edildi!")

async def kart_onay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("Kullanım: /kart_onay KULLANICI_ID")
        return
    
    target_id = int(context.args[0])
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone()
    
    if not user:
        conn.close()
        await update.message.reply_text("❌ Kullanıcı bulunamadı.")
        return
    
    if not user['is_premium']:
        conn.close()
        await update.message.reply_text("❌ Bu kullanıcı premium değil!")
        return
    
    if user['balance'] < 100:
        conn.close()
        await update.message.reply_text("❌ Kullanıcının bakiyesi yetersiz! (Gerekli: 100 coin)")
        return
    
    new_balance = user['balance'] - 100
    conn.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, target_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ İstanbulkart yükleme onaylandı! {target_id} ID'li kullanıcıdan 100 coin düşüldü. Yeni bakiye: {new_balance} coin")
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="🚌 *İstanbulkart Yükleme Onaylandı!*\n\n50 TL İstanbulkart'ınıza yüklendi.",
            parse_mode="Markdown"
        )
    except:
        pass

async def kart_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("Kullanım: /kart_red KULLANICI_ID")
        return
    
    target_id = int(context.args[0])
    
    await update.message.reply_text(f"✅ {target_id} ID'li kullanıcının İstanbulkart talebi reddedildi.")
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="❌ İstanbulkart yükleme talebiniz reddedildi. Detay için @turancoinsdestek"
        )
    except:
        pass

def run_bot():
    init_db()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("kontrol", kontrol))
    app.add_handler(CommandHandler("premium_onay", premium_onay))
    app.add_handler(CommandHandler("premium_iptal", premium_iptal))
    app.add_handler(CommandHandler("kart_onay", kart_onay))
    app.add_handler(CommandHandler("kart_red", kart_red))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Turan Coin Bot başlatıldı!")
    
    asyncio.run(app.run_polling())
