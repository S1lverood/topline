import logging
from datetime import datetime

from typing import TYPE_CHECKING
from aiogram import html
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from fluentogram import TranslatorRunner
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ChatMemberBanned, \
    ChatMemberUpdated
from aiogram_dialog import DialogManager, StartMode, ShowMode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.database.crud.create import add_moderation_vote
from bot.database.crud.get import get_user_tg_id, get_moderation_votes
from bot.database.requests import upsert_user
from bot.database.crud.update import update_user_moderation_status
from bot.handlers.admin.moderation import notify_admins_about_new_user
from bot.dialogs.user.account.dialogs import account_dialog
from bot.dialogs.user.main.dialogs import (
    start_dialog,
    faq_dialog,
    support_dialog
)
from bot.dialogs.user.subscription.dialogs import subscription_general_dialog
from bot.filters.main import IsBannedMessage, IsBannedCallback
from bot.keyboards.user_inline import back_btn
from bot.misc import Config
from bot.misc.callback_data import ReplyMessage
from bot.service.Payments.Stars import stars_router
from bot.states.state_user import StartSG, StateSubscription

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

user_router = Router()
user_router.include_routers(
    stars_router,
    start_dialog,
    faq_dialog,
    support_dialog,
    subscription_general_dialog,
    account_dialog
)
user_router.message.filter(IsBannedMessage())
user_router.callback_query.filter(IsBannedCallback())

class StateReply(StatesGroup):
    input_message = State()


