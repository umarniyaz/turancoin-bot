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
        f"/kart_red ID - İstanbulkart reddet\n"
        f"/uc_onay ID UC_MIKTARI - UC ver\n"
        f"/uc_red ID - UC reddet\n"
        f"/liderlik - Aylık liderlik",
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
            text="🎉 *Premium Üyeliğiniz Aktif!*\n\nArtık reklam başına 2 kat kazanıyorsunuz!",
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
    
    await update.message.reply_text(f"✅ İstanbulkart yükleme onaylandı! {target_id} ID'li kullanıcıdan 100 coin düşüldü.")
    
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
            text="❌ İstanbulkart yükleme talebiniz reddedildi."
        )
    except:
        pass

async def uc_onay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Kullanım: /uc_onay KULLANICI_ID UC_MIKTARI\nÖrnek: /uc_onay 123456 60")
        return
    
    target_id = int(context.args[0])
    uc_amount = int(context.args[1])
    
    # UC paketleri ve coin maliyetleri
    uc_packages = {
        60: 1500,
        120: 3000,
        300: 7333,
        600: 14666
    }
    
    if uc_amount not in uc_packages:
        await update.message.reply_text("❌ Geçersiz UC miktarı! Desteklenen: 60, 120, 300, 600")
        return
    
    coin_cost = uc_packages[uc_amount]
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone()
    
    if not user:
        conn.close()
        await update.message.reply_text("❌ Kullanıcı bulunamadı.")
        return
    
    if user['balance'] < coin_cost:
        conn.close()
        await update.message.reply_text(f"❌ Bakiyesi yetersiz! Gerekli: {coin_cost} coin, Mevcut: {user['balance']} coin")
        return
    
    new_balance = user['balance'] - coin_cost
    conn.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, target_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ {uc_amount} UC onaylandı! {target_id} ID'li kullanıcıdan {coin_cost} coin düşüldü.")
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎮 *PUBG UC Yüklendi!*\n\n✅ {uc_amount} UC hesabınıza tanımlandı.\nİyi oyunlar!",
            parse_mode="Markdown"
        )
    except:
        pass

async def uc_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    if not context.args:
        await update.message.reply_text("Kullanım: /uc_red KULLANICI_ID")
        return
    
    target_id = int(context.args[0])
    await update.message.reply_text(f"✅ {target_id} ID'li kullanıcının UC talebi reddedildi.")
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="❌ PUBG UC talebiniz reddedildi."
        )
    except:
        pass

async def liderlik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
        return
    
    from datetime import date
    current_month = date.today().strftime('%Y-%m')
    
    conn = get_db()
    top_users = conn.execute('''
        SELECT ml.user_id, ml.ads_count, u.username, u.first_name
        FROM monthly_leaderboard ml
        JOIN users u ON ml.user_id = u.user_id
        WHERE ml.month = ?
        ORDER BY ml.ads_count DESC
        LIMIT 10
    ''', (current_month,)).fetchall()
    conn.close()
    
    if not top_users:
        await update.message.reply_text("📊 Bu ay henüz veri yok.")
        return
    
    text = f"🏆 *Aylık Liderlik ({current_month})*\n\n"
    
    for i, row in enumerate(top_users, 1):
        medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'{i}.'
        name = row['first_name'] or row['username'] or 'Kullanıcı'
        text += f"{medal} {name}: {row['ads_count']} reklam\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

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
    app.add_handler(CommandHandler("uc_onay", uc_onay))
    app.add_handler(CommandHandler("uc_red", uc_red))
    app.add_handler(CommandHandler("liderlik", liderlik))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Turan Coin Bot başlatıldı!")
    
    asyncio.run(app.run_polling())
