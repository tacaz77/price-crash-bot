import telebot
import requests
import time
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = '8224578094:AAEOwXsE2aJly_LoMbS-5ud6FgT-O2rh3r8'
CHANNEL_ID = '@pricecrashpro_bot' 
ADMIN_ID = 123456789 # Твой ID (можно узнать у @userinfobot), чтобы бот тебя слушал
# -----------------

bot = telebot.TeleBot(TOKEN)

# База данных рефералов (в идеале нужна SQL, но для старта храним в памяти)
user_data = {}

def get_latest_giveaway():
    try:
        url = "https://www.gamerpower.com/api/giveaways"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()[0]
    except Exception as e:
        print(f"Ошибка API: {e}")
    return None

# 1. ПРИВЕТСТВИЕ И РЕФЕРАЛКА
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    args = message.text.split()
    
    # Логика реферала
    if len(args) > 1:
        referrer = args[1]
        if referrer.isdigit() and int(referrer) != user_id:
            bot.send_message(referrer, "🎉 По твоей ссылке перешел новый пользователь!")

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn1 = telebot.types.InlineKeyboardButton("📢 Перейти в канал", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")
    btn2 = telebot.types.InlineKeyboardButton("🎁 Моя реф-ссылка", callback_data="get_ref")
    btn3 = telebot.types.InlineKeyboardButton("🔍 Проверить купон", callback_data="check_coupon")
    markup.add(btn1, btn2, btn3)

    bot.send_message(user_id, 
        f"📉 **Price Crash Bot приветствует тебя!**\n\n"
        f"Я ищу ошибки в ценах и халяву 24/7. Основные посты выходят в канале, а здесь ты можешь управлять подпиской.", 
        reply_markup=markup, parse_mode="Markdown")

# 2. ОБРАБОТКА КНОПОК
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_ref":
        ref_link = f"https://t.me/pricecrashpro_bot?start={call.message.chat.id}"
        bot.send_message(call.message.chat.id, f"🔗 Твоя реферальная ссылка:\n`{ref_link}`\n\nПригласи 5 друзей и получи доступ к VIP-ошибкам цен!", parse_mode="Markdown")
    
    elif call.data == "check_coupon":
        bot.send_message(call.message.chat.id, "Пришли мне ссылку на товар или название магазина, и я попробую найти рабочий промокод! (Функция в разработке)")

# 3. МОНИТОРИНГ С КНОПКОЙ «ПОДЕЛИТЬСЯ»
def monitor():
    last_id = None
    while True:
        deal = get_latest_giveaway()
        if deal and deal['id'] != last_id:
            last_id = deal['id']
            
            caption = (
                f"💳 **PRICE CRASH: ОБНАРУЖЕНА ХАЛЯВА**\n\n"
                f"🔥 **{deal['title']}**\n"
                f"💰 Ценность: {deal['worth']}\n"
                f"✅ **СТАТУС: БЕСПЛАТНО**\n"
                f"🏢 Платформа: {deal['platforms']}"
            )
            
            # Кнопки: Забрать + Поделиться
            markup = telebot.types.InlineKeyboardMarkup()
            btn_get = telebot.types.InlineKeyboardButton(text="🎁 ЗАБРАТЬ", url=deal['open_giveaway_url'])
            
            # Ссылка для быстрой пересылки другу
            share_url = f"https://t.me/share/url?url=https://t.me/{CHANNEL_ID.replace('@', '')}&text=Смотри, какую халяву нашел в Price Crash!"
            btn_share = telebot.types.InlineKeyboardButton(text="📢 ПЕРЕСЛАТЬ ДРУГУ", url=share_url)
            
            markup.add(btn_get)
            markup.add(btn_share)

            try:
                bot.send_photo(CHANNEL_ID, deal['image'], caption=caption, reply_markup=markup, parse_mode="Markdown")
            except Exception as e:
                print(f"Ошибка отправки: {e}")
        
        time.sleep(1800)

if __name__ == "__main__":
    Thread(target=monitor).start()
    bot.infinity_polling()
