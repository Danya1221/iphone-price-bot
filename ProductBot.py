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

print(f"Бот запускается с токеном: {TOKEN[:10]}...")
print(f"Канал: {CHANNEL}")
print(f"Файл Excel: {FILE}")
print(f"Файлы в папке: {os.listdir('.')}")

async def main():
    bot = Bot(token=TOKEN)
    
    while True:
        try:
            print("Проверяю Excel...")
            
            if not os.path.exists(FILE):
                print(f"❌ Файл {FILE} не найден!")
                await asyncio.sleep(30)
                continue
            
            wb = openpyxl.load_workbook(FILE)
            sheet = wb.active
            
            for row in sheet.iter_rows(min_row=2, values_only=True):
                code = row[0]
                name = row[1]
                price = row[2]
                
                if not code or not name or not price:
                    continue
                
                text = f"{name}\n💰 {price}₽"
                print(f"Отправляю: {name}")
                
                try:
                    await bot.send_message(chat_id=CHANNEL, text=text)
                except Exception as e:
                    print(f"Ошибка: {e}")
                
                await asyncio.sleep(2)  # пауза между сообщениями
            
            wb.close()
            
        except Exception as e:
            print(f"Ошибка: {e}")
        
        await asyncio.sleep(60)  # пауза 1 минута

if __name__ == "__main__":
    asyncio.run(main())
