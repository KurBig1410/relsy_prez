from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # noqa: F401
from sqlalchemy import Date, String, JSON, Integer, Time, BigInteger, Text  # noqa: F401


class Base(DeclarativeBase):
    pass