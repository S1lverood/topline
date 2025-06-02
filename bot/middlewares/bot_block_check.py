from typing import Callable, Awaitable, Dict, Any, cast

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.main import User as UserModel


class BotBlockCheckMiddleware(BaseMiddleware):
    """
    Middleware для проверки полной блокировки пользователя в боте.
    Если пользователь заблокирован (bot_blocked=True), то его сообщения будут отклонены.
    """
    
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        # Проверяем, что событие содержит информацию о пользователе
        user = data.get("event_from_user")
        if not user:
            # Если нет информации о пользователе, пропускаем обработку
            return await handler(event, data)
        
        # Получаем ID пользователя
        user_id = user.id
        
        # Пропускаем проверку для администраторов
        from bot.misc import Config
        if user_id in Config.ADMINS_ID:
            return await handler(event, data)
        
        # Проверяем, заблокирован ли пользователь в боте
        session: AsyncSession = data.get("session")
        if session:
            # Запрос к базе данных для проверки статуса блокировки
            statement = select(UserModel).filter(UserModel.telegram_id == user_id)
            result = await session.execute(statement)
            user_db = result.scalar_one_or_none()
            
            # Если пользователь найден и заблокирован, отклоняем сообщение
            if user_db and user_db.blocked:
                # Здесь можно добавить логирование или другие действия
                # Просто возвращаем None, чтобы прервать обработку сообщения
                return None
        
        # Если пользователь не заблокирован, продолжаем обработку
        return await handler(event, data)
