import os
import asyncio
from telegram import Bot
from flask import Flask
import threading

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

async def send_test():
    """Отправляет тестовое сообщение"""
    print("🚀 Отправляю тестовое сообщение...")
    
    bot = Bot(token=TOKEN)
    
    try:
        # Проверяем бота
        me = await bot.get_me()
        print(f"✅ Бот: @{me.username}")
        
        # Отправляем простое сообщение
        msg = await bot.send_message(
            chat_id=CHANNEL,
            text="✅ Бот работает! Тестовое сообщение."
        )
        print(f"✅✅✅ СООБЩЕНИЕ ОТПРАВЛЕНО! ID: {msg.message_id}")
        print(f"🔗 https://t.me/Netizenshop/{msg.message_id}")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print(f"\n⚠️ ПРОВЕРЬ:")
        print(f"1. Бот добавлен в админы канала {CHANNEL}")
        print(f"2. Токен правильный")
        print(f"3. Канал существует")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_test())

# ========= ЗАПУСК ==========
if __name__ == "__main__":
    print("ЗАПУСК ТЕСТА")
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    
    # Держим процесс
    import time
    while True:
        time.sleep(1)
