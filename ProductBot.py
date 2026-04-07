import os
import asyncio
import openpyxl
from telegram import Bot
from flask import Flask
import threading
from datetime import datetime
import traceback

# ========= ДИАГНОСТИКА ВСЕГО ==========
print("="*60)
print("ДИАГНОСТИКА ЗАПУЩЕНА")
print("="*60)

# 1. Проверяем файлы
print(f"📂 Текущая папка: {os.getcwd()}")
print(f"📂 Файлы: {os.listdir('.')}")

# 2. Проверяем токен (безопасно - только первые 10 символов)
TOKEN = "8708654790:AAEG-HQcgYgLykvceLpGJUiQFLOuS3d8c2k"
print(f"🔑 Токен: {TOKEN[:10]}... (первые 10 символов)")

# 3. ПРЯМОЙ ТЕСТ ОТПРАВКИ (самый честный)
async def direct_test():
    print("\n🚀 ПРЯМОЙ ТЕСТ ОТПРАВКИ СООБЩЕНИЯ")
    bot = Bot(token=TOKEN)
    try:
        me = await bot.get_me()
        print(f"✅ Бот найден: @{me.username}")
        
        msg = await bot.send_message(
            chat_id="@Netizenshop",
            text="🔥 ТЕСТОВОЕ СООБЩЕНИЕ ОТ БОТА! 🔥\n\nЕсли ты это видишь - бот работает!"
        )
        print(f"✅✅✅ СООБЩЕНИЕ УСПЕШНО ОТПРАВЛЕНО!")
        print(f"📝 ID: {msg.message_id}")
        print(f"🔗 Ссылка: https://t.me/Netizenshop/{msg.message_id}")
        return True
    except Exception as e:
        print(f"❌❌❌ ОШИБКА ОТПРАВКИ: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        traceback.print_exc()
        return False

# 4. Запускаем прямой тест
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
test_result = loop.run_until_complete(direct_test())

if not test_result:
    print("\n⚠️ Прямой тест не прошел! Бот НЕ может отправить сообщение.")
    print("Проверь:")
    print("1. Бот добавлен в админы канала @Netizenshop")
    print("2. Токен правильный (скопируй заново у @BotFather)")
    print("3. Канал существует")
    exit(1)
else:
    print("\n✅ Прямой тест ПРОШЕЛ! Бот может отправлять.")
    print("Теперь проверяем Excel...")
    
    # 5. Проверяем Excel
    FILE = "products.xlsx"
    if os.path.exists(FILE):
        try:
            wb = openpyxl.load_workbook(FILE)
            sheet = wb.active
            print(f"📊 Excel: {sheet.max_row} строк, {sheet.max_column} колонок")
            
            # Покажем первые 3 строки данных
            for i, row in enumerate(sheet.iter_rows(min_row=2, max_row=4, values_only=True), 2):
                if any(row):
                    print(f"   Строка {i}: {row[:5]}")  # первые 5 колонок
            wb.close()
        except Exception as e:
            print(f"❌ Ошибка чтения Excel: {e}")
    else:
        print(f"❌ Файл {FILE} не найден!")

print("="*60)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("="*60)

# ========= ОСНОВНОЙ КОД (будет работать только если тест прошел) ==========
if test_result:
    # ... твой основной код здесь ...
    print("\n✅ Запускаю основной бот...")
else:
    print("\n❌ Бот НЕ БУДЕТ работать, пока не исправишь проблемы выше!")
