import os
import asyncio
import openpyxl
from telegram import Bot
from telegram.constants import ParseMode
from flask import Flask
import threading
from datetime import datetime
import re
import logging

# ========= НАСТРОЙКА ЛОГОВ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
TOKEN = "8708654790:AAEG-HQcgYgLykvceLpGJUiQFLOuS3d8c2k"
CHANNEL = "@Netizenshop"
FILE = "products.xlsx"

# Обычные эмодзи (запасной вариант)
DEFAULT_EMOJI = {
    'update': '📌',
    'check': '✅',
    'battery': '🔋',
    'storage': '📱',
    'cross': '❌',
    'truck': '🚚',
    'phone': '📞',
    'dot': '•'
}

def clean_emoji_id(emoji_id):
    """Очищает ID эмодзи от лишних символов"""
    if not emoji_id:
        return None
    
    emoji_id = str(emoji_id).strip()
    
    # Если это уже HTML тег, вытаскиваем ID
    if 'emoji-id="' in emoji_id:
        match = re.search(r'emoji-id="(\d+)"', emoji_id)
        if match:
            return match.group(1)
    
    # Убираем скобки, кавычки и прочее
    emoji_id = emoji_id.strip('[]{}()"\'').strip()
    
    # Проверяем, что остались только цифры
    if emoji_id.isdigit():
        return emoji_id
    
    return None

def get_premium_emoji(emoji_id, default_emoji):
    """
    Возвращает премиум-эмодзи в правильном формате:
    <tg-emoji emoji-id="ID">ОБЫЧНЫЙ_ЭМОДЗИ</tg-emoji>
    """
    clean_id = clean_emoji_id(emoji_id)
    if clean_id:
        return f'<tg-emoji emoji-id="{clean_id}">{default_emoji}</tg-emoji>'
    return default_emoji

def format_price_list(products, global_emoji_ids):
    """Форматирует прайс-лист с премиум-эмодзи"""
    lines = []
    
    # Заголовок с датой
    today = datetime.now().strftime("%d.%m.%Y")
    lines.append(f"{today}")
    lines.append("")
    
    # Обновление цен
    update_emoji = get_premium_emoji(global_emoji_ids.get('update'), DEFAULT_EMOJI['update'])
    lines.append(f"{update_emoji} последнее обновление цен")
    lines.append("")
    
    # Гарантия
    check_emoji = get_premium_emoji(global_emoji_ids.get('check'), DEFAULT_EMOJI['check'])
    lines.append(f"{check_emoji} Гарантия 14 дней со дня покупки.")
    lines.append("Дополнительная гарантия:")
    lines.append("+3 месяца - 2.500₽")
    lines.append("+6 месяцев - 4.000₽")
    lines.append("+12 месяцев - 6.000₽")
    lines.append("")
    
    # Блоки зарядки
    battery_emoji = get_premium_emoji(global_emoji_ids.get('battery'), DEFAULT_EMOJI['battery'])
    lines.append(f"{battery_emoji} Блоки зарядки:")
    lines.append("20w - 2.490₽")
    lines.append("40/60w - 3.990₽")
    lines.append("")
    
    # Группировка товаров
    grouped = {}
    for p in products:
        model = p.get('model', 'iPhone 17')
        storage = p.get('storage', '256GB')
        sim_type = p.get('type', 'eSIM')
        color = p.get('color', '')
        price = p.get('price')
        emoji_id = p.get('emoji_id')
        
        key = (model, storage, sim_type)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append((color, price, emoji_id))
    
    model_order = ["iPhone 17", "iPhone 17 Air"]
    
    storage_emoji = get_premium_emoji(global_emoji_ids.get('storage'), DEFAULT_EMOJI['storage'])
    cross_emoji = get_premium_emoji(global_emoji_ids.get('cross'), DEFAULT_EMOJI['cross'])
    
    for model in model_order:
        if model not in [k[0] for k in grouped.keys()]:
            continue
        
        model_items = {k: v for k, v in grouped.items() if k[0] == model}
        
        for (_, storage, sim_type), items in sorted(model_items.items(), key=lambda x: int(x[0][1].replace('GB', ''))):
            type_label = "eSIM" if sim_type == "eSIM" else "SIM + eSIM"
            
            # ЗАГОЛОВОК МОДЕЛИ С ПРЕМИУМ-ЭМОДЗИ
            lines.append(f"{storage_emoji} {model} — {storage} ({type_label})")
            
            for color, price, emoji_id in sorted(items, key=lambda x: x[0]):
                # ЦВЕТ С ПРЕМИУМ-ЭМОДЗИ
                color_emoji = get_premium_emoji(emoji_id, DEFAULT_EMOJI['dot'])
                
                if price and price > 0:
                    price_str = f"{int(price):,}₽".replace(',', '.')
                    lines.append(f"  {color_emoji} {color} — {price_str}")
                else:
                    lines.append(f"  {color_emoji} {color} — {cross_emoji}")
            lines.append("")
    
    # Футер
    truck_emoji = get_premium_emoji(global_emoji_ids.get('truck'), DEFAULT_EMOJI['truck'])
    phone_emoji = get_premium_emoji(global_emoji_ids.get('phone'), DEFAULT_EMOJI['phone'])
    
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append(f"{truck_emoji} Доставка по РФ")
    lines.append(f"{phone_emoji} Для заказа: @netizenstaff")
    lines.append("")
    lines.append("eSIM - только виртуальные (нет физического слота под сим)")
    lines.append("SIM+eSIM - одна физическая сим карта + виртуальные")
    
    return "\n".join(lines)

