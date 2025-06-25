import os
import re
import logging
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import setup_application

# --- 🔧 Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegram-bot-moderator.onrender.com/webhook")
OWNER_ID = 691724703  # ← Замени на свой Telegram ID
GROUP_LINK = "https://t.me/poputchik_sozak"
ALLOWED_WORDS_FILE = "allowed.txt"

# --- 📜 Загрузка разрешённых слов
def load_allowed_words():
    if not os.path.exists(ALLOWED_WORDS_FILE):
        return set()
    with open(ALLOWED_WORDS_FILE, encoding='utf-8') as f:
        return set(normalize_word(line.strip()) for line in f if line.strip())

def normalize_word(text: str) -> str:
    # Удаляет пробелы, приводит к нижнему регистру, заменяет кириллицу на казахскую
    replacements = {
        'а': 'а', 'ә': 'ә', 'б': 'б', 'в': 'в', 'г': 'г', 'ғ': 'ғ',
        'д': 'д', 'е': 'е', 'ё': 'е', 'ж': 'ж', 'з': 'з', 'и': 'и', 'й': 'и',
        'к': 'к', 'қ': 'қ', 'л': 'л', 'м': 'м', 'н': 'н', 'ң': 'ң',
        'о': 'о', 'ө': 'ө', 'п': 'п', 'р': 'р', 'с': 'с', 'т': 'т',
        'у': 'у', 'ұ': 'ұ', 'ү': 'ү', 'ф': 'ф', 'х': 'х', 'һ': 'һ',
        'ц': 'с', 'ч': 'ш', 'ш': 'ш', 'щ': 'ш', 'ы': 'ы', 'і': 'і', 'э': 'е', 'ю': 'у', 'я': 'а'
    }
    text = re.sub(r'\s+', '', text.lower())
    return ''.join(replacements.get(c, c) for c in text)

ALLOWED_WORDS = load_allowed_words()

# --- ⚙️ Логирование
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {levelname}: {message}",
    style="{",
    handlers=[
        logging.FileHandler("moderator.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)


# --- ✅ Команда /reload
async def reload_words(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ Только владелец может использовать эту команду.")
        return
    global ALLOWED_WORDS
    ALLOWED_WORDS = load_allowed_words()
    await message.answer("🔁 Разрешённые слова обновлены.")

# --- 🔍 Проверка допустимости
def is_allowed_message(text: str) -> bool:
    text_norm = normalize_word(text)
    for word in ALLOWED_WORDS:
        if word in text_norm:
            return True
    return False

def has_external_link(text: str) -> bool:
    for match in re.findall(r'https?://[^\s]+', text):
        if GROUP_LINK not in match:
            return True
    return False

def has_phone_number(text: str) -> bool:
    return bool(re.search(r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', text))

# --- 🧹 Обработка сообщений
async def handle_message(message: Message):
    if not message.text:
        return

    text = message.text

    if has_external_link(text) and not has_phone_number(text):
        await message.delete()
        return

    if not is_allowed_message(text):
        await message.delete()

# --- 🔗 Регистрация хендлеров
def register_handlers(dp: Dispatcher):
        dp.message.register(reload_words, Command("reload"))
        dp.message.register(handle_message)

# --- ▶️ Запуск
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_webhook()
    logging.info("❌ Webhook удалён")

async def main():
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    register_handlers(dp)

    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    setup_application(app, dp, bot=bot, path="/webhook")
    return app

if __name__ == "__main__":
    app = asyncio.run(main())
    web.run_app(app, port=int(os.getenv("PORT", 10000)))


