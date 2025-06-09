import re
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

# 🔧 Конфигурация
API_TOKEN = os.getenv('API_TOKEN')
GROUP_LINK = 'https://t.me/poputchik_sozak'
OWNER_ID = 691724703

# ✅ Загрузка разрешённых слов
def load_allowed_words(filename="allowed_words.txt"):
    if not os.path.exists(filename):
        return []
    with open(filename, encoding='utf-8') as f:
        words = [line.strip().lower().replace(' ', '') for line in f if line.strip()]
        return words

ALLOWED_WORDS = load_allowed_words()

# ⚙️ Логирование
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {levelname}: {message}",
    style="{",
    handlers=[
        logging.FileHandler("moderator.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ✅ Создание бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 🔁 Обновление списка разрешённых слов
@dp.message(Command("reload"))
async def reload_words(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ Только владелец может использовать эту команду.")
        return
    global ALLOWED_WORDS
    ALLOWED_WORDS = load_allowed_words()
    await message.answer("🔁 Список разрешённых слов обновлён.")
    logging.info(f"✅ Список разрешённых слов обновлён. Всего: {len(ALLOWED_WORDS)}")

# 📦 Проверка на разрешённые слова
def is_message_allowed(text: str) -> bool:
    normalized = text.lower()
    clean_text = normalized.replace(" ", "")
    for word in ALLOWED_WORDS:
        if word in clean_text:
            return True
    return False

# 🔍 Проверка на допустимые ссылки (номер телефона или ссылка на группу)
def is_safe_link(text: str) -> bool:
    phone_pattern = r'(\+7|8)\d{9,10}'
    urls = re.findall(r"https?://\S+", text)
    for url in urls:
        if GROUP_LINK in url:
            continue
        return False
    if re.search(phone_pattern, text):
        return True
    return not urls  # если есть другие ссылки — удалим

# 🧹 Модерация сообщений
@dp.message()
async def moderate_message(message: Message):
    if not message.text:
        return

    text = message.text

    if is_message_allowed(text):
        return

    if not is_safe_link(text):
        await message.delete()
        logging.info(f"Удалена внешняя ссылка от @{message.from_user.username} ({message.from_user.id})")
        return

    await message.delete()
    logging.info(f"Удалено сообщение от @{message.from_user.username} ({message.from_user.id}) — неразрешённый контент")

# ▶️ Запуск бота в режиме polling
async def main():
    logging.info("🚀 Бот запущен в режиме polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
