import logging
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.create import add_moderation_vote
from bot.database.crud.get import get_user_tg_id, get_moderation_votes
from bot.database.crud.update import update_user_moderation_status
from bot.keyboards.admin_inline import moderation_keyboard
from bot.misc import Config
from bot.misc.callback_data import ModerationVoteCallback, RulesAcceptCallback

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

# Создаем роутер для модерации
moderation_router = Router()

# Экспортируем роутер для регистрации в основном приложении
__all__ = ["moderation_router", "notify_admins_about_new_user", "send_guaranteed_message", "process_rules_accept"]


async def send_guaranteed_message(bot, user_id: int, text: str, reply_markup=None, parse_mode=None) -> bool:
    """
    Гарантированная отправка сообщения пользователю с использованием разных методов
    :param bot: Экземпляр бота
    :param user_id: ID пользователя
    :param text: Текст сообщения
    :param reply_markup: Клавиатура (опционально)
    :param parse_mode: Режим форматирования текста (опционально)
    :return: True если удалось отправить сообщение, False в противном случае
    """
    success = False
    attempts = 0
    max_attempts = 3
    
    # Пробуем отправить сообщение несколько раз с задержкой
    while not success and attempts < max_attempts:
        attempts += 1
        
        # Метод 1: Стандартный метод send_message
        try:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            logging.info(f"CRITICAL: Message sent to user {user_id} using standard method (attempt {attempts})")
            success = True
            break
        except Exception as e:
            logging.error(f"CRITICAL: Error sending message to user {user_id} using standard method (attempt {attempts}): {e}")
            await asyncio.sleep(0.5)  # Небольшая задержка перед следующей попыткой
        
        # Метод 2: Прямой вызов API
        try:
            from aiogram.methods.send_message import SendMessage
            result = await bot(SendMessage(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode))
            logging.info(f"CRITICAL: Message sent to user {user_id} using direct API (attempt {attempts}): {result}")
            success = True
            break
        except Exception as e:
            logging.error(f"CRITICAL: Error sending message to user {user_id} using direct API (attempt {attempts}): {e}")
            await asyncio.sleep(0.5)  # Небольшая задержка перед следующей попыткой
    
    # Если все попытки не удались, пробуем отправить простое сообщение
    if not success:
        try:
            from aiogram.methods.send_message import SendMessage
            # Упрощенное сообщение
            simple_text = "Вы были одобрены. Отправьте /start для начала использования бота."
            result = await bot(SendMessage(chat_id=user_id, text=simple_text))
            logging.info(f"CRITICAL: Simple message sent to user {user_id} using direct API: {result}")
            success = True
        except Exception as e:
            logging.error(f"CRITICAL: Error sending simple message to user {user_id} using direct API: {e}")
    
    return success


async def send_notification_in_background(bot: Bot, user_id: int, status: bool):
    """
    Отправляет уведомление пользователю в фоновом режиме
    :param bot: Экземпляр бота
    :param user_id: ID пользователя
    :param status: True - одобрен, False - отклонен
    """
    try:
        # Определяем текст уведомления в зависимости от статуса
        if status:
            notification_text = "Модерация прошла успешно! Теперь вы можете пользоваться ботом."
        else:
            notification_text = "К сожалению, вам отказано в доступе к боту."
        
        # Отправляем уведомление пользователю
        success = await send_guaranteed_message(
            bot=bot,
            user_id=user_id,
            text=notification_text
        )
        
        logging.info(f"CRITICAL: Notification sent to user {user_id}, status: {status}, success: {success}")
        
        # Если пользователь был одобрен, отправляем ему дополнительное сообщение с инструкциями
        if status and success:
            welcome_message = (
                "🎉 <b>Добро пожаловать в наш клуб!</b> 🎉\n\n"
                "Теперь вы можете использовать все функции бота и получить доступ к эксклюзивному контенту.\n\n"
                "Отправьте /start, чтобы начать использование бота."
            )
            
            await send_guaranteed_message(
                bot=bot,
                user_id=user_id,
                text=welcome_message,
                parse_mode='HTML'
            )
            
            logging.info(f"CRITICAL: Welcome message sent to user {user_id}")
    
    except Exception as e:
        logging.error(f"CRITICAL: Error sending notification to user {user_id}: {e}")
        
    # Очищаем голоса модерации для этого пользователя, чтобы не перегружать базу данных
    try:
        from bot.database.crud.delete import delete_moderation_votes
        from sqlalchemy.ext.asyncio import AsyncSession
        from bot.database.main import get_session
        
        async with get_session() as session:
            session: AsyncSession
            await delete_moderation_votes(session, user_id)
            logging.info(f"CRITICAL: Moderation votes cleared for user {user_id}")
    except Exception as e:
        logging.error(f"CRITICAL: Error clearing moderation votes for user {user_id}: {e}")


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

