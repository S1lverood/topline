from unittest import result

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.get import get_user_tg_id
from bot.misc import Config
from bot.service.service import check_admin


class IsAdmin(Filter):

    async def __call__(self, message: Message) -> bool:
        return await check_admin(message.from_user.id)



class IsBannedMessage(Filter):

    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        return await check_blocked(session, message.from_user.id)


class IsBannedCallback(Filter):

    async def __call__(self, callback: CallbackQuery, session: AsyncSession) -> bool:
        return await check_blocked(session, callback.from_user.id)


async def check_blocked(session, telegram_id):
    user = await get_user_tg_id(session, telegram_id)
    if user.telegram_id in Config.ADMINS_ID:
        return True
    return not user.blocked