from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.get import get_user_tg_id
from bot.misc import Config
from bot.service.service import check_admin


class IsAdmin(Filter):

    async def __call__(self, event) -> bool:
        # Проверяем, является ли событие сообщением или колбэком
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return False
            
        return await check_admin(user_id)



class IsBannedMessage(Filter):

    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        return await check_blocked(session, message.from_user.id)


class IsBannedCallback(Filter):

    async def __call__(self, callback: CallbackQuery, session: AsyncSession) -> bool:
        return await check_blocked(session, callback.from_user.id)


async def check_blocked(session, telegram_id):
    import logging
    user = await get_user_tg_id(session, telegram_id)
    # Проверяем, что пользователь существует в базе данных
    if user is None:
        # Если пользователя нет в базе, разрешаем доступ (он будет создан при первом взаимодействии)
        return True
    
    # Проверяем, является ли пользователь администратором
    if user.telegram_id in Config.ADMINS_ID:
        return True
    
    # Проверяем статус модерации пользователя
    if user.moderation_status is False:
        logging.info(f"User {telegram_id} access denied: moderation_status is False")
        return False
    
    # Проверяем, не заблокирован ли пользователь
    if user.blocked:
        logging.info(f"User {telegram_id} access denied: user is blocked")
        return False
    
    # Если все проверки пройдены, разрешаем доступ
    return True