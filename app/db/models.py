from __future__ import annotations

from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, MetaData, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, relationship, mapped_column
import enum
from app.core.config import Config
from app.services.security import hash_password

# Определение метаданных для таблиц
metadata = MetaData(
    schema=Config.SCHEMA_NAME,
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)

# Создание базового класса для всех сущностей базы данных
Base: Any = declarative_base(metadata=metadata)


class IDMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)


class User(Base, IDMixin):
    """Модель пользователя в системе."""

    __tablename__ = 'user'
    __table_args__ = {'schema': Config.SCHEMA_NAME}

    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    _hashed_password: Mapped[str] = mapped_column('hashed_password', Text, nullable=False)

    @property
    def hashed_password(self) -> str:
        """Возвращает хешированный пароль пользователя.

        Returns:
            str: Хешированный пароль пользователя.
        """
        return self._hashed_password

    @hashed_password.setter
    def hashed_password(self, plain_password: str) -> None:
        """Устанавливает хешированный пароль пользователя.

        Args:
            plain_password (str): Нехешированный пароль пользователя.
        """
        self._hashed_password = hash_password(plain_password)


class OrderEnum(enum.Enum):
    success = 'success'
    failed = 'failed'
    pending = 'pending'


class Order(Base, IDMixin):
    """Модель записи в системе."""

    __tablename__ = 'order'
    __table_args__ = {'schema': Config.SCHEMA_NAME}

    user: Mapped[int] = mapped_column(Integer, ForeignKey(f'{Config.SCHEMA_NAME}.user.id'))
    status: Mapped[OrderEnum] = mapped_column(ENUM(OrderEnum, inherit_schema=True), default=OrderEnum.pending)
    name: Mapped[str] = mapped_column(Text, nullable=False)
