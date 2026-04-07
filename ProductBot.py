import time
import openpyxl
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError
import os
import asyncio
import json
from flask import Flask
import threading

# ========= ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот для цен iPhone работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

threading.Thread(target=run_web, daemon=True).start()
print("✅ Веб-сервер запущен на порту 8080")
# ==========================================

# ========= НАСТРОЙКИ БОТА ==========
TELEGRAM_TOKEN = "It's Private :)"  # ← ЗАМЕНИ НА СВОЙ ТОКЕН!
CHANNEL_ID = '@Netizenshop'
EXCEL_FILE = 'products.xlsx'
MESSAGE_IDS_FILE = 'message_ids.json'

def load_message_ids():
    """Загружает словарь с ID отправленных сообщений"""
    if os.path.exists(MESSAGE_IDS_FILE):
        with open(MESSAGE_IDS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_message_ids(message_ids):
    """Сохраняет словарь с ID отправленных сообщений"""
    with open(MESSAGE_IDS_FILE, 'w') as f:
        json.dump(message_ids, f)

async def send_or_edit_product(bot, product_code, product_name, price, image_url, message_id):
    """Отправляет новый пост или редактирует существующий"""
    caption = f"{product_name}\n💰 Цена: {price}₽"
    
    try:
        if image_url and image_url.strip():
            if message_id:
                await bot.edit_message_media(
                    chat_id=CHANNEL_ID,
                    message_id=message_id,
                    media=InputMediaPhoto(media=image_url, caption=caption)
                )
            else:
                msg = await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image_url,
                    caption=caption
                )
                return msg.message_id
        else:
            if message_id:
                await bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=message_id,
                    text=caption
                )
            else:
                msg = await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=caption
                )
                return msg.message_id
    except TelegramError as e:
        print(f"Ошибка: {e}")
    return None

async def main():
    print("🚀 Бот запускается...")
    bot = Bot(token=TELEGRAM_TOKEN)
    message_ids = load_message_ids()
    
    while True:
        try:
            if not os.path.exists(EXCEL_FILE):
                print(f"❌ Файл {EXCEL_FILE} не найден!")
                await asyncio.sleep(60)
                continue
            
            wb = openpyxl.load_workbook(EXCEL_FILE)
            sheet = wb.active
            
            for row in sheet.iter_rows(min_row=2, values_only=False):
                product_code = row[0].value
                product_name = row[1].value
                price = row[2].value
                image_url = row[3].value if len(row) > 3 else None
                
                if not product_code or not product_name or not price:
                    continue
                
                existing_message_id = message_ids.get(str(product_code))
                
                if existing_message_id:
                    print(f"🔄 Обновляем: {product_name}")
                else:
                    print(f"📤 Отправляем новый: {product_name}")
                
                new_id = await send_or_edit_product(
                    bot, str(product_code), product_name, price, image_url, existing_message_id
                )
                
                if new_id:
                    message_ids[str(product_code)] = new_id
            
            save_message_ids(message_ids)
            wb.close()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
