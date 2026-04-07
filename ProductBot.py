import os
import asyncio
import openpyxl
from telegram import Bot
from flask import Flask
import threading

# ========= ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_web, daemon=True).start()
print("✅ Веб-сервер запущен")
# ===============================

# ========= НАСТРОЙКИ ==========
TOKEN = "8103497827:AAF4FrhXgx4PTpuLbK6dY-tALg7Iu6UWhkE"  # ← ТВОЙ ТОКЕН
CHANNEL = "@Netizenshop"
FILE = "products.xlsx"
MESSAGE_ID_FILE = "post_message_id.txt"  # Файл для хранения ID одного поста

def format_price_list(products):
    """
    products: список словарей с ключами: storage, color, type, price
    Возвращает отформатированный текст для поста
    """
    # Группируем по объёму памяти
    by_storage = {}
    for p in products:
        storage = p['storage']
        if storage not in by_storage:
            by_storage[storage] = []
        by_storage[storage].append(p)
    
    # Формируем сообщение
    lines = []
    lines.append("📱 *iPhone 17 — Цены и наличие*\n")
    
    # Эмодзи для цветов
    color_emoji = {
        'Black': '⚫️',
        'White': '⚪️',
        'Blue': '🔵',
        'Sage': '🟢',
        'Lavender': '🟣'
    }
    
    for storage in sorted(by_storage.keys(), key=int):
        lines.append(f"💾 *{storage}GB*")
        for p in by_storage[storage]:
            emoji = color_emoji.get(p['color'], '🔘')
            lines.append(f"  {emoji} {p['color']} ({p['type']}) — {int(p['price']):,}₽")
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("✅ Гарантия 14 дней")
    lines.append("🚚 Доставка по РФ")
    lines.append("📞 Для заказа: @manager")
    
    return "\n".join(lines)

def load_post_message_id():
    """Загружает ID последнего отправленного поста"""
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, 'r') as f:
            return int(f.read().strip())
    return None

def save_post_message_id(message_id):
    """Сохраняет ID поста"""
    with open(MESSAGE_ID_FILE, 'w') as f:
        f.write(str(message_id))

def read_products_from_excel():
    """Читает товары из Excel и возвращает список словарей"""
    wb = openpyxl.load_workbook(FILE)
    sheet = wb.active
    
    products = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        code = row[0]
        name = row[1]
        price = row[2]
        
        if not code or not name or not price:
            continue
        
        # Парсим название: "iPhone 17 256GB Black (eSim)"
        # Извлекаем объём, цвет и тип
        parts = name.split()
        storage = None
        color = None
        sim_type = "eSim"
        
        for part in parts:
            if "GB" in part:
                storage = part.replace("GB", "")
            if part in ['Black', 'White', 'Blue', 'Sage', 'Lavender']:
                color = part
        
        if not storage or not color:
            # Если не распарсилось, используем заглушки
            storage = "256"
            color = "Unknown"
        
        products.append({
            'code': code,
            'storage': storage,
            'color': color,
            'type': sim_type,
            'price': price,
            'full_name': name
        })
    
    wb.close()
    return products

async def main():
    print("🚀 Бот запускается...")
    bot = Bot(token=TOKEN)
    
    # Загружаем ID существующего поста (если есть)
    post_message_id = load_post_message_id()
    if post_message_id:
        print(f"📝 Найден существующий пост с ID: {post_message_id}")
    else:
        print("📝 Создаём новый пост")
    
    while True:
        try:
            print("🔄 Проверяю Excel...")
            
            if not os.path.exists(FILE):
                print(f"❌ Файл {FILE} не найден!")
                await asyncio.sleep(60)
                continue
            
            # Читаем товары из Excel
            products = read_products_from_excel()
            print(f"📦 Найдено товаров: {len(products)}")
            
            if not products:
                print("⚠️ Нет товаров в Excel")
                await asyncio.sleep(60)
                continue
            
            # Форматируем пост
            post_text = format_price_list(products)
            
            # Отправляем или редактируем
            try:
                if post_message_id:
                    # Редактируем существующий пост
                    await bot.edit_message_text(
                        chat_id=CHANNEL,
                        message_id=post_message_id,
                        text=post_text,
                        parse_mode="Markdown"
                    )
                    print("✅ Пост обновлён")
                else:
                    # Отправляем новый пост
                    msg = await bot.send_message(
                        chat_id=CHANNEL,
                        text=post_text,
                        parse_mode="Markdown"
                    )
                    post_message_id = msg.message_id
                    save_post_message_id(post_message_id)
                    print(f"✅ Новый пост отправлен (ID: {post_message_id})")
                    
            except Exception as e:
                print(f"❌ Ошибка при отправке/редактировании: {e}")
                # Если пост не найден (удалили вручную), сбрасываем ID
                if "message to edit not found" in str(e).lower():
                    post_message_id = None
                    save_post_message_id(None)
            
        except Exception as e:
            print(f"❌ Ошибка в цикле: {e}")
        
        print("⏳ Жду 60 секунд...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
