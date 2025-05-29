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
        bot = None,
        user_record_ids = None
) -> User:
    """
    Обновить статус модерации пользователя
    :param session: Сессия базы данных
    :param telegram_id: ID пользователя
    :param status: True - одобрен, False - отклонен
    :param bot: Экземпляр бота для отправки уведомления пользователю
    :param user_record_ids: Список ID записей пользователя для обновления
    :return: Объект пользователя или None, если пользователь не найден
    """
    import datetime
    logging.info(f'CRITICAL: Starting update_user_moderation_status for user {telegram_id} with status {status}')
    logging.info(f'CRITICAL: Current time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logging.info(f'CRITICAL: Bot provided: {bot is not None}')
    logging.info(f'CRITICAL: User record IDs provided: {user_record_ids}')
    
    # Сначала получаем основного пользователя для возврата
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    logging.info(f'CRITICAL: Found user in database: {user is not None}')
    if user:
        logging.info(f'CRITICAL: User details - ID: {user.id}, telegram_id: {user.telegram_id}, current moderation_status: {user.moderation_status}')
    
    if user is not None:
        # Обновляем статус модерации для основного пользователя
        user.moderation_status = status
        
        # Если переданы ID записей пользователя, обновляем статус для всех записей
        if user_record_ids and len(user_record_ids) > 0:
            try:
                logging.info(f'CRITICAL: Updating moderation status for all user records: {user_record_ids}')
                # Обновляем статус модерации для всех записей пользователя
                for record_id in user_record_ids:
                    # Получаем запись пользователя по ID
                    record_stmt = select(User).filter(User.id == record_id)
                    record_result = await session.execute(record_stmt)
                    user_record = record_result.scalar_one_or_none()
                    
                    if user_record:
                        user_record.moderation_status = status
                        logging.info(f'CRITICAL: Updated moderation status for user record ID {record_id} to {status}')
            except Exception as e:
                logging.error(f'CRITICAL: Error updating moderation status for user records: {e}')
                import traceback
                logging.error(f'CRITICAL: Traceback: {traceback.format_exc()}')
        
        # Сохраняем изменения в базе данных
        await session.commit()
        # Обновляем пользователя в сессии
        await session.refresh(user)
        logging.info(f'CRITICAL: User {telegram_id} moderation status updated to {status}, user: {user.moderation_status}')
        
        # Отправляем уведомление пользователю, если бот предоставлен
        if bot is not None:
            from bot.handlers.admin.moderation import send_notification_in_background
            import asyncio
            # Запускаем отправку уведомления в фоновом режиме
            task = asyncio.create_task(send_notification_in_background(bot, telegram_id, status))
            logging.info(f'CRITICAL: Notification task created for user {telegram_id}, status: {status}')
            
            # Добавляем обработчик завершения задачи для логирования результата
            def log_task_result(task):
                try:
                    # Проверяем, была ли задача отменена или завершена с ошибкой
                    if task.cancelled():
                        logging.error(f'CRITICAL: Notification task for user {telegram_id} was cancelled')
                    elif task.exception():
                        logging.error(f'CRITICAL: Notification task for user {telegram_id} failed with error: {task.exception()}')
                    else:
                        logging.info(f'CRITICAL: Notification task for user {telegram_id} completed successfully')
                except Exception as e:
                    logging.error(f'CRITICAL: Error in log_task_result for user {telegram_id}: {e}')
            
            # Добавляем callback для отслеживания результата
            task.add_done_callback(log_task_result)
    else:
        logging.error(f'CRITICAL: User {telegram_id} not found in database')
    return user