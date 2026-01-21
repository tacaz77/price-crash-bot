import telebot
import requests
import time
from threading import Thread
from flask import Flask

# --- НАСТРОЙКИ ---
TOKEN = '8224578094:AAEOwXsE2aJly_LoMbS-5ud6FgT-O2rh3r8' 
CHANNEL_ID = '@pricecrashpro'
# -----------------

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Price Crash System: Online 24/7"

def run_web_server():
    app.run(host='0.0.0.0', port=10000)

posted_ids = set()

# --- 1. ГЕЙМЕРСКАЯ ХАЛЯВА ---
def get_games():
    try:
        url = "https://www.gamerpower.com/api/giveaways"
        res = requests.get(url, timeout=10)
        return res.json()[0] if res.status_code == 200 else None
    except: return None

# --- 2. WILDBERRIES (ОШИБКИ ЦЕН) ---
def get_wb_errors():
    try:
        url = "https://catalog.wb.ru/catalog/electronic/v4/filters?appType=1&curr=rub&dest=-1257786&subject=7000"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            products = res.json().get('data', {}).get('products', [])
            for item in products:
                if item.get('sale', 0) >= 90: # Скидка от 90%
                    return {
                        'id': f"wb_{item['id']}",
                        'title': f"WB: {item['brand']} {item['name']}",
                        'old': f"{item['priceU']/100} ₽",
                        'new': f"{item['salePriceU']/100} ₽",
                        'link': f"https://www.wildberries.ru/catalog/{item['id']}/detail.aspx",
                        'img': f"https://basket-01.wb.ru/vol{item['id']//100000}/part{item['id']//1000}/{item['id']}/images/big/1.jpg"
                    }
    except: return None

# --- 3. ALIEXPRESS (ТОВАРЫ ЗА ЦЕНТЫ) ---
def get_ali_deals():
    try:
        # Используем CheapShark как временный фильтр для Ali/Global или их открытые фиды
        url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=0.10" # Ищем товары до 10 центов
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            item = res.json()[0]
            return {
                'id': f"ali_{item['dealID']}",
                'title': f"ALIEXPRESS: {item['title']}",
                'old': f"${item['normalPrice']}",
                'new': f"${item['salePrice']}",
                'link': f"https://www.cheapshark.com/redirect?dealID={item['dealID']}",
                'img': item['thumb']
            }
    except: return None

# --- 4. М.ВИДЕО (АКЦИИ И СЛИВЫ) ---
def get_mvideo_deals():
    try:
        # Эмуляция поиска по разделу распродаж М.Видео
        # В реальном API Admitad это был бы запрос к Coupons
        return {
            'id': 'mvideo_promo_1',
            'title': "М.ВИДЕО: Ночная распродажа техники!",
            'old': "По прайсу",
            'new': "-50% по промокоду",
            'link': "https://www.mvideo.ru/promo/skidki",
            'img': "https://static.mvideo.ru/assets/img/logo.png"
        }
    except: return None

# --- ОТПРАВКА ---
def send_post(title, old_price, new_price, link, image, platform):
    caption = (
        f"🚨 **ЦЕНА РУХНУЛА!**\n\n"
        f"🔥 **{title}**\n"
        f"❌ Было: {old_price}\n"
        f"✅ **СТАЛО: {new_price}**\n\n"
        f"🏢 Площадка: {platform}\n"
        f"👇 Хватай быстрее!"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎁 КУПИТЬ / ЗАБРАТЬ", url=link))
    try: bot.send_photo(CHANNEL_ID, image, caption=caption, reply_markup=markup, parse_mode="Markdown")
    except: pass

# --- МОНИТОРИНГ ---
def monitor():
    while True:
        # Проверка всех модулей по очереди
        sources = [
            (get_games(), "Раздача"),
            (get_wb_errors(), "Wildberries"),
            (get_ali_deals(), "AliExpress"),
            (get_mvideo_deals(), "М.Видео")
        ]
        
        for deal, platform in sources:
            if deal and deal.get('id') not in posted_ids:
                posted_ids.add(deal.get('id'))
                # Унификация полей для разных API
                t = deal.get('title')
                o = deal.get('old', deal.get('worth', '???'))
                n = deal.get('new', 'БЕСПЛАТНО')
                l = deal.get('link', deal.get('open_giveaway_url'))
                i = deal.get('img', deal.get('image', deal.get('thumb')))
                
                send_post(t, o, n, l, i, platform)
                time.sleep(5) # Пауза между постами

        time.sleep(1800) # Проверка каждые 30 минут

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    Thread(target=monitor).start()
    bot.infinity_polling()
