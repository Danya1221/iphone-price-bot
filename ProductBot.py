import os
import asyncio
import openpyxl
from telegram import Bot
from flask import Flask
import threading
import sys

print("1. Начало загрузки скрипта")

# ========= ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    print("3. Запуск веб-сервера...")
    app.run(host='0.0.0.0', port=8080)

print("2. Создаю поток для веб-сервера")
threading.Thread(target=run_web, daemon=True).start()
print("✅ Веб-сервер запущен")
# ===============================

# ========= НАСТРОЙКИ ==========
TOKEN = "8103497827:AAF4FrhXgx4PTpuLbK6dY-tALg7Iu6UWhkE"
CHANNEL = "@Netizenshop"
FILE = "products.xlsx"

print(f"4. Бот запускается с токеном: {TOKEN[:10]}...")
print(f"5. Канал: {CHANNEL}")
print(f"6. Файл Excel: {FILE}")
print(f"7. Файлы в папке: {os.listdir('.')}")
print("8. Проверяю наличие Excel...")

if not os.path.exists(FILE):
    print(f"❌ Файл {FILE} не найден!")
    sys.exit(1)

print("9. Excel найден, загружаю...")

try:
    wb = openpyxl.load_workbook(FILE)
    sheet = wb.active
    print("10. Excel загружен успешно")
except Exception as e:
    print(f"❌ Ошибка загрузки Excel: {e}")
    sys.exit(1)

print("11. Создаю бота...")

async def main():
    print("12. Вход в main()")
    bot = Bot(token=TOKEN)
    print("13. Бот создан, вхожу в бесконечный цикл")
    
    while True:
        try:
            print("14. Проверяю Excel...")
            wb = openpyxl.load_workbook(FILE)
            sheet = wb.active
            
            row_num = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):
                code = row[0]
                name = row[1]
                price = row[2]
                
                if not code or not name or not price:
                    continue
                
                row_num += 1
                text = f"{name}\n💰 {price}₽"
                print(f"15. Отправляю товар #{row_num}: {name}")
                
                try:
                    await bot.send_message(chat_id=CHANNEL, text=text)
                    print(f"    ✅ Отправлено")
                except Exception as e:
                    print(f"    ❌ Ошибка: {e}")
                
                await asyncio.sleep(2)
            
            print(f"16. Обработано {row_num} товаров")
            wb.close()
            
        except Exception as e:
            print(f"❌ Ошибка в цикле: {e}")
        
        print("17. Жду 60 секунд...")
        await asyncio.sleep(60)

print("18. Запускаю main()")
asyncio.run(main())
