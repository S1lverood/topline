import logging
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Set

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

# Список пользователей, которым уже отправлено уведомление об отказе
# Используем глобальную переменную для отслеживания
rejection_notifications_sent: Set[int] = set()

from bot.database.crud.create import add_moderation_vote
from bot.database.crud.get import get_user_tg_id, get_moderation_votes
from bot.database.crud.update import update_user_moderation_status
# from bot.keyboards.admin_inline import moderation_keyboard
from bot.misc import Config
from bot.misc.callback_data import ModerationVoteCallback, RulesAcceptCallback

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

# Создаем роутер для модерации
moderation_router = Router()

# Экспортируем роутер для регистрации в основном приложении
__all__ = ["moderation_router", "notify_admins_about_new_user", "send_guaranteed_message", "process_rules_accept"]


async def send_guaranteed_message(bot, user_id: int, text: str, reply_markup=None, parse_mode=None, is_approval=True) -> bool:
    """
    Гарантированная отправка сообщения пользователю с использованием разных методов
    :param bot: Экземпляр бота
    :param user_id: ID пользователя
    :param text: Текст сообщения
    :param reply_markup: Клавиатура (опционально)
    :param parse_mode: Режим форматирования текста (опционально)
    :param is_approval: True если это сообщение об одобрении, False если об отклонении
    :return: True если удалось отправить сообщение, False в противном случае
    """
    message_type = "approval" if is_approval else "rejection"
    logging.info(f"CRITICAL: Starting guaranteed message delivery to user {user_id} (type: {message_type})")
    
    success = False
    attempts = 0
    max_attempts = 5  # Увеличиваем максимальное количество попыток
    
    # Увеличиваем задержку между попытками
    delay_seconds = 1.0
    
    # Сохраняем все ошибки для анализа
    errors = []
    
    # Пробуем отправить сообщение несколько раз с задержкой
    while not success and attempts < max_attempts:
        attempts += 1
        logging.info(f"CRITICAL: Attempt {attempts}/{max_attempts} to send message to user {user_id}")
        
        # Метод 1: Стандартный метод send_message
        try:
            logging.info(f"CRITICAL: Trying standard method for user {user_id} (attempt {attempts})")
            await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            logging.info(f"CRITICAL: Message sent to user {user_id} using standard method (attempt {attempts})")
            success = True
            # Добавляем дополнительную задержку после успешной отправки
            await asyncio.sleep(1.0)
            break
        except Exception as e:
            error_msg = f"Error sending message to user {user_id} using standard method (attempt {attempts}): {e}"
            logging.error(f"CRITICAL: {error_msg}")
            errors.append(f"Standard method: {str(e)}")
            await asyncio.sleep(delay_seconds)  # Задержка перед следующей попыткой
            delay_seconds *= 1.5  # Увеличиваем задержку с каждой попыткой
        
        # Метод 2: Прямой вызов API
        try:
            logging.info(f"CRITICAL: Trying direct API method for user {user_id} (attempt {attempts})")
            from aiogram.methods.send_message import SendMessage
            result = await bot(SendMessage(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode))
            logging.info(f"CRITICAL: Message sent to user {user_id} using direct API (attempt {attempts}): {result}")
            success = True
            # Добавляем дополнительную задержку после успешной отправки
            await asyncio.sleep(1.0)
            break
        except Exception as e:
            error_msg = f"Error sending message to user {user_id} using direct API (attempt {attempts}): {e}"
            logging.error(f"CRITICAL: {error_msg}")
            errors.append(f"Direct API: {str(e)}")
            await asyncio.sleep(delay_seconds)  # Задержка перед следующей попыткой
            delay_seconds *= 1.5  # Увеличиваем задержку с каждой попыткой
            
        # Метод 3: Использование copy_message для отправки сообщения через бота
        if not success and attempts < max_attempts:
            try:
                logging.info(f"CRITICAL: Trying copy_message method for user {user_id} (attempt {attempts})")
                # Создаем временное сообщение в специальном чате для копирования
                temp_chat_id = Config.TEMP_CHAT_ID if hasattr(Config, 'TEMP_CHAT_ID') else Config.ADMINS_ID[0]
                
                # Отправляем сообщение во временный чат
                temp_message = await bot.send_message(
                    chat_id=temp_chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                
                # Копируем сообщение пользователю
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=temp_chat_id,
                    message_id=temp_message.message_id
                )
                
                # Удаляем временное сообщение
                await bot.delete_message(chat_id=temp_chat_id, message_id=temp_message.message_id)
                
                logging.info(f"CRITICAL: Message sent to user {user_id} using copy_message method (attempt {attempts})")
                success = True
                await asyncio.sleep(1.0)
                break
            except Exception as e:
                error_msg = f"Error sending message to user {user_id} using copy_message method (attempt {attempts}): {e}"
                logging.error(f"CRITICAL: {error_msg}")
                errors.append(f"Copy message: {str(e)}")
                await asyncio.sleep(delay_seconds)  # Задержка перед следующей попыткой
                delay_seconds *= 1.5  # Увеличиваем задержку с каждой попыткой
    
    # Если все попытки не удались, пробуем отправить простое сообщение
    if not success:
        try:
            from aiogram.methods.send_message import SendMessage
            # Упрощенное сообщение в зависимости от типа уведомления
            if is_approval:
                simple_text = "Вы были одобрены. Отправьте /start для начала использования бота."
            else:
                simple_text = "К сожалению, Вы не прошли модерацию. Вы можете повторно попробовать через 24 часа."
                
            result = await bot(SendMessage(chat_id=user_id, text=simple_text))
            logging.info(f"CRITICAL: Simple message sent to user {user_id} using direct API: {result}")
            success = True
        except Exception as e:
            logging.error(f"CRITICAL: Error sending simple message to user {user_id} using direct API: {e}")
    
    # Если не удалось отправить сообщение после всех попыток, логируем это
    if not success:
        error_summary = "\n".join(errors)
        logging.error(f"CRITICAL: Failed to send message to user {user_id} after {max_attempts} attempts. Errors: {error_summary}")
        
        # Если это уведомление об отклонении, добавляем пользователя в список уведомленных,
        # чтобы не пытаться отправить ему сообщение повторно
        if not is_approval:
            global rejection_notifications_sent
            rejection_notifications_sent.add(user_id)
            logging.info(f"CRITICAL: Added user {user_id} to rejection_notifications_sent list after failed attempts")
            logging.info(f"CRITICAL: Current rejection_notifications_sent list size: {len(rejection_notifications_sent)}")
        
        # Пытаемся уведомить администраторов о проблеме
        try:
            admin_notification = f"CRITICAL: Не удалось отправить уведомление пользователю {user_id} после {max_attempts} попыток"
            for admin_id in Config.ADMINS_ID[:1]:  # Уведомляем только первого админа в списке
                await bot.send_message(chat_id=admin_id, text=admin_notification)
                logging.info(f"CRITICAL: Notified admin {admin_id} about failed message delivery to user {user_id}")
        except Exception as e:
            logging.error(f"CRITICAL: Failed to notify admin about message delivery failure: {e}")
    else:
        logging.info(f"CRITICAL: Successfully sent message to user {user_id} after {attempts} attempts")
    
    return success


