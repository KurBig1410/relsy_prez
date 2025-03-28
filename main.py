import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Time, BigInteger, select, delete, Date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime, date, timedelta

# Logging
logging.basicConfig(level=logging.INFO)

# === DATABASE SETUP === #
engine = create_async_engine("sqlite+aiosqlite:///bot.db")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(String)  # 'user' or 'admin'

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(String)
    time: Mapped[str] = mapped_column(String)  # HH:MM
    date: Mapped[str] = mapped_column(String)  # YYYY-MM-DD  # noqa: F811

class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)

# === FSM States === #
class AdminStates(StatesGroup):
    add_admin_name = State()
    add_admin_id = State()
    add_user_name = State()
    add_user_id = State()
    add_chat_id = State()
    add_message_title = State()
    add_message_text = State()
    add_message_time = State()
    add_message_date = State()

# === BOT SETUP === #
bot = Bot(token="7149425421:AAGESxE2Y-7gX5u0vUozwrdvi7Tcwn4FDZ0")
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# === UTILS === #
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def send_scheduled_messages():
    async with SessionLocal() as session:
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        today = now.strftime('%Y-%m-%d')

        result = await session.execute(
            select(Message).where(
                Message.date == today,
                Message.time <= current_time
            )
        )
        messages = result.scalars().all()

        chats_result = await session.execute(select(Chat))
        chats = chats_result.scalars().all()

        for msg in messages:
            for chat in chats:
                try:
                    await bot.send_message(chat.chat_id, msg.text)
                except Exception as e:
                    logging.warning(f"Не удалось отправить сообщение в чат {chat.chat_id}: {e}")
            await session.delete(msg)

        await session.commit()

# === ADMIN PANEL === #
@dp.message(F.text == "/admin")
async def admin_panel(msg: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Добавить администратора")],
        [KeyboardButton(text="Добавить пользователя")],
        [KeyboardButton(text="Добавить ID чата")],
        [KeyboardButton(text="Добавить сообщение")],
        [KeyboardButton(text="Список администраторов")],
        [KeyboardButton(text="Список пользователей")],
        [KeyboardButton(text="Список сообщений")],
        [KeyboardButton(text="Удалить все сообщения")],
    ], resize_keyboard=True)
    await msg.answer("Админ-панель:", reply_markup=kb)

# === УДАЛЕНИЕ ВСЕХ СООБЩЕНИЙ === #
@dp.message(F.text == "Удалить все сообщения")
async def delete_all_messages(msg: types.Message):
    async with SessionLocal() as session:
        await session.execute(delete(Message))
        await session.commit()
    await msg.answer("Все сообщения удалены из базы данных.")

# === ДОБАВЛЕНИЕ СООБЩЕНИЯ === #
@dp.message(F.text == "Добавить сообщение")
async def add_message(msg: types.Message, state: FSMContext):
    await msg.answer("Введите название сообщения:")
    await state.set_state(AdminStates.add_message_title)

@dp.message(AdminStates.add_message_title)
async def message_title_step(msg: types.Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Введите текст сообщения:")
    await state.set_state(AdminStates.add_message_text)

@dp.message(AdminStates.add_message_text)
async def message_text_step(msg: types.Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await msg.answer("Введите время отправки (в формате ЧЧ:ММ):")
    await state.set_state(AdminStates.add_message_time)

@dp.message(AdminStates.add_message_time)
async def message_time_step(msg: types.Message, state: FSMContext):
    await state.update_data(time=msg.text)
    await msg.answer("Введите дату отправки (в формате ГГГГ-ММ-ДД):")
    await state.set_state(AdminStates.add_message_date)

@dp.message(AdminStates.add_message_date)
async def message_date_step(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    async with SessionLocal() as session:
        session.add(Message(
            title=data['title'],
            text=data['text'],
            time=data['time'],
            date=msg.text
        ))
        await session.commit()
    await msg.answer("Сообщение добавлено!")
    await state.clear()


# === ДОБАВЛЕНИЕ ЧАТА === #
@dp.message(F.text == "Добавить ID чата")
async def add_chat(msg: types.Message, state: FSMContext):
    await msg.answer("Отправьте любое сообщение из нужного чата или введите его ID:")
    await state.set_state(AdminStates.add_chat_id)

@dp.message(AdminStates.add_chat_id)
async def save_chat_id(msg: types.Message, state: FSMContext):
    try:
        chat_id = int(msg.text) if msg.text.lstrip('-').isdigit() else msg.chat.id
        async with SessionLocal() as session:
            session.add(Chat(chat_id=chat_id))
            await session.commit()
        await msg.answer(f"Чат с ID `{chat_id}` добавлен в базу данных.", parse_mode="Markdown")
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")
    await state.clear()

# === СПИСОК СООБЩЕНИЙ === #
@dp.message(F.text == "Список сообщений")
async def list_messages(msg: types.Message):
    async with SessionLocal() as session:
        result = await session.execute(select(Message))
        messages = result.scalars().all()
        if messages:
            text = "\n\n".join([
                f"📌 *{m.title}*\n🗓 {m.date} ⏰ {m.time}\n📝 {m.text}"
                for m in messages
            ])
        else:
            text = "Нет сохранённых сообщений."
        await msg.answer(text, parse_mode="Markdown")

# === SCHEDULER SETUP === #
scheduler.add_job(send_scheduled_messages, CronTrigger(minute="*"))  # Every minute

# === STARTUP === #
async def main():
    await init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
