from telegram import Update
from telegram.ext import ContextTypes
from config.config import MIN_WITHDRAWAL, PREMIUM_PRICE, REFERRAL_REWARD
from database.db import get_db
from utils.helpers import get_user, create_user, check_ip_limit, coin_to_tl, is_premium_active
from bot.keyboard import start_keyboard, back_keyboard, premium_keyboard, confirm_withdraw_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "Bilinmiyor"
    first_name = user.first_name or "Bilinmiyor"
    
    # IP kontrolü (gerçek uygulamada request'ten alınır, şimdilik placeholder)
    ip_address = "127.0.0.1"
    
    create_user(user_id, username, first_name, ip_address)
    
    # Referans kontrolü
    if context.args and len(context.args) > 0:
        referrer_id = int(context.args[0])
        if referrer_id != user_id:
            conn = get_db()
            existing = conn.execute(
                "SELECT * FROM referrals WHERE invited_id = ?", (user_id,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO referrals (inviter_id, invited_id) VALUES (?, ?)",
                    (referrer_id, user_id)
                )
                conn.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (REFERRAL_REWARD, referrer_id)
                )
                conn.commit()
            conn.close()
    
    webapp_url = "https://turan-coins.onrender.com"  # Geçici URL, sonra değişecek
    
    await update.message.reply_text(
        f"🪙 *Turan Coin'e Hoş Geldin {first_name}!*\n\n"
        "Reklam izle, coin kazan, paraya çevir!\n\n"
        "👇 Başlamak için Mini App'i aç:",
        reply_markup=start_keyboard(webapp_url),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "main_menu":
        webapp_url = "https://turan-coins.onrender.com"
        await query.edit_message_text(
            "🪙 *Ana Menü*\n\n👇 Başlamak için Mini App'i aç:",
            reply_markup=start_keyboard(webapp_url),
            parse_mode="Markdown"
        )
    
    elif query.data == "balance":
        user = get_user(user_id)
        is_prem = is_premium_active(user_id)
        tl_value = coin_to_tl(user["balance"], is_prem)
        
        await query.edit_message_text(
            f"💰 *Bakiyen*\n\n"
            f"Coin: {user['balance']}\n"
            f"TL Değeri: {tl_value:.2f} TL\n"
            f"Premium: {'✅ Aktif' if is_prem else '❌ Pasif'}\n"
            f"Toplam Kazanç: {user['total_earned']} coin",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "referral":
        await query.edit_message_text(
            f"👥 *Referans Sistemi*\n\n"
            f"Her davet ettiğin arkadaşın için {REFERRAL_REWARD} coin kazan!\n\n"
            f"🔗 Referans linkin:\n"
            f"https://t.me/turancoinsbot?start={user_id}\n\n"
            f"Linki arkadaşlarınla paylaş, kazanmaya başla!",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "premium":
        await query.edit_message_text(
            "👑 *Premium Üyelik*\n\n"
            f"• Coin değerin 5 katına çıkar (0.5 TL)\n"
            f"• Sınırsız reklam izleme\n"
            f"• Otomatik reklam izleme\n"
            f"• İstanbulkart yükleme\n\n"
            f"💰 Fiyat: {PREMIUM_PRICE} TL\n"
            f"💎 Maksimum kazanç: 30 TL",
            reply_markup=premium_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "withdraw":
        user = get_user(user_id)
        tl_value = coin_to_tl(user["balance"], is_premium_active(user_id))
        
        if tl_value < MIN_WITHDRAWAL:
            await query.edit_message_text(
                f"💸 *Para Çek*\n\n"
                f"Mevcut bakiyen: {tl_value:.2f} TL\n"
                f"Minimum çekim: {MIN_WITHDRAWAL} TL\n\n"
                f"❌ Henüz yeterli bakiyen yok.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"💸 *Para Çek*\n\n"
                f"Mevcut bakiyen: {tl_value:.2f} TL\n\n"
                f"Çekim talebi için IBAN'ını bot'a özel mesaj olarak gönder.\n"
                f"Örnek: TR00 0000 0000 0000 0000 0000 00",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
    
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ *Yardım*\n\n"
            "1. Mini App'i aç\n"
            "2. Reklam izle, coin kazan\n"
            "3. 50 TL olunca para çek\n\n"
            "📩 Destek için: @TuranCoinDestek",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "buy_premium":
        await query.edit_message_text(
            "👑 *Premium Satın Alma*\n\n"
            "Premium üyeliği satın almak için lütfen yönetici ile iletişime geç.\n\n"
            "📩 @TuranCoinDestek",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
