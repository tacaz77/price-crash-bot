import telebot
import requests
import time
from threading import Thread
from flask import Flask

# --- НАСТРОЙКИ (ЗАПОЛНИ СВОИМИ ДАННЫМИ) ---
TOKEN = '8224578094:AAEOwXsE2aJly_LoMbS-5ud6FgT-O2rh3r8' 
CHANNEL_ID = '@pricecrashpro_bot'
# ------------------------------------------

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Бот активен и работает 24/7!"

def run_web_server():
    # Порт 10000 для Render
    app.run(host='0.0.0.0', port=10000)

posted_ids = set()

# --- ФУНКЦИИ ПОИСКА ---
def get_games():
    try:
        url = "https://www.gamerpower.com/api/giveaways"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()[0]
    except: return None

def get_products():
    try:
        url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()[0]
    except: return None

def get_wb_errors():
    try:
        # Subject 7000 - Электроника
        url = "https://catalog.wb.ru/catalog/electronic/v4/filters?appType=1&curr=rub&dest=-1257786&subject=7000"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            products = response.json().get('data', {}).get('products', [])
            for item in products:
                discount = item.get('sale', 0)
                if discount >= 90:
                    return {
                        'id': f"wb_{item.get('id')}",
                        'title': f"{item.get('brand')} {item.get('name')}",
                        'old_price': f"{item.get('priceU', 0)/100} ₽",
                        'new_price': f"{item.get('salePriceU', 0)/100} ₽",
                        'link': f"https://www.wildberries.ru/catalog/{item.get('id')}/detail.aspx",
                        'image': f"https://basket-01.wb.ru/vol{item.get('id')//100000}/part{item.get('id')//1000}/{item.get('id')}/images/big/1.jpg",
                        'platform': 'Wildberries'
                    }
    except: return None

# --- КОМАНДЫ БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_chan = telebot.types.InlineKeyboardButton("📢 Перейти в канал", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")
    btn_ref = telebot.types.InlineKeyboardButton("🎁 Моя реф-ссылка", callback_data="get_ref")
    markup.add(btn_chan, btn_ref)
    bot.send_message(message.chat.id, "📉 **Price Crash Bot запущен!**\nЯ ищу ошибки цен и халяву 24/7.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_ref":
        ref_link = f"https://t.me/{bot.get_me().username}?start={call.message.chat.id}"
        bot.send_message(call.message.chat.id, f"🔗 **Твоя ссылка:**\n`{ref_link}`", parse_mode="Markdown")

# --- ОТПРАВКА В КАНАЛ ---
def send_post(title, old_price, new_price, link, image, platform):
    caption = (
        f"💳 **PRICE CRASH: НАЙДЕНА ВЫГОДА**\n\n"
        f"🔥 **{title}**\n"
        f"❌ Было: {old_price}\n"
        f"✅ **СТАЛО: {new_price}**\n\n"
        f"🏢 Площадка: {platform}"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎁 ЗАБРАТЬ", url=link))
    share_url = f"https://t.me/share/url?url=https://t.me/{CHANNEL_ID.replace('@','')}&text=Тут цена рухнула!"
    markup.add(telebot.types.InlineKeyboardButton("📢 ПЕРЕСЛАТЬ ДРУГУ", url=share_url))
    try: bot.send_photo(CHANNEL_ID, image, caption=caption, reply_markup=markup, parse_mode="Markdown")
    except: print("Ошибка отправки поста")

# --- ЦИКЛ МОНИТОРИНГА ---
def monitor():
    while True:
        try:
            # 1. Проверка Игр
            game = get_games()
            if game and game['id'] not in posted_ids:
                posted_ids.add(game['id'])
                send_post(game['title'], game['worth'], "БЕСПЛАТНО", game['open_giveaway_url'], game['image'], game['platforms'])
            
            # 2. Проверка WB
            wb = get_wb_errors()
            if wb and wb['id'] not in posted_ids:
                posted_ids.add(wb['id'])
                send_post(wb['title'], wb['old_price'], wb['new_price'], wb['link'], wb['image'], wb['platform'])
                
            # 3. Проверка Товаров
            prod = get_products()
            if prod and prod['dealID'] not in posted_ids:
                posted_ids.add(prod['dealID'])
                send_post(prod['title'], f"${prod['normalPrice']}", f"${prod['salePrice']}", f"https://www.cheapshark.com/redirect?dealID={prod['dealID']}", prod['thumb'], "Global Store")
        except Exception as e:
            print(f"Ошибка в мониторинге: {e}")
        
        time.sleep(1800) # Раз в 30 минут

if __name__ == "__main__":
    Thread(target=run_web_server).start() # Поток для веб-сервера
    Thread(target=monitor).start()         # Поток для поиска цен
    bot.infinity_polling()                # Основной поток бота
