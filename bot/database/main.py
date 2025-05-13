from sqlalchemy.ext.asyncio import create_async_engine

from bot.misc import Config

import os

# Создаем директорию для базы данных SQLite, если она не существует
db_dir = os.path.join(os.path.dirname(__file__), 'sqlite')
os.makedirs(db_dir, exist_ok=True)

# Путь к файлу базы данных SQLite
db_path = os.path.join(db_dir, 'PrivateClubDB.db')

# Используем SQLite вне зависимости от значения DEBUG
ENGINE = f"sqlite+aiosqlite:///{db_path}"


def engine():
    return create_async_engine(ENGINE)
