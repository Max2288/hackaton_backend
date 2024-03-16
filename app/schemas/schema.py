from pydantic import BaseModel, ConfigDict, Field

from app.db.models import OrderEnum


class UserInfo(BaseModel):
    """Модель данных для создания нового пользователя."""

    username: str = Field(
        min_length=3,
        max_length=20,
        description="Имя пользователя.",
    )
    hashed_password: str = Field(
        description="Хеш пороля пользователя.",
    )


class OrderInfo(BaseModel):
    user: int
    status: OrderEnum
    name: str


class UserEntity(BaseModel):
    """Модель данных для аутентификации пользователя."""

    username: str = Field(description="Имя пользователя.")
    password: str = Field(description="Пароль пользователя.")


class UserResponse(BaseModel):
    """Модель данных для ответа с информацией о пользователе."""

    username: str = Field(description="Имя пользователя.")
