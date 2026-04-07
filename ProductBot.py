import os
import asyncio
import openpyxl
from telegram import Bot
from flask import Flask
import threading
from datetime import datetime

# ========= ДИАГНОСТИКА ==========
print("🔍 ДИАГНОСТИКА ЗАПУЩЕНА")
print(f"📂 Текущая папка: {os.getcwd()}")
print(f"📂 Содержимое папки: {os.listdir('.')}")

FILE = "products.xlsx"

# Проверяем Excel файл
if os.path.exists(FILE):
    print(f"✅ Файл {FILE} НАЙДЕН!")
    try:
        wb = openpyxl.load_workbook(FILE)
        sheet = wb.active
        print(f"📊 Кол-во строк: {sheet.max_row}")
        print(f"📊 Кол-во колонок: {sheet.max_column}")
        
        headers = []
        for cell in sheet[1]:
            headers.append(cell.value)
        print(f"📋 Заголовки: {headers}")
        
        # Покажем первые 3 строки данных
        for i in range(2, min(5, sheet.max_row + 1)):
            row_data = []
            for cell in sheet[i]:
                row_data.append(cell.value)
            print(f"📋 Строка {i-1}: {row_data}")
        
        wb.close()
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
else:
    print(f"❌ ФАЙЛ {FILE} НЕ НАЙДЕН!")
# =================================

# ========= ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

threading.Thread(target=run_web, daemon=True).start()
print("✅ Веб-сервер запущен")
# ===============================

# ========= НАСТРОЙКИ ==========
TOKEN = "8103497827:AAF4FrhXgx4PTpuLbK6dY-tALg7Iu6UWhkE"
CHANNEL = "@Netizenshop"

# ========= ПРОСТОЕ ФОРМАТИРОВАНИЕ ==========
def format_simple_price_list(products):
    """Простое форматирование для теста"""
    lines = []
    today = datetime.now().strftime("%d.%m.%Y")
    lines.append(f"📱 ПРАЙС-ЛИСТ от {today}")
    lines.append("=" * 30)
    
    for p in products:
        model = p.get('model', 'iPhone')
        storage = p.get('storage', '128GB')
        sim_type = "eSIM" if p.get('type') == "eSIM" else "SIM+eSIM"
        color = p.get('color', '')
        price = p.get('price')
        
        price_str = f"{int(price):,}₽".replace(',', '.') if price and price > 0 else "Нет в наличии"
        lines.append(f"{model} {storage} ({sim_type})")
        lines.append(f"  {color} — {price_str}")
        lines.append("")
    
    return "\n".join(lines)

def read_products_from_excel():
    """Читает товары из Excel"""
    print("📖 Читаю Excel...")
    wb = openpyxl.load_workbook(FILE)
    sheet = wb.active
    
    products = []
    for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        model = row[0] if len(row) > 0 else None
        storage = row[1] if len(row) > 1 else None
        sim_type = row[2] if len(row) > 2 else None
        color = row[3] if len(row) > 3 else None
        price = row[4] if len(row) > 4 else None
        
        if not model or not storage or not sim_type or not color:
            print(f"⚠️ Строка {row_num}: пропущена (не все поля заполнены)")
            continue
        
        # Преобразуем цену
        if price is None or (isinstance(price, str) and price.strip() == ""):
            price = None
        else:
            try:
                price = float(price)
            except:
                price = None
        
        product = {
            'model': str(model).strip(),
            'storage': str(storage).strip(),
            'type': str(sim_type).strip(),
            'color': str(color).strip(),
            'price': price
        }
        products.append(product)
        print(f"✅ Строка {row_num}: {product}")
    
    wb.close()
    print(f"📦 Итого товаров: {len(products)}")
    return products

async def send_test_message():
    """Отправляет тестовое сообщение"""
    print("🚀 Пытаюсь отправить сообщение...")
    
    bot = Bot(token=TOKEN)
    
    # Проверяем бота
    try:
        bot_info = await bot.get_me()
        print(f"✅ Бот найден: @{bot_info.username}")
    except Exception as e:
        print(f"❌ Ошибка подключения к боту: {e}")
        return
    
    # Проверяем доступ к каналу
    try:
        chat = await bot.get_chat(CHANNEL)
        print(f"✅ Канал найден: {chat.title}")
        print(f"📊 Тип чата: {chat.type}")
    except Exception as e:
        print(f"❌ Ошибка доступа к каналу: {e}")
        print("⚠️ Проверь, что бот добавлен в админы канала!")
        return
    
    # Проверяем файл
    if not os.path.exists(FILE):
        print(f"❌ Файл {FILE} не найден!")
        return
    
    # Читаем товары
    products = read_products_from_excel()
    if not products:
        print("❌ Нет товаров в Excel!")
        return
    
    # Формируем текст
    post_text = format_simple_price_list(products)
    print("📝 Текст сообщения:")
    print(post_text)
    print("-" * 50)
    
    # Отправляем
    try:
        msg = await bot.send_message(
            chat_id=CHANNEL,
            text=post_text
        )
        print(f"✅✅✅ СООБЩЕНИЕ ОТПРАВЛЕНО! ID: {msg.message_id}")
        print(f"🔗 Ссылка: https://t.me/{CHANNEL[1:]}/{msg.message_id}")
    except Exception as e:
        print(f"❌❌❌ ОШИБКА ОТПРАВКИ: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Полное сообщение: {e}")

def run_bot():
    """Запускает бота"""
    print("🤖 Запускаем бота...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_test_message())

# ========= ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК БОТА")
    print("=" * 50)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    print("✅ Бот запущен, ждём отправки...")
    
    # Держим приложение живым
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("Остановка...")