async def send_notification_in_background(bot: Bot, user_id: int, status: bool) -> None:
    """
    Отправляет уведомление пользователю в фоновом режиме
    :param bot: Экземпляр бота
    :param user_id: ID пользователя
    :param status: True - одобрен, False - отклонен
    """
    logging.info(f"CRITICAL: Starting notification process for user {user_id}, status: {status}")
    logging.info(f"CRITICAL: Bot info: {bot.id}")
    logging.info(f"CRITICAL: Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем, активен ли бот
    try:
        bot_info = await bot.get_me()
        logging.info(f"CRITICAL: Bot is active: {bot_info.id}")
    except Exception as e:
        logging.error(f"CRITICAL: Bot is not active: {e}")
        return
    
    # Отправляем уведомление пользователю о результате модерации
    if status:  # Пользователь одобрен
        try:
            logging.info(f"CRITICAL: Preparing approval notification for user {user_id}")
            # Отправляем сообщение об одобрении
            message = await bot.send_message(
                chat_id=user_id,
                text="Модерация прошла успешно! Теперь вы можете пользоваться ботом."
            )
            logging.info(f"CRITICAL: Direct message sent to user {user_id}: {message.message_id}")
        except Exception as e:
            logging.error(f"CRITICAL: Error sending approval notification to user {user_id}: {e}")
            # Пробуем отправить через гарантированную доставку
            try:
                await send_guaranteed_message(
                    bot=bot,
                    user_id=user_id,
                    text="Модерация прошла успешно! Теперь вы можете пользоваться ботом.",
                    is_approval=True
                )
            except Exception as backup_error:
                logging.error(f"CRITICAL: Backup method also failed for user {user_id}: {backup_error}")
    else:  # Пользователь отклонен
        try:
            logging.info(f"CRITICAL: Preparing rejection notification for user {user_id}")
            # Отправляем сообщение об отклонении
            message = await bot.send_message(
                chat_id=user_id,
                text="К сожалению, ваша заявка на использование бота была отклонена администратором."
            )
            logging.info(f"CRITICAL: Direct message sent to user {user_id}: {message.message_id}")
        except Exception as e:
            logging.error(f"CRITICAL: Error sending rejection notification to user {user_id}: {e}")
            # Пробуем отправить через гарантированную доставку
            try:
                await send_guaranteed_message(
                    bot=bot,
                    user_id=user_id,
                    text="К сожалению, ваша заявка на использование бота была отклонена администратором.",
                    is_approval=False
                )
            except Exception as backup_error:
                logging.error(f"CRITICAL: Backup method also failed for user {user_id}: {backup_error}")

    # Отправляем дополнительное приветственное сообщение, если пользователь был одобрен
    if status:
        logging.info(f"CRITICAL: Attempting to send welcome message to user {user_id}")
        try:
            # Отправляем приветственное сообщение
            welcome_text = "Добро пожаловать! Теперь вы можете использовать все функции бота.\nОтправьте /start чтобы начать"

            # Используем гарантированную отправку сообщения
            welcome_success = await send_guaranteed_message(
                bot=bot,
                user_id=user_id,
                text=welcome_text,
                is_approval=True
            )

            if welcome_success:
                logging.info(f"CRITICAL: Welcome message successfully sent to user {user_id}")
            else:
                logging.error(f"CRITICAL: Failed to send welcome message to user {user_id}")
        except Exception as e:
            logging.error(f"CRITICAL: Error sending welcome message to user {user_id}: {e}")
    
    # Завершаем выполнение функции
    logging.info(f"CRITICAL: Notification process for user {user_id} completed in background task")

# Регистрируем обработчик для кнопки "Начать использование бота"
@moderation_router.callback_query(F.data == "start_bot")
async def process_start_bot_callback(
        callback: CallbackQuery,
        session: AsyncSession,
        i18n: TranslatorRunner
):
    logging.info(f"CRITICAL: Processing start_bot callback for user {callback.from_user.id}")
    try:
        # Отвечаем на коллбэк
        await callback.answer("Запускаем бота...")
        
        # Удаляем кнопку из сообщения
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
            logging.info(f"CRITICAL: Button removed from message for user {callback.from_user.id}")
        except Exception as e:
            logging.error(f"CRITICAL: Error removing button from message for user {callback.from_user.id}: {e}")
        
        # Импортируем необходимые компоненты для эмуляции команды /start
        from bot.handlers.user.main import process_start_command
        from aiogram.types import Message
        from aiogram_dialog import DialogManager
        from aiogram.types.user import User
        
        try:
            # Создаем объект сообщения для эмуляции команды /start
            fake_message = Message(
                message_id=0,
                date=datetime.now(),
                chat=callback.message.chat,
                from_user=callback.from_user,
                sender_chat=callback.message.chat,
                text="/start",
                bot=callback.bot
            )
            
            # Напрямую вызываем обработчик команды /start
            from aiogram_dialog import DialogManager
            dialog_manager = DialogManager(callback, None)
            
            # Вызываем process_start_command с правильными параметрами
            await process_start_command(fake_message, dialog_manager, session, i18n)
            
            logging.info(f"CRITICAL: Successfully emulated /start command for user {callback.from_user.id}")
        except Exception as e:
            logging.error(f"CRITICAL: Error emulating /start command for user {callback.from_user.id}: {e}")
            
            # Запасной вариант - отправка сообщения с основным меню
            from aiogram.methods.send_message import SendMessage
            from aiogram.enums import ParseMode
            
            try:
                welcome_text = "Добро пожаловать! Вы успешно прошли модерацию. Пожалуйста, отправьте команду /start для начала работы с ботом."
                await callback.bot(SendMessage(
                    chat_id=callback.from_user.id,
                    text=welcome_text,
                    parse_mode=ParseMode.HTML
                ))
                logging.info(f"CRITICAL: Sent fallback welcome message to user {callback.from_user.id}")
            except Exception as e2:
                logging.error(f"CRITICAL: Error sending fallback welcome message to user {callback.from_user.id}: {e2}")
        
        logging.info(f"CRITICAL: User {callback.from_user.id} started using the bot after moderation approval")
    except Exception as e:
        logging.error(f"CRITICAL: Error processing start_bot callback for user {callback.from_user.id}: {e}")


# Регистрируем обработчик для принятия правил
async def process_rules_accept(callback: CallbackQuery, i18n: TranslatorRunner):
    """
    Обработчик принятия правил пользователем
    """
    try:
        await callback.message.edit_text(
            text=i18n.user.text.rules_accepted(),
            reply_markup=None
        )
        await callback.answer(i18n.user.text.rules_accepted_notification())
        logging.info(f"User {callback.from_user.id} accepted the rules")
    except Exception as e:
        logging.error(f"Error processing rules acceptance for user {callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


# Регистрируем обработчик для принятия правил
@moderation_router.callback_query(RulesAcceptCallback.filter())
async def handle_rules_accept(callback: CallbackQuery, i18n: TranslatorRunner):
    await process_rules_accept(callback, i18n)

# Регистрируем обработчик голосования за модерацию  ПЕРЕНЕСЕНО В user/main.py
# @moderation_router.callback_query(ModerationVoteCallback.filter())
# async def process_moderation_vote(
#         callback: CallbackQuery,
#         callback_data: ModerationVoteCallback,
#         session: AsyncSession,
#         i18n: TranslatorRunner
# ) -> None:
#     """
#     Обработчик голосования администратора за модерацию пользователя
#     """
#     # Добавляем расширенное логирование для отслеживания проблем
#     logging.info(f"CRITICAL: Received moderation vote callback from admin {callback.from_user.id} for user {callback_data.user_id}")
#     logging.info(f"CRITICAL: Vote details - approved: {callback_data.approved}, callback_id: {callback.id}")
#     logging.info(f"CRITICAL: Full callback data: {callback_data}")
#     logging.info(f"CRITICAL: Callback message: {callback.message.message_id if callback.message else 'None'}")
#     logging.info(f"CRITICAL: Admin info: {callback.from_user.id}, {callback.from_user.username}, {callback.from_user.full_name}")
#     logging.info(f"CRITICAL: Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     logging.info(f"CRITICAL: Bot info: {callback.bot.id}")
#     logging.info(f"CRITICAL: Session info: {session.__class__.__name__}")
#     logging.info(f"CRITICAL: i18n info: {i18n.__class__.__name__}")
#
#     try:
#         logging.info(f"Admin {callback.from_user.id} voted for user {callback_data.user_id}, approved: {callback_data.approved}")
#     except Exception as e:
#         logging.error(f"CRITICAL: Error in initial logging: {e}")
#         # Продолжаем выполнение функции, несмотря на ошибку в логировании
#
#     # Проверяем текущий статус пользователя перед добавлением голоса
#     # Это позволит избежать повторной модерации уже одобренных пользователей
#     current_user = await get_user_tg_id(session, callback_data.user_id)
#     if current_user and current_user.moderation_status is True and callback_data.approved is True:
#         logging.info(f"User {callback_data.user_id} is already approved, skipping moderation process")
#         await callback.answer(f"Пользователь {callback_data.user_id} уже одобрен")
#
#         # Удаляем сообщение с кнопками голосования
#         try:
#             await callback.message.delete()
#             logging.info(f"Deleted moderation message for admin {callback.from_user.id} after skipping")
#         except Exception as e:
#             logging.error(f"Error deleting moderation message: {e}")
#
#         # Отправляем сообщение администратору
#         try:
#             await callback.bot.send_message(
#                 chat_id=callback.from_user.id,
#                 text=f"Пользователь ID: {callback_data.user_id} уже был одобрен ранее."
#             )
#         except Exception as e:
#             logging.error(f"Error sending notification to admin {callback.from_user.id}: {e}")
#
#         return
#
#     # Добавляем голос в базу данных
#     vote = await add_moderation_vote(
#         session=session,
#         user_id=callback_data.user_id,
#         admin_id=callback.from_user.id,
#         approved=callback_data.approved
#     )
#
#     if vote is None:
#         logging.error(f"Error adding vote for user {callback_data.user_id} by admin {callback.from_user.id}")
#         await callback.answer("Произошла ошибка при голосовании. Попробуйте еще раз.")
#         return
#
#     # Получаем все голоса для этого пользователя
#     try:
#         logging.info(f"CRITICAL: Getting all votes for user {callback_data.user_id}")
#         votes = await get_moderation_votes(session, callback_data.user_id)
#         logging.info(f"CRITICAL: Received {len(votes)} votes for user {callback_data.user_id}")
#
#         # Проверяем и логируем каждый голос
#         for i, vote in enumerate(votes):
#             logging.info(f"CRITICAL: Vote {i+1} details - admin_id: {vote.admin_id}, approved: {vote.approved}")
#
#         if not votes:
#             logging.error(f"CRITICAL: No votes found for user {callback_data.user_id}")
#
#             # Пробуем получить голос напрямую
#             try:
#                 # Импортируем функцию для получения голоса напрямую, если она существует
#                 from bot.database.crud.get import get_user_moderation_vote
#                 direct_vote = await get_user_moderation_vote(session, callback_data.user_id, callback.from_user.id)
#                 if direct_vote:
#                     logging.info(f"CRITICAL: Found direct vote for user {callback_data.user_id} from admin {callback.from_user.id}")
#                     votes = [direct_vote]
#                 else:
#                     logging.error(f"CRITICAL: No direct vote found for user {callback_data.user_id} from admin {callback.from_user.id}")
#                     await callback.answer("Произошла ошибка при получении голосов. Попробуйте еще раз.")
#                     return
#             except ImportError:
#                 # Если функция не существует, используем текущий голос
#                 logging.info(f"CRITICAL: get_user_moderation_vote not found, using current vote")
#                 votes = [vote]
#     except Exception as e:
#         logging.error(f"CRITICAL: Error getting votes: {e}")
#         import traceback
#         logging.error(f"CRITICAL: Traceback: {traceback.format_exc()}")
#         await callback.answer("Произошла ошибка при получении голосов. Попробуйте еще раз.")
#         return
#
#     # Получаем пользователя из базы данных
#     user = await get_user_tg_id(session, callback_data.user_id)
#     if not user:
#         logging.error(f"User {callback_data.user_id} not found in database")
#         await callback.answer("Пользователь не найден в базе данных.")
#         return
#
#     # Получаем все записи пользователя в базе данных
#     # Это позволит обработать все запросы пользователя на модерацию,
#     # независимо от того, на какое сообщение ответил администратор
#     try:
#         from sqlalchemy import select, desc
#         # Используем правильный путь импорта модели User
#         from bot.database.models.main import User
#
#         # Получаем все записи пользователя в базе данных
#         # Используем поле subscription для сортировки по времени
#         stmt = select(User).filter(User.telegram_id == callback_data.user_id).order_by(desc(User.subscription))
#         result = await session.execute(stmt)
#         all_user_records = result.scalars().all()
#
#         if not all_user_records:
#             logging.error(f"No user records found for user {callback_data.user_id} in database")
#             await callback.answer("Пользователь не найден в базе данных.")
#             return
#
#         # Получаем самую последнюю запись пользователя
#         latest_user = all_user_records[0] if all_user_records else None
#
#         if latest_user and latest_user.id != user.id:
#             logging.info(f"Found newer moderation request for user {callback_data.user_id}. Using that instead.")
#             user = latest_user
#             logging.info(f"Switched to newer request: user ID {user.id}, subscription time {user.subscription}")
#
#         # Сохраняем все ID записей пользователя для последующего обновления
#         user_record_ids = [record.id for record in all_user_records]
#         logging.info(f"Found {len(user_record_ids)} records for user {callback_data.user_id}: {user_record_ids}")
#     except Exception as e:
#         logging.error(f"Error checking for user records: {e}")
#         import traceback
#         logging.error(f"Traceback: {traceback.format_exc()}")
#         # Продолжаем с текущим пользователем в случае ошибки
#         user_record_ids = [user.id] if user else []
#
#     # Проверяем, достаточно ли голосов для принятия решения
#     total_admins = 1  # Устанавливаем 1 админа для принятия решения
#     total_votes = len(votes)
#     approved_votes = sum(1 for vote in votes if vote.approved)
#     rejected_votes = sum(1 for vote in votes if not vote.approved)  # Явный подсчет отклоненных голосов
#
#     any_rejected = rejected_votes > 0  # Любой голос против
#     any_approved = approved_votes > 0  # Любой голос за
#     all_voted = total_votes >= total_admins  # Все проголосовали (хотя бы один)
#     majority_voted = True  # Всегда считаем, что большинство за, так как нужен только один голос
#
#     logging.info(f"Votes for user {callback_data.user_id}: total={total_votes}, approved={approved_votes}, rejected={rejected_votes}")
#     logging.info(f"Decision criteria: any_rejected={any_rejected}, all_voted={all_voted}, majority_voted={majority_voted}")
#
#     # Принимаем решение о модерации
#     # Для одного администратора достаточно любого голоса
#     if any_rejected or any_approved:
#         # Одобряем только если нет ни одного голоса против
#         should_approve = not any_rejected
#         logging.info(f"Making decision for user {callback_data.user_id}: approved={should_approve}, approved_votes={approved_votes}, rejected_votes={rejected_votes}")
#
#         # Проверяем, изменился ли статус модерации
#         current_status = user.moderation_status if user else None
#         logging.info(f"Current moderation status for user {callback_data.user_id}: {current_status}, should be: {should_approve}")
#
#         # Всегда обновляем статус, даже если он не изменился
#         # Это решает проблему с "зависанием" модерации
#         # Отправляем уведомление администратору о результате модерации
#         status_text = "одобрен" if should_approve else "отклонен"
#         admin_notification = f"Пользователь с ID {callback_data.user_id} был {status_text}."
#         logging.info(f"CRITICAL: Attempting to send notification to admin {callback.from_user.id} with text: {admin_notification}")
#
#         try:
#             # Обновляем статус модерации пользователя
#             # Уведомление пользователю будет отправлено в функции send_notification_in_background
#             updated_user = await update_user_moderation_status(
#                 session=session,
#                 telegram_id=callback_data.user_id,
#                 status=should_approve,  # Одобряем, если нет голосов против
#                 bot=callback.bot,
#                 user_record_ids=user_record_ids  # Передаем все ID записей пользователя для обновления
#             )
#             logging.info(f"Updated moderation status for user {callback_data.user_id} to {should_approve}")
#
#             # Отправляем уведомление пользователю напрямую из этой функции
#             # Это дублирование, но оно повышает надежность системы
#             if should_approve:
#                 try:
#                     notification_text = "Модерация прошла успешно! Теперь вы можете пользоваться ботом. Отправьте /start, чтобы начать."
#                     await callback.bot.send_message(chat_id=callback_data.user_id, text=notification_text)
#                     logging.info(f"CRITICAL: Direct notification sent to user {callback_data.user_id} about approval")
#                 except Exception as e:
#                     logging.error(f"CRITICAL: Error sending direct notification to user {callback_data.user_id}: {e}")
#
#             # Отправляем уведомление администратору
#             await callback.bot.send_message(chat_id=callback.from_user.id, text=admin_notification)
#             logging.info(f"CRITICAL: Successfully sent moderation result notification to admin {callback.from_user.id}")
#         except Exception as e:
#             logging.error(f"CRITICAL: Failed to send notification to admin {callback.from_user.id}: {e}")
#             import traceback
#             logging.error(f"CRITICAL: Traceback: {traceback.format_exc()}")
#
#         # Удалено условие else, теперь всегда обновляем статус
#         # Это решает проблему с "зависанием" модерации
#     else:
#         logging.info(f"Not enough votes to make a decision for user {callback_data.user_id} yet")
#
#     # Удаляем сообщение с кнопками голосования после того, как админ проголосовал
#     try:
#         await callback.message.delete()
#         logging.info(f"Deleted moderation message for admin {callback.from_user.id} after voting")
#     except Exception as e:
#         logging.error(f"Error deleting moderation message: {e}")
#
#     # Отправляем новое сообщение администратору о его голосе
#     vote_type = "ОДОБРЕНИЕ" if callback_data.approved else "ОТКЛОНЕНИЕ"
#     try:
#         await callback.bot.send_message(
#             chat_id=callback.from_user.id,
#             text=f"Пользователь ID: {callback_data.user_id} - Вы проголосовали за {vote_type}"
#         )
#     except Exception as e:
#         logging.error(f"Error sending notification to admin {callback.from_user.id}: {e}")
#
#     # Отвечаем на callback
#     vote_text = "одобрение" if callback_data.approved else "отклонение"
#     await callback.answer(i18n.admin.text.moderation.vote_counted(vote_type=vote_text))


async def notify_admins_about_new_user(
        bot,
        user_id: int,
        username: str = None,
        fullname: str = None,
        i18n: TranslatorRunner = None
):
    """
    Уведомляет всех администраторов о новом пользователе
    """
    logging.info(f"Attempting to notify admins about new user: {user_id}, username: {username}, fullname: {fullname}")
    
    # Логируем список администраторов
    logging.info(f"Admins to notify: {Config.ADMINS_ID}")
    
    # Отправляем сообщение и клавиатуру для голосования всем админам
    for admin_id in Config.ADMINS_ID:
        try:
            logging.info(f"Sending notification to admin: {admin_id}")
            
            # Создаем клавиатуру для голосования
            keyboard = await moderation_keyboard(i18n, user_id)
            
            # Формируем текст уведомления
            notification_text = i18n.admin.text.moderation.new_user(
                user_id=user_id,
                username=username or "отсутствует",
                fullname=fullname or "отсутствует"
            )
            
            # Отправляем текстовое сообщение с кнопками
            await bot.send_message(
                chat_id=admin_id,
                text=notification_text,
                reply_markup=keyboard
            )
            logging.info(f"Successfully sent notification to admin: {admin_id}")
                
        except Exception as e:
            logging.error(f"Error notifying admin {admin_id}: {e}")
    
    # Отправляем пользователю правила группы, пока его заявка на модерации
    try:
        # Получаем правила группы
        rules_message = i18n.user.text.group_rules()
        
        # Отправляем правила без кнопки
        await send_guaranteed_message(
            bot=bot,
            user_id=user_id,
            text=rules_message,
            parse_mode='HTML'
        )
        
        logging.info(f"Successfully sent rules to user: {user_id}")
    except Exception as e:
        logging.error(f"Error sending rules to user {user_id}: {e}")
    
    logging.info("Finished notifying all admins about new user")