@user_router.message(CommandStart())
async def process_start_command(
        message: Message,
        dialog_manager: DialogManager,
        session: AsyncSession,
        i18n: TranslatorRunner
) -> None:
    # Добавляем логирование для отладки
    logging.info(f"START COMMAND RECEIVED from user {message.from_user.id}")
    # Проверяем, является ли пользователь администратором
    is_admin = message.from_user.id in Config.ADMINS_ID
    logging.info(f"User {message.from_user.id} is_admin: {is_admin}, ADMINS_ID: {Config.ADMINS_ID}")
    
    # Проверяем, есть ли пользователь в базе данных
    user = await get_user_tg_id(session, message.from_user.id)
    logging.info(f"User database check: {user is not None}, user moderation status: {user.moderation_status if user else None}")
    
    # Если пользователь не существует или не прошел модерацию
    if user is None:
        # Если это администратор, автоматически одобряем его
        moderation_status = True if is_admin else None
        
        await upsert_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            fullname=message.from_user.full_name,
            lang_tg=message.from_user.language_code,
            moderation_status=moderation_status  # Устанавливаем статус модерации
        )
    
    # Если это не администратор, отправляем на модерацию
    if not is_admin:
        # Проверяем статус модерации пользователя
        needs_moderation = True
        if user is not None and user.moderation_status is not None:
            needs_moderation = not user.moderation_status
            logging.info(f"User {message.from_user.id} moderation status: {user.moderation_status}")
        
        if needs_moderation:
            logging.info(f"User {message.from_user.id} is not admin, sending to moderation")
            # Отправляем сообщение пользователю о ожидании модерации
            await message.answer(i18n.user.text.moderation.waiting())
            
            # Напрямую отправляем сообщения администраторам
            logging.info(f"CRITICAL: Sending direct notifications to admins about new user: {message.from_user.id}")
            
            # Выводим список администраторов для отладки
            logging.info(f"CRITICAL: Admin IDs from config: {Config.ADMINS_ID}")
            
            # Формируем расширенный текст уведомления с подробной информацией о пользователе
            user_info = [
                f"🔔 <b>Новый пользователь ожидает модерации!</b>",
                f"🔑 <b>ID:</b> <code>{message.from_user.id}</code>"
            ]
            
            # Добавляем имя пользователя, если оно есть
            if message.from_user.full_name:
                user_info.append(f"👤 <b>Имя:</b> {message.from_user.full_name}")
            
            # Добавляем имя пользователя, если оно есть
            if message.from_user.username:
                user_info.append(f"📲 <b>Username:</b> @{message.from_user.username}")
                user_info.append(f"🔗 <b>Ссылка:</b> <a href='https://t.me/{message.from_user.username}'>@{message.from_user.username}</a>")
            
            # Добавляем язык пользователя, если он есть
            if message.from_user.language_code:
                user_info.append(f"🌐 <b>Язык:</b> {message.from_user.language_code}")
                
            # Добавляем время регистрации
            from datetime import datetime
            registration_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_info.append(f"📅 <b>Время регистрации:</b> {registration_time}")
            
            # Объединяем все строки в одно сообщение
            notification_text = "\n".join(user_info)
                
            # Создаем простую клавиатуру
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            # Создаем клавиатуру с кнопками модерации
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить пользователя",
                        callback_data=f"moderationvote_{message.from_user.id}_true"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отклонить пользователя",
                        callback_data=f"moderationvote_{message.from_user.id}_false"
                    )
                ]
            ])

            # Отправляем уведомления всем администраторам
            notification_sent = False
            for admin_id in Config.ADMINS_ID:
                try:
                    logging.info(f"CRITICAL: Trying to send notification to admin {admin_id}")
                    await message.bot.send_message(
                        chat_id=admin_id,
                        text=notification_text,
                        reply_markup=keyboard
                    )
                    logging.info(f"CRITICAL: Successfully sent direct notification to admin: {admin_id}")
                    notification_sent = True
                except Exception as e:
                    logging.error(f"CRITICAL: Error sending direct notification to admin {admin_id}: {e}")
            
            # Если ни одно уведомление не было отправлено, логируем ошибку
            if not notification_sent:
                logging.error("CRITICAL: Failed to send notifications to any admin from the config list!")
            
            # Логируем результат отправки уведомлений
            status_message = "Уведомления администраторам отправлены" if notification_sent else "Произошла ошибка при отправке уведомлений"
            logging.info(f"CRITICAL: Status of notifications: {status_message}")
            
            # Пытаемся отправить правила пользователю напрямую
            try:
                # Получаем правила группы
                rules_message = i18n.user.text.group_rules()
                
                # Отправляем правила без кнопки
                await message.answer(
                    text=rules_message,
                    parse_mode='HTML'
                )
                
                logging.info(f"Successfully sent rules directly to user: {message.from_user.id}")
            except Exception as e:
                logging.error(f"Error sending rules directly to user {message.from_user.id}: {e}")
            
            
            return
        
        # Если это администратор, показываем ему меню сразу
        user = await get_user_tg_id(session, message.from_user.id)
    
    # Если пользователь уже есть в базе, проверяем статус модерации
    if not is_admin and user.moderation_status is None:
        # Если пользователь ожидает модерации и не является админом
        await message.answer(i18n.user.text.moderation.waiting())
        return
    elif not is_admin and user.moderation_status is False:
        # Если пользователь был отклонен, сбрасываем статус модерации и отправляем на повторную модерацию
        logging.info(f"User {message.from_user.id} was previously rejected, resetting moderation status")
        
        # Сбрасываем статус модерации без отправки уведомления
        # Используем прямой запрос к базе данных вместо update_user_moderation_status
        statement = select(User).filter(User.telegram_id == message.from_user.id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if user is not None:
            user.moderation_status = None
            await session.commit()
            logging.info(f"Reset moderation status for user {message.from_user.id}")
        
        # Отправляем сообщение о повторной модерации
        await message.answer(i18n.user.text.moderation.waiting())
        
        # Отправляем уведомление администраторам
        await notify_admins_about_new_user(
            message.bot,
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            i18n
        )
        
        return
    
    # Если это администратор, но у него нет статуса модерации, устанавливаем его
    if is_admin and user.moderation_status is None:
        from bot.database.crud.update import update_user_moderation_status
        await update_user_moderation_status(session, message.from_user.id, True)
    
    # Если пользователь прошел модерацию, показываем основное меню
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


@user_router.callback_query(lambda c: c.data and c.data.startswith("moderationvote_"))
async def process_moderation_vote_callback(callback: types.CallbackQuery,session:AsyncSession,i18n: TranslatorRunner):
    callback_data = callback.data
    approved = True if callback.data.split("_")[-1] == "true" else False
    user_id = int(callback.data.split("_")[-2])

    logging.info(
        f"CRITICAL: Received moderation vote callback from admin {callback.from_user.id} for user {user_id}")
    logging.info(f"CRITICAL: Vote details - approved: {approved}, callback_id: {callback.id}")
    logging.info(f"CRITICAL: Full callback data: {callback_data}")
    logging.info(f"CRITICAL: Callback message: {callback.message.message_id if callback.message else 'None'}")
    logging.info(
        f"CRITICAL: Admin info: {callback.from_user.id}, {callback.from_user.username}, {callback.from_user.full_name}")
    logging.info(f"CRITICAL: Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"CRITICAL: Bot info: {callback.bot.id}")

    try:
        logging.info(f"Admin {callback.from_user.id} voted for user {user_id}, approved: {approved}")
    except Exception as e:
        logging.error(f"CRITICAL: Error in initial logging: {e}")

    current_user = await get_user_tg_id(session, user_id)
    if current_user and current_user.moderation_status is True and approved is True:
        logging.info(f"User {user_id} is already approved, skipping moderation process")
        await callback.answer(f"Пользователь {user_id} уже одобрен")

        # Удаляем сообщение с кнопками голосования
        try:
            await callback.message.delete()
            logging.info(f"Deleted moderation message for admin {callback.from_user.id} after skipping")
        except Exception as e:
            logging.error(f"Error deleting moderation message: {e}")

        # Отправляем сообщение администратору
        try:
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=f"Пользователь ID: {user_id} уже был одобрен ранее."
            )
        except Exception as e:
            logging.error(f"Error sending notification to admin {callback.from_user.id}: {e}")

        return

    vote = await add_moderation_vote(
        session=session,
        user_id=user_id,
        admin_id=callback.from_user.id,
        approved=approved
    )

    if vote is None:
        logging.error(f"Error adding vote for user {user_id} by admin {callback.from_user.id}")
        await callback.answer("Произошла ошибка при голосовании. Попробуйте еще раз.")
        return

    try:
        logging.info(f"CRITICAL: Getting all votes for user {user_id}")
        votes = await get_moderation_votes(session, user_id)
        logging.info(f"CRITICAL: Received {len(votes)} votes for user {user_id}")

        # Проверяем и логируем каждый голос
        for i, vote in enumerate(votes):
            logging.info(f"CRITICAL: Vote {i + 1} details - admin_id: {vote.admin_id}, approved: {vote.approved}")

        if not votes:
            logging.error(f"CRITICAL: No votes found for user {user_id}")

            # Пробуем получить голос напрямую
            try:
                # Импортируем функцию для получения голоса напрямую, если она существует
                from bot.database.crud.get import get_user_moderation_vote
                direct_vote = await get_user_moderation_vote(session, user_id, callback.from_user.id)
                if direct_vote:
                    logging.info(
                        f"CRITICAL: Found direct vote for user {user_id} from admin {callback.from_user.id}")
                    votes = [direct_vote]
                else:
                    logging.error(
                        f"CRITICAL: No direct vote found for user {user_id} from admin {callback.from_user.id}")
                    await callback.answer("Произошла ошибка при получении голосов. Попробуйте еще раз.")
                    return
            except ImportError:
                # Если функция не существует, используем текущий голос
                logging.info(f"CRITICAL: get_user_moderation_vote not found, using current vote")
                votes = [vote]
    except Exception as e:
        logging.error(f"CRITICAL: Error getting votes: {e}")
        import traceback
        logging.error(f"CRITICAL: Traceback: {traceback.format_exc()}")
        await callback.answer("Произошла ошибка при получении голосов. Попробуйте еще раз.")
        return

    user = await get_user_tg_id(session, user_id)
    if not user:
        logging.error(f"User {user_id} not found in database")
        await callback.answer("Пользователь не найден в базе данных.")
        return

    try:
        from sqlalchemy import select, desc
        # Используем правильный путь импорта модели User
        from bot.database.models.main import User

        # Получаем все записи пользователя в базе данных
        # Используем поле subscription для сортировки по времени
        stmt = select(User).filter(User.telegram_id == user_id).order_by(desc(User.subscription))
        result = await session.execute(stmt)
        all_user_records = result.scalars().all()

        if not all_user_records:
            logging.error(f"No user records found for user {user_id} in database")
            await callback.answer("Пользователь не найден в базе данных.")
            return

        # Получаем самую последнюю запись пользователя
        latest_user = all_user_records[0] if all_user_records else None

        if latest_user and latest_user.id != user.id:
            logging.info(f"Found newer moderation request for user {user_id}. Using that instead.")
            user = latest_user
            logging.info(f"Switched to newer request: user ID {user.id}, subscription time {user.subscription}")

        # Сохраняем все ID записей пользователя для последующего обновления
        user_record_ids = [record.id for record in all_user_records]
        logging.info(f"Found {len(user_record_ids)} records for user {user_id}: {user_record_ids}")
    except Exception as e:
        logging.error(f"Error checking for user records: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        # Продолжаем с текущим пользователем в случае ошибки
        user_record_ids = [user.id] if user else []

    total_admins = 7  # Устанавливаем 1 админа для принятия решения
    total_votes = len(votes)
    approved_votes = sum(1 for vote in votes if vote.approved)
    rejected_votes = sum(1 for vote in votes if not vote.approved)  # Явный подсчет отклоненных голосов

    any_rejected = rejected_votes > 0  # Любой голос против
    any_approved = approved_votes > 0  # Любой голос за
    all_voted = total_votes >= total_admins  # Все проголосовали (хотя бы один)
    majority_voted = True  # Всегда считаем, что большинство за, так как нужен только один голос

    logging.info(
        f"Votes for user {user_id}: total={total_votes}, approved={approved_votes}, rejected={rejected_votes}")
    logging.info(
        f"Decision criteria: any_rejected={any_rejected}, all_voted={all_voted}, majority_voted={majority_voted}")

    if any_rejected or any_approved:
        # Одобряем только если нет ни одного голоса против
        should_approve = not any_rejected
        logging.info(
            f"Making decision for user {user_id}: approved={should_approve}, approved_votes={approved_votes}, rejected_votes={rejected_votes}")

        # Проверяем, изменился ли статус модерации
        current_status = user.moderation_status if user else None
        logging.info(
            f"Current moderation status for user {user_id}: {current_status}, should be: {should_approve}")

        # Всегда обновляем статус, даже если он не изменился
        # Это решает проблему с "зависанием" модерации
        # Отправляем уведомление администратору о результате модерации
        status_text = "одобрен" if should_approve else "отклонен"
        admin_notification = f"Пользователь с ID {user_id} был {status_text}."
        logging.info(
            f"CRITICAL: Attempting to send notification to admin {callback.from_user.id} with text: {admin_notification}")

        try:
            # Обновляем статус модерации пользователя
            # Уведомление пользователю будет отправлено в функции send_notification_in_background
            updated_user = await update_user_moderation_status(
                session=session,
                telegram_id=user_id,
                status=should_approve,  # Одобряем, если нет голосов против
                bot=callback.bot,
                user_record_ids=user_record_ids  # Передаем все ID записей пользователя для обновления
            )
            logging.info(f"Updated moderation status for user {user_id} to {should_approve}")

            # Отправляем уведомление пользователю напрямую из этой функции
            # Это дублирование, но оно повышает надежность системы
            # if should_approve:
            #     try:
            #         # notification_text = "Модерация прошла успешно! Теперь вы можете пользоваться ботом. Отправьте /start, чтобы начать."
            #         await callback.bot.send_message(chat_id=user_id, text=notification_text)
            #         logging.info(f"CRITICAL: Direct notification sent to user {user_id} about approval")
            #     except Exception as e:
            #         logging.error(f"CRITICAL: Error sending direct notification to user {user_id}: {e}")

            # Отправляем уведомление администратору
            await callback.bot.send_message(chat_id=callback.from_user.id, text=admin_notification)
            logging.info(f"CRITICAL: Successfully sent moderation result notification to admin {callback.from_user.id}")
        except Exception as e:
            logging.error(f"CRITICAL: Failed to send notification to admin {callback.from_user.id}: {e}")
            import traceback
            logging.error(f"CRITICAL: Traceback: {traceback.format_exc()}")

        # Удалено условие else, теперь всегда обновляем статус
        # Это решает проблему с "зависанием" модерации
    else:
        logging.info(f"Not enough votes to make a decision for user {user_id} yet")

    # Удаляем сообщение с кнопками голосования после того, как админ проголосовал
    try:
        await callback.message.delete()
        logging.info(f"Deleted moderation message for admin {callback.from_user.id} after voting")
    except Exception as e:
        logging.error(f"Error deleting moderation message: {e}")
    # Теперь вы можете
    # Отправляем новое сообщение администратору о его голосе
    vote_type = "ОДОБРЕНИЕ" if approved else "ОТКЛОНЕНИЕ"
    try:
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=f"Пользователь ID: {user_id} - Вы проголосовали за {vote_type}"
        )
    except Exception as e:
        logging.error(f"Error sending notification to admin {callback.from_user.id}: {e}")

    # Отвечаем на callback
    vote_text = "одобрение" if approved else "отклонение"
    await callback.answer(i18n.admin.text.moderation.vote_counted(vote_type=vote_text))

@user_router.callback_query(F.data == 'answer_back_general_menu_btn')
async def process_start_command(
        callback: CallbackQuery,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(
        state=StartSG.start,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )
    await callback.answer()


@user_router.callback_query(F.data == 'subscribe_btn')
async def process_start_command(
        callback: CallbackQuery,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(
        state=StateSubscription.subscription_general,
        mode=StartMode.RESET_STACK,
    )
    await callback.answer()


@user_router.chat_join_request()
async def process_start_command(
        update: types.ChatJoinRequest,
        session: AsyncSession,
        i18n: TranslatorRunner,
        dialog_manager: DialogManager
) -> None:
    user = await get_user_tg_id(session, update.from_user.id)
    if user is None:
        await upsert_user(
            session=session,
            telegram_id=update.from_user.id,
            username=update.from_user.username,
            fullname=update.from_user.full_name,
            lang_tg=update.from_user.language_code
        )
        user = await get_user_tg_id(session, update.from_user.id)

    if user.blocked:
        return

    if user.status_subscription:
        await update.approve()
        await update.bot.send_message(
            chat_id=update.from_user.id,
            text=i18n.user.text.subscription.approv(),
        )
    else:
        await update.bot.send_message(
            chat_id=update.from_user.id,
            text=i18n.user.text.subscription.approve.none(),
            reply_markup=await back_btn(i18n)
        )


@user_router.callback_query(ReplyMessage.filter())
async def reply_message(
        callback_query: CallbackQuery,
        i18n: TranslatorRunner,
        dialog_manager: DialogManager,
        state: FSMContext,
        callback_data: ReplyMessage
) -> None:
    await callback_query.message.answer(
        i18n.admin.text.support.reply()
    )
    await state.update_data(
        id_client=callback_data.id_client,
        message_id = callback_query.message.message_id
    )
    await state.set_state(StateReply.input_message)
    await callback_query.answer()


@user_router.message(StateReply.input_message)
async def reply_message(
        message: Message,
        i18n: TranslatorRunner,
        dialog_manager: DialogManager,
        state: FSMContext,
) -> None:
    data = await state.get_data()
    await message.bot.send_message(
        data['id_client'],
        i18n.user.text.support.reply()
    )
    try:
        await message.send_copy(data['id_client'])
        await message.bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=data['message_id']
        )
        for admin in Config.ADMINS_ID:
            if admin == message.from_user.id:
                continue
            await message.bot.send_message(
                admin,
                text=i18n.admin.text.support.reply.all(
                    admin_name=html.quote(message.from_user.full_name),
                    user_id=str(data['id_client'])
                )
            )
            await message.send_copy(admin)

    except Exception as e:
        logging.exception(e)
    await state.clear()