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
API_TOKEN = os.getenv('API_TOKEN')  # ← Вставь сюда свой токен
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Адрес твоего вебхука (Render выдаст ссылку)
GROUP_LINK = 'https://t.me/poputchik_sozak'  # ← Укажи свою ссылку
OWNER_ID = 691724703  # ← замени это число на свой Telegram user ID


# 📜 Загрузка запрещённых слов
def load_banned_words(filename="xwords.txt"):
    if not os.path.exists(filename):
        return []
    with open(filename, encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]

BANNED_WORDS = load_banned_words()

# ⚙️ Настройка логирования — файл + консоль
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {levelname}: {message}",
    style="{",
    handlers=[
        logging.FileHandler("moderator.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ✅ Создание бота с правильной конфигурацией (aiogram 3.7+)
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# 🔍 Проверка на внешние ссылки
def has_external_links(text: str) -> bool:
    urls = re.findall(r"https?://\S+", text)
    for url in urls:
        if GROUP_LINK not in url:
            return True
    return False

# 🚫 Проверка на запрещённые слова
def contains_banned_words(text: str) -> bool:
    text = text.lower()
    return any(bad_word in text for bad_word in BANNED_WORDS)

# 🧹 Обработка сообщений
@dp.message(Command("reload"))
async def reload_words(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ Только владелец может использовать эту команду.")
        logging.warning(f"❌ Попытка перезагрузки от не-владельца: {message.from_user.id}")
        return
    global BANNED_WORDS
    BANNED_WORDS = load_banned_words()
    await message.answer("🔁 Список запрещённых слов обновлён.")
    logging.info(f"✅ Список обновлён владельцем. Всего слов: {len(BANNED_WORDS)}")

@dp.message()
async def moderate_message(message: Message):
    if not message.text:
        return

    text = message.text

    if has_external_links(text):
        await message.delete()
        logging.info(
            f"Удалено сообщение с внешней ссылкой от @{message.from_user.username} ({message.from_user.id})"
        )
        return

    if contains_banned_words(text):
        await message.delete()
        logging.info(
            f"Удалено сообщение с запрещённым словом от @{message.from_user.username} ({message.from_user.id})"
        )
        return

# ▶️ Запуск бота
from aiohttp import web
from aiogram.webhook.aiohttp_server import setup_application

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_webhook()
    logging.info("❌ Webhook удалён")

async def main():
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    setup_application(app, dp, bot=bot)
    logging.info("🚀 AIOHTTP приложение запущено")
    return app

if __name__ == "__main__":
    web.run_app(main())