def read_products_from_excel():
    """Читает товары из Excel (6 колонок)"""
    try:
        wb = openpyxl.load_workbook(FILE)
        sheet = wb.active
        
        products = []
        global_emoji_ids = {}
        
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or len(row) < 4:
                continue
                
            model = row[0] if len(row) > 0 else None
            storage = row[1] if len(row) > 1 else None
            sim_type = row[2] if len(row) > 2 else None
            color = row[3] if len(row) > 3 else None
            price = row[4] if len(row) > 4 else None
            emoji_id = row[5] if len(row) > 5 else None
            
            if not model or not storage or not sim_type or not color:
                continue
            
            # Глобальные настройки
            if str(model).upper().startswith("GLOBAL_"):
                key = str(model).replace("GLOBAL_", "").lower()
                global_emoji_ids[key] = emoji_id
                print(f"🌍 Глобальный эмодзи: {key} = {emoji_id}")
                continue
            
            # Преобразуем цену
            if price is None or (isinstance(price, str) and price.strip() == ""):
                price = None
            else:
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    price = None
            
            product = {
                'model': str(model).strip(),
                'storage': str(storage).strip(),
                'type': str(sim_type).strip(),
                'color': str(color).strip(),
                'price': price,
                'emoji_id': emoji_id if emoji_id else None
            }
            products.append(product)
        
        wb.close()
        print(f"📖 Прочитано товаров: {len(products)}")
        print(f"🌍 Глобальных настроек: {len(global_emoji_ids)}")
        return products, global_emoji_ids
        
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return [], {}

async def send_price_list():
    """Отправляет прайс-лист в канал"""
    print("🚀 Отправка прайс-листа...")
    
    bot = Bot(token=TOKEN)
    
    try:
        me = await bot.get_me()
        print(f"✅ Бот: @{me.username}")
        
        if not os.path.exists(FILE):
            print(f"❌ Файл {FILE} не найден!")
            return False
        
        products, global_emoji_ids = read_products_from_excel()
        
        if not products:
            print("⚠️ Нет товаров в Excel!")
            return False
        
        post_text = format_price_list(products, global_emoji_ids)
        print(f"📝 Длина сообщения: {len(post_text)} символов")
        
        # Показываем первые 200 символов для проверки эмодзи
        print(f"📝 Начало сообщения: {post_text[:200]}...")
        
        msg = await bot.send_message(
            chat_id=CHANNEL,
            text=post_text,
            parse_mode=ParseMode.HTML
        )
        
        print(f"✅✅✅ ПРАЙС-ЛИСТ ОТПРАВЛЕН!")
        print(f"🔗 https://t.me/{CHANNEL[1:]}/{msg.message_id}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    print("=" * 50)
    print("🚀 БОТ ЗАПУЩЕН")
    print("=" * 50)
    
    await send_price_list()
    
    while True:
        print("⏳ Жду 60 секунд...")
        await asyncio.sleep(60)
        await send_price_list()

if __name__ == "__main__":
    print("🔄 Запуск бота...")
    asyncio.run(main())
