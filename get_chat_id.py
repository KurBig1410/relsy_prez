# Получение ID чата
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
# from aiogram.runner import run_polling
from aiogram.client.default import DefaultBotProperties
import asyncio

# Замените на свой токен
BOT_TOKEN = "7149425421:AAGESxE2Y-7gX5u0vUozwrdvi7Tcwn4FDZ0"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("chatid"))
async def get_chat_id(message: Message):
    chat = message.chat
    await message.answer(f"🆔 Chat ID: <code>{chat.id}</code>\n"
                         f"💬 Title: {chat.title or chat.full_name}\n"
                         f"📂 Type: {chat.type}")

# === STARTUP === #
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())