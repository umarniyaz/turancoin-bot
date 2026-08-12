from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

def start_keyboard(webapp_url, is_premium=False):
    keyboard = [
        [InlineKeyboardButton("🚀 Mini App'i Aç", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton("💰 Bakiye Sorgula", callback_data="balance")],
        [InlineKeyboardButton("👥 Referans Sistemi", callback_data="referral")],
        [InlineKeyboardButton("👑 Premium", callback_data="premium")],
        [InlineKeyboardButton("💸 Para Çek", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Yardım", callback_data="help")]
    ]
    
    if is_premium:
        keyboard.insert(3, [InlineKeyboardButton("🚌 İstanbulkart Yükle", callback_data="istanbulkart")])
    
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def premium_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 Premium Satın Al", callback_data="buy_premium")],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_withdraw_keyboard(withdraw_id):
    keyboard = [
        [InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{withdraw_id}")],
        [InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{withdraw_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
