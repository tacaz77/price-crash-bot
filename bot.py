import telebot
import requests
import time
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = 'ТВОЙ_ТОКЕН_БОТА'
CHANNEL_ID = '@ТВОЙ_КАНАЛ'
# -----------------

bot = telebot.TeleBot(TOKEN)

def get_latest_giveaway():
    try:
        url = "https://www.gamerpower.com/api/giveaways"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()[0]
    except Exception as e:
        print(f"Ошибка API: {e}")
    return None

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
                f"✅ **СТАТУС: БЕСПЛАТНО**\n\n"
                f"🏢 Платформа: {deal['platforms']}"
            )
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text="🎁 ЗАБРАТЬ", url=deal['open_giveaway_url']))
            
            try:
                bot.send_photo(CHANNEL_ID, deal['image'], caption=caption, reply_markup=markup, parse_mode="Markdown")
            except Exception as e:
                print(f"Ошибка отправки: {e}")
        time.sleep(1800)

if __name__ == "__main__":
    Thread(target=monitor).start()
    bot.infinity_polling()
