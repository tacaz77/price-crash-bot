import telebot
import requests
import time
from threading import Thread
from flask import Flask
import os

# --- НАСТРОЙКИ (ЗАПОЛНИ СВОИ ДАННЫЕ) ---
TOKEN = '8224578094:AAHRZdg6j8XWLpgqWqFeyeaFSIqeMT2vPIc' 
CHANNEL_ID = '@pricecrashpro' 
# Твоя реферальная ссылка или ссылка на канал для ЛС
REF_LINK = f"https://t.me/{CHANNEL_ID.replace('@', '')}" 
# ---------------------------------------

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask('')

@app.route('/')
def home():
    return "Status: Online"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

posted_ids = set()

# --- ПАРСЕРЫ ---

def get_wb():
    try:
        url = "https://catalog.wb.ru/catalog/electronic/v4/filters?appType=1&curr=rub&dest=-1257786&subject=7000"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if res.status_code == 200:
            products = res.json().get('data', {}).get('products', [])
            for item in products:
                if item.get('sale', 0) >= 90:
                    return {
                        'id': f"wb_{item['id']}",
                        'title': f"WB: {item['brand']} {item['name']}",
                        'old': f"{item['priceU']/100} ₽",
                        'new': f"{item['salePriceU']/100} ₽",
                        'link': f"https://www.wildberries.ru/catalog/{item['id']}/detail.aspx",
                        'img': f"https://basket-01.wb.ru/vol{item['id']//100000}/part{item['id']//1000}/{item['id']}/images/big/1.jpg"
                    }
    except: return None

def get_games():
    try:
        res = requests.get("https://www.gamerpower.com/api/giveaways", timeout=10)
        if res.status_code == 200:
            item = res.json()[0]
            return {
                'id': f"game_{item['id']}",
                'title': item['title'],
                'old': item.get('worth', 'FREE'),
                'new': '0 ₽ (Раздача)',
                'link': item['open_giveaway_url'],
                'img': item['image']
            }
    except: return None

# --- ОТПРАВКА ---

def send_post(deal, platform):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎁 ЗАБРАТЬ ПО АКЦИИ", url=deal['link']))
    caption = (
        f"🚨 **ЦЕНА РУХНУЛА!** ({platform})\n\n"
        f"🔥 **{deal['title']}**\n"
        f"❌ Старая цена: {deal['old']}\n"
        f"✅ **НОВАЯ ЦЕНА: {deal['new']}**\n\n"
        f"📍 Ссылка в кнопке ниже!"
    )
    try:
        bot.send_photo(CHANNEL_ID, deal['img'], caption=caption, reply_markup=markup, parse_mode="Markdown")
    except: pass

# --- МОНИТОРИНГ ---

def monitor():
    print("Мониторинг запущен...")
    while True:
        # Проверяем WB
        wb_deal = get_wb()
        if wb_deal and wb_deal['id'] not in posted_ids:
            posted_ids.add(wb_deal['id'])
            send_post(wb_deal, "Wildberries")
        
        # Проверяем Игры
        game_deal = get_games()
        if game_deal and game_deal['id'] not in posted_ids:
            posted_ids.add(game_deal['id'])
            send_post(game_deal, "GamerPower")

        time.sleep(900) # Проверка каждые 15 минут

# --- КОМАНДЫ В ЛС ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔥 ПЕРЕЙТИ К СКИДКАМ", url=REF_LINK))
    bot.reply_to(message, 
        f"Привет! 🤖 Я ищу ошибки цен и раздачи 24/7.\n\n"
        f"Чтобы успеть купить товары со скидкой до 90%, подпишись на наш основной канал!", 
        reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Все актуальные скидки публикуются только в канале! Нажми /start для ссылки.")

# --- ЗАПУСК ---

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    Thread(target=monitor, daemon=True).start()
    
    bot.remove_webhook()
    time.sleep(1)
    
    print("Бот запущен...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
