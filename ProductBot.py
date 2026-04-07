import os
import asyncio
import openpyxl
from telegram import Bot
from flask import Flask
import threading
from datetime import datetime

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
TOKEN = "8103497827:AAF4FrhXgx4PTpuLbK6dY-tALg7Iu6UWhkE"
CHANNEL = "@Netizenshop"
FILE = "products.xlsx"
MESSAGE_ID_FILE = "post_message_id.txt"

# Эмодзи для оформления
EMOJI = {
    'update': '📌',
    'check': '✅',
    'battery': '🔋',
    'storage': '💾',
    'cross': '❌',
    'truck': '🚚',
    'phone': '📞',
    'dot': '•'
}

def format_price_list(products):
    """
    Форматирует прайс-лист
    products: список товаров с полями model, storage, type, color, price
    """
    lines = []
    
    # Заголовок с датой
    today = datetime.now().strftime("%d.%m.%Y")
    lines.append(f"{today}")
    lines.append(f"{EMOJI['update']} последнее обновление цен")
    lines.append("")
    
    # Гарантия
    lines.append(f"{EMOJI['check']} Гарантия 14 дней со дня покупки.")
    lines.append("Дополнительная гарантия:")
    lines.append("+3 месяца - 2.500₽")
    lines.append("+6 месяцев - 4.000₽")
    lines.append("+12 месяцев - 6.000₽")
    lines.append("")
    
    # Блоки зарядки
    lines.append(f"{EMOJI['battery']} Блоки зарядки:")
    lines.append("20w - 2.490₽")
    lines.append("40/60w - 3.990₽")
    lines.append("")
    
    # Группируем товары
    grouped = {}
    for p in products:
        model = p.get('model', 'iPhone 17')
        storage = p.get('storage', '256GB')
        sim_type = p.get('type', 'eSIM')
        color = p.get('color', '')
        price = p.get('price')
        
        key = (model, storage, sim_type)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append((color, price))
    
    # Сортируем модели
    model_order = ["iPhone 17", "iPhone 17 Air"]
    
    for model in model_order:
        if model not in [k[0] for k in grouped.keys()]:
            continue
        
        model_items = {k: v for k, v in grouped.items() if k[0] == model}
        
        for (_, storage, sim_type), items in sorted(model_items.items(), key=lambda x: int(x[0][1].replace('GB', ''))):
            type_label = "eSIM" if sim_type == "eSIM" else "SIM + eSIM"
            lines.append(f"{EMOJI['storage']} {model} — {storage} ({type_label})")
            
            for color, price in sorted(items, key=lambda x: x[0]):
                if price and price > 0:
                    price_str = f"{int(price):,}₽".replace(',', '.')
                    lines.append(f"  {EMOJI['dot']} {color} — {price_str}")
                else:
                    lines.append(f"  {EMOJI['dot']} {color} — {EMOJI['cross']}")
            lines.append("")
    
    # Футер
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append(f"{EMOJI['truck']} Доставка по РФ")
    lines.append(f"{EMOJI['phone']} Для заказа: @manager")
    lines.append("")
    lines.append("eSIM - только виртуальные (нет физического слота под сим)")
    lines.append("SIM+eSIM - одна физическая сим карта + виртуальные")
    
    return "\n".join(lines)

def load_post_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, 'r') as f:
            return int(f.read().strip())
    return None

def save_post_message_id(message_id):
    if message_id:
        with open(MESSAGE_ID_FILE, 'w') as f:
            f.write(str(message_id))
    elif os.path.exists(MESSAGE_ID_FILE):
        os.remove(MESSAGE_ID_FILE)

def read_products_from_excel():
    """Читает товары из Excel (5 колонок: Model, Storage, Type, Color, Price)"""
    wb = openpyxl.load_workbook(FILE)
    sheet = wb.active
    
    products = []
    
    for row in sheet.iter_rows(min_row=2, values_only=True):
        model = row[0] if len(row) > 0 else None
        storage = row[1] if len(row) > 1 else None
        sim_type = row[2] if len(row) > 2 else None
        color = row[3] if len(row) > 3 else None
        price = row[4] if len(row) > 4 else None
        
        if not model or not storage or not sim_type or not color:
            continue
        
        # Преобразуем цену
        if price is None or (isinstance(price, str) and price.strip() == ""):
            price = None
        else:
            try:
                price = float(price)
            except:
                price = None
        
        products.append({
            'model': str(model).strip(),
            'storage': str(storage).strip(),
            'type': str(sim_type).strip(),
            'color': str(color).strip(),
            'price': price
        })
    
    wb.close()
    return products

async def main():
    print("🚀 Бот запускается...")
    bot = Bot(token=TOKEN)
    
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
                print(f"📂 Текущая директория: {os.getcwd()}")
                print(f"📂 Файлы в директории: {os.listdir('.')}")
                await asyncio.sleep(60)
                continue
            
            products = read_products_from_excel()
            print(f"📦 Найдено товаров: {len(products)}")
            
            if not products:
                print("⚠️ Нет товаров в Excel")
                await asyncio.sleep(60)
                continue
            
            post_text = format_price_list(products)
            
            # Выводим в консоль для отладки
            print("📝 Текст поста:")
            print(post_text)
            print("---")
            
            try:
                if post_message_id:
                    await bot.edit_message_text(
                        chat_id=CHANNEL,
                        message_id=post_message_id,
                        text=post_text
                    )
                    print("✅ Пост обновлён")
                else:
                    msg = await bot.send_message(
                        chat_id=CHANNEL,
                        text=post_text
                    )
                    post_message_id = msg.message_id
                    save_post_message_id(post_message_id)
                    print(f"✅ Новый пост отправлен (ID: {post_message_id})")
                    
            except Exception as e:
                print(f"❌ Ошибка при отправке: {e}")
                if "message to edit not found" in str(e).lower():
                    post_message_id = None
                    save_post_message_id(None)
            
        except Exception as e:
            print(f"❌ Ошибка в цикле: {e}")
        
        print("⏳ Жду 60 секунд...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
