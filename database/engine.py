import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from database.models import Base
from dotenv import load_dotenv



# Загрузка переменных окружения
load_dotenv()


# Проверка наличия переменной окружения DB_URL
db_url = os.getenv("DB_URL")
if not db_url:
    raise ValueError("Переменная окружения DB_URL не установлена или пуста.")


# Создание асинхронного движка
engine = create_async_engine(db_url, echo=True)


# Настройка session_maker для асинхронных сессий
session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# Асинхронная функция для создания базы данных
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Асинхронная функция для удаления базы данных
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)