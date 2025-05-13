import datetime as dt
import logging

from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.main import User
from bot.misc.config import timezone_offset


async def user_swith_one_day(
        session: AsyncSession,
        telegram_id: int,
        new_value: bool
):
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    user.notion_oneday = new_value
    await session.commit()

async def user_swith_sub(
        session: AsyncSession,
        telegram_id: int,
        new_value: bool
):
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    user.status_subscription = new_value
    user.notion_oneday = new_value
    await session.commit()


async def user_subscribe(
        session: AsyncSession,
        telegram_id: int,
        period: str
):
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    time_delta = dt.timedelta()
    type_period = period.split('.')
    match type_period[0]:
        case 'min':
            time_delta = dt.timedelta(minutes=int(type_period[1]))
        case 'day':
            time_delta = dt.timedelta(days=int(type_period[1]))
        case 'mon':
            time_delta = dt.timedelta(days=31*int(type_period[1]))
        case 'year':
            time_delta = dt.timedelta(days=365*int(type_period[1]))
    if user.status_subscription:
        user.subscription += time_delta
    else:
        user.subscription = dt.datetime.now() + time_delta
    user.status_subscription = True
    user.notion_oneday = True
    await session.commit()
    logging.info(f'user {telegram_id} subscribed, DB write')


async def user_new_subscribe(
        session: AsyncSession,
        telegram_id: int,
        selection_date: date
):
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    selected_datetime = dt.datetime.combine(
        selection_date,
        dt.datetime.max.time()
    )
    user.subscription = selected_datetime
    selected_datetime = selected_datetime.replace(tzinfo=timezone_offset)
    if selected_datetime > dt.datetime.now(timezone_offset):
        user.status_subscription = True
        user.notion_oneday = True
        logging.info(f'user {telegram_id} subscribed, DB write')
    else:
        user.status_subscription = False
        user.notion_oneday = False
        logging.info(f'user {telegram_id} un subscribed, DB write')
    await session.commit()
    await session.refresh(user)
    return user



async def user_swith_ban(session: AsyncSession, telegram_id: int) -> bool | None:
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.blocked = not user.blocked
    new_value = not user.blocked
    await session.commit()
    return new_value


async def update_user_moderation_status(
        session: AsyncSession,
        telegram_id: int,
        status: bool,
        bot = None
) -> User:
    """
    Обновить статус модерации пользователя
    :param session: Сессия базы данных
    :param telegram_id: ID пользователя
    :param status: True - одобрен, False - отклонен
    :param bot: Экземпляр бота для отправки уведомления пользователю
    :return: Объект пользователя или None, если пользователь не найден
    """
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is not None:
        user.moderation_status = status
        await session.commit()
        # Обновляем пользователя в сессии
        await session.refresh(user)
        logging.info(f'CRITICAL: User {telegram_id} moderation status updated to {status}, user: {user.moderation_status}')
        
        # Отправляем уведомление пользователю, если бот предоставлен
        if bot is not None:
            from bot.handlers.admin.moderation import send_notification_in_background
            import asyncio
            # Запускаем отправку уведомления в фоновом режиме
            asyncio.create_task(send_notification_in_background(bot, telegram_id, status))
            logging.info(f'CRITICAL: Notification task created for user {telegram_id}, status: {status}')
    else:
        logging.error(f'CRITICAL: User {telegram_id} not found in database')
    return user