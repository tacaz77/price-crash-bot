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

# threaded=False критически важен для предотвращения Conflict 409 на Render
bot = telebot.TeleBot(TOKEN, threaded=False) 
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

posted_ids = set()

# --- ПАРСЕР WILDBERRIES ---
def get_wb_errors():
    try:
        # Subject 7000 — электроника. Можно менять на другие категории.
        url = "https://catalog.wb.ru/catalog/electronic/v4/filters?appType=1&curr=rub&dest=-1257786&subject=7000"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            products = res.json().get('data', {}).get('products', [])
            for item in products:
                # Временно поставил 10% для теста, потом верни на 90
                if item.get('sale', 0) >= 10: 
                    return {
                        'id': f"wb_{item['id']}",
                        'title': f"WB: {item['brand']} {item['name']}",
                        'old': f"{item['priceU']/100} ₽",
                        'new': f"{item['salePriceU']/100} ₽",
                        'link': f"https://www.wildberries.ru/catalog/{item['id']}/detail.aspx",
                        'img': f"https://basket-01.wb.ru/vol{item['id']//100000}/part{item['id']//1000}/{item['id']}/images/big/1.jpg"
                    }
    except Exception as e:
        print(f"Ошибка парсера WB: {e}")
    return None

# --- ОТПРАВКА В КАНАЛ ---
def send_post(deal, platform):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎁 КУПИТЬ / ЗАБРАТЬ", url=deal['link']))
    caption = (
        f"🚨 **ЦЕНА РУХНУЛА!**\n\n"
        f"🔥 **{deal['title']}**\n"
        f"❌ Было: {deal['old']}\n"
        f"✅ **СТАЛО: {deal['new']}**\n\n"
        f"🏢 Площадка: {platform}\n"
        f"👇 Хватай быстрее!"
    )
    try:
        bot.send_photo(CHANNEL_ID, deal['img'], caption=caption, reply_markup=markup, parse_mode="Markdown")
        print(f"Пост {deal['id']} отправлен!")
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")

# --- МОНИТОРИНГ ---
def monitor():
    print("Поток мониторинга запущен...")
    # Тестовое сообщение при старте (удалить, когда всё заработает)
    try:
        bot.send_message(CHANNEL_ID, "🚀 Система мониторинга цен запущена и ищет скидки!")
    except:
        pass

    while True:
        deal = get_wb_errors()
        if deal and deal['id'] not in posted_ids:
            posted_ids.add(deal['id'])
            send_post(deal, "Wildberries")
        
        # Проверка раз в 10 минут (600 сек)
        time.sleep(600)

# --- ОБРАБОТКА ЛС ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    print(f"Команда /start от {message.chat.id}")
    bot.reply_to(message, "Привет! Я бот канала «Цена - Копейка». Все скидки публикуются в канале!")

@bot.message_handler(func=lambda message: True)
def all_messages(message):
    bot.reply_to(message, "Я работаю только в автоматическом режиме.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запускаем Flask для Render
    Thread(target=run_web_server, daemon=True).start()
    
    # Запускаем мониторинг скидок
    Thread(target=monitor, daemon=True).start()
    
    # Очистка и запуск Polling
    print("Удаление вебхуков и запуск...")
    bot.remove_webhook()
    time.sleep(1)
    
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"Критическая ошибка Polling: {e}")
        time.sleep(5)
