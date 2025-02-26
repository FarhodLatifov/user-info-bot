import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# --- Загрузка переменных окружения ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not BOT_TOKEN:
    raise ValueError("Необходимо установить переменную окружения BOT_TOKEN")

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Lifespan менеджер для FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(start_bot())
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# --- Клавиатура ---
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Показать мой профиль", callback_data="show_profile")]
        ]
    )
    return keyboard

# --- Обработчик команды /start ---
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "👋 Привет! Этот бот покажет информацию о твоем аккаунте.",
        reply_markup=get_main_keyboard()
    )

# --- Обработчик кнопки "Показать мой профиль" ---
@dp.callback_query(F.data == "show_profile")
async def show_profile(callback: types.CallbackQuery):
    user = callback.from_user
    profile_info = (
        f"🆔 <b>ID:</b> {user.id}\n"
        f"👤 <b>Имя:</b> {user.first_name or 'Не указано'}\n"
        f"👥 <b>Фамилия:</b> {user.last_name or 'Не указано'}\n"
        f"🌍 <b>Язык:</b> {user.language_code or 'Неизвестно'}\n"
        f"💎 <b>Премиум:</b> {'✅ Да' if user.is_premium else '❌ Нет'}\n"
        f"📌 <b>Тип аккаунта:</b> {'👑 Premium' if user.is_premium else '👤 Пользователь'}"
    )
    await callback.message.edit_text(profile_info, reply_markup=get_main_keyboard())
    await callback.answer()

# --- FastAPI эндпоинт для проверки статуса ---
@app.get("/")
async def health_check():
    return {"status": "running"}

# --- Запуск бота ---
async def start_bot():
    try:
        await bot.set_my_commands([BotCommand(command="start", description="Запустить бота")])
        logger.info("Бот запущен!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Ошибка бота: {e}")
        await bot.session.close()
        os._exit(1)

# --- Запуск FastAPI ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
