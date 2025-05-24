import logging

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

from bot.database.crud.get import get_user_tg_id
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
    
    # Если это не администратор, проверяем статус модерации
    if not is_admin:
        # Проверяем статус модерации пользователя
        if user is not None and user.moderation_status is False:
            # Пользователь был отклонен ранее, отправляем сообщение об отказе
            logging.info(f"User {message.from_user.id} was previously rejected, blocking access")
            await message.answer(i18n.user.text.moderation.rejected())
            return
        
        # Проверяем, нужна ли модерация
        needs_moderation = True
        if user is not None and user.moderation_status is not None:
            needs_moderation = not user.moderation_status
            logging.info(f"User {message.from_user.id} moderation status: {user.moderation_status}")
        
        if needs_moderation:
            logging.info(f"User {message.from_user.id} is not admin, sending to moderation")
            # Отправляем сообщение пользователю о ожидании модерации
            await message.answer(i18n.user.text.moderation.waiting())
            
            # Используем функцию notify_admins_about_new_user для отправки уведомлений администраторам
            logging.info(f"CRITICAL: Sending notifications to admins about new user: {message.from_user.id}")
            
            # Вызываем функцию с передачей сессии базы данных
            await notify_admins_about_new_user(
                bot=message.bot,
                user_id=message.from_user.id,
                username=message.from_user.username,
                fullname=message.from_user.full_name,
                i18n=i18n,
                session=session
            )
            
            return
        
        # Если это администратор, показываем ему меню сразу
        user = await get_user_tg_id(session, message.from_user.id)
    
    # Если пользователь уже есть в базе, проверяем статус модерации
    if not is_admin and user.moderation_status is None:
        # Если пользователь ожидает модерации и не является админом
        await message.answer(i18n.user.text.moderation.waiting())
        return
    elif not is_admin and user.moderation_status is False:
        # Если пользователь был отклонен и не является админом
        await message.answer(i18n.user.text.moderation.rejected())
        return
    
    # Если это администратор, но у него нет статуса модерации, устанавливаем его
    if is_admin and user.moderation_status is None:
        from bot.database.crud.update import update_user_moderation_status
        await update_user_moderation_status(session, message.from_user.id, True)
    
    # Если пользователь прошел модерацию, показываем основное меню
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


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