# Регистрируем обработчик голосования за модерацию
@moderation_router.callback_query(ModerationVoteCallback.filter())
async def process_moderation_vote(
        callback: CallbackQuery,
        callback_data: ModerationVoteCallback,
        session: AsyncSession,
        i18n: TranslatorRunner
) -> None:
    """
    Обработчик голосования администратора за модерацию пользователя
    """
    logging.info(f"Admin {callback.from_user.id} voted for user {callback_data.user_id}, approved: {callback_data.approved}")
    
    # Добавляем голос в базу данных
    vote = await add_moderation_vote(
        session=session,
        user_id=callback_data.user_id,
        admin_id=callback.from_user.id,
        approved=callback_data.approved
    )
    
    if vote is None:
        logging.error(f"Error adding vote for user {callback_data.user_id} by admin {callback.from_user.id}")
        await callback.answer("Произошла ошибка при голосовании. Попробуйте еще раз.")
        return
    
    # Получаем все голоса для этого пользователя
    votes = await get_moderation_votes(session, callback_data.user_id)
    if not votes:
        logging.error(f"No votes found for user {callback_data.user_id}")
        await callback.answer("Произошла ошибка при получении голосов. Попробуйте еще раз.")
        return
    
    # Получаем пользователя из базы данных
    user = await get_user_tg_id(session, callback_data.user_id)
    if not user:
        logging.error(f"User {callback_data.user_id} not found in database")
        await callback.answer("Пользователь не найден в базе данных.")
        return
    
    # Проверяем, достаточно ли голосов для принятия решения
    total_admins = 6  # Для тестирования используем 2 админа
    total_votes = len(votes)
    approved_votes = sum(1 for vote in votes if vote.approved)
    rejected_votes = sum(1 for vote in votes if not vote.approved)  # Явный подсчет отклоненных голосов
    
    any_rejected = rejected_votes > 0
    all_voted = total_votes >= total_admins
    majority_voted = total_votes >= (total_admins // 2 + 1)  # Большинство админов проголосовало
    
    logging.info(f"Votes for user {callback_data.user_id}: total={total_votes}, approved={approved_votes}, rejected={rejected_votes}")
    logging.info(f"Decision criteria: any_rejected={any_rejected}, all_voted={all_voted}, majority_voted={majority_voted}")
    
    # Принимаем решение, если все админы проголосовали, большинство проголосовало или есть хотя бы один голос против
    if all_voted or any_rejected or majority_voted:
        # Одобряем только если нет ни одного голоса против
        should_approve = not any_rejected
        logging.info(f"Making decision for user {callback_data.user_id}: approved={should_approve}, approved_votes={approved_votes}, rejected_votes={rejected_votes}")
        
        # Обновляем статус модерации пользователя
        # Уведомление пользователю будет отправлено в функции send_notification_in_background
        user = await update_user_moderation_status(
            session=session,
            telegram_id=callback_data.user_id,
            status=should_approve,  # Одобряем, если нет голосов против
            bot=callback.bot
        )
    
    # Удаляем сообщение с кнопками голосования после того, как админ проголосовал
    try:
        await callback.message.delete()
        logging.info(f"Deleted moderation message for admin {callback.from_user.id} after voting")
    except Exception as e:
        logging.error(f"Error deleting moderation message: {e}")
    
    # Отправляем новое сообщение администратору о его голосе
    vote_type = "ОДОБРЕНИЕ" if callback_data.approved else "ОТКЛОНЕНИЕ"
    try:
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=f"Пользователь ID: {callback_data.user_id} - Вы проголосовали за {vote_type}"
        )
    except Exception as e:
        logging.error(f"Error sending notification to admin {callback.from_user.id}: {e}")
    
    # Отвечаем на callback
    vote_text = "одобрение" if callback_data.approved else "отклонение"
    await callback.answer(i18n.admin.text.moderation.vote_counted(vote_type=vote_text))


async def notify_admins_about_new_user(
        bot,
        user_id: int,
        username: str = None,
        fullname: str = None,
        i18n: TranslatorRunner = None,
        session: AsyncSession = None
):
    """
    Уведомляет всех администраторов о новом пользователе
    """
    logging.info(f"Attempting to notify admins about new user: {user_id}, username: {username}, fullname: {fullname}")
    
    # Проверяем, не был ли пользователь отклонен ранее
    if session is not None:
        user = await get_user_tg_id(session, user_id)
        if user is not None and user.moderation_status is False:
            logging.info(f"User {user_id} was previously rejected, not sending to moderation again")
            # Отправляем пользователю сообщение об отказе
            await send_guaranteed_message(
                bot=bot,
                user_id=user_id,
                text=i18n.user.text.moderation.rejected()
            )
            return
    
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

