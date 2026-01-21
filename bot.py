import telebot
import requests
import time
from threading import Thread
from flask import Flask
import os

# --- НАСТРОЙКИ ---
TOKEN = '8224578094:AAHRZdg6j8XWLpgqWqFeyeaFSIqeMT2vPIc' 
CHANNEL_ID = '@pricecrashpro'
# -----------------

bot = telebot.TeleBot(TOKEN, threaded=False) # threaded=False помогает избежать 409
app = Flask('')

@app.route('/')
def home():
    return "OK"

def run_web_server():
    # Render передает порт в переменную окружения PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

posted_ids = set()

# --- ПАРСЕРЫ (WB, Ali, M.Video) ---
def get_wb_errors():
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
    return None

# --- ОТПРАВКА ---
def send_post(deal, platform):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎁 КУПИТЬ / ЗАБРАТЬ", url=deal['link']))
    caption = (f"🚨 **ЦЕНА РУХНУЛА!**\n\n🔥 {deal['title']}\n❌ Было: {deal['old']}\n"
               f"✅ **СТАЛО: {deal['new']}**\n\n🏢 Площадка: {platform}")
    try:
        bot.send_photo(CHANNEL_ID, deal['img'], caption=caption, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

# --- МОНИТОРИНГ (В ОТДЕЛЬНОМ ПОТОКЕ) ---
def monitor():
    print("Мониторинг запущен...")
    while True:
        deal = get_wb_errors() # Пока тестим на WB, потом добавь Ali и M.Video
        if deal and deal['id'] not in posted_ids:
            posted_ids.add(deal['id'])
            send_post(deal, "Wildberries")
        time.sleep(600) # Проверка раз в 10 минут

# --- ОБРАБОТКА ЛС ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот активен! Все скидки в канале.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # 1. Запускаем веб-сервер
    Thread(target=run_web_server, daemon=True).start()
    
    # 2. Запускаем мониторинг
    Thread(target=monitor, daemon=True).start()
    
    # 3. Запускаем Polling (ОСНОВНОЙ ПРОЦЕСС)
    print("Удаляем старые вебхуки...")
    bot.remove_webhook()
    time.sleep(1)
    print("Запуск Polling...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
