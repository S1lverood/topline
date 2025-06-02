import asyncio
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING

from aiogram import html
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Calendar
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.get import (
    get_all_user,
    get_users_status,
    get_payments,
    get_user_tg_id,
    get_payments_user
)
from bot.database.crud.update import user_swith_ban, user_new_subscribe
from bot.keyboards.user_inline import link_chanel
from bot.misc import Config
from bot.service.loop import end_subscription
from bot.service.service import send_document, check_number_int
from bot.states.state_user import  StateAdmin

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def back_admin_menu(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(StateAdmin.admin_menu)


async def button_milling(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(StateAdmin.milling_menu)


async def button_statistic(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(StateAdmin.statistics_menu)


async def button_user_control_input(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(StateAdmin.user_control_input)


async def button_milling_group(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data.update(type_milling=button.widget_id)
    await dialog_manager.switch_to(StateAdmin.milling_active)


async def milling_input_handler(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    data = dialog_manager.dialog_data.copy()
    type_milling = data.get('type_milling')
    message_wait = await message.answer(
        i18n.admin.text.admin_menu.milling.wait(percent=0)
    )
    if type_milling == 'subscribe_users':
        users_milling = await get_users_status(session)
    elif type_milling == 'not_subscribe_users':
        users_milling = await get_users_status(session, False)
    else:
        users_milling = await get_all_user(session)

    total_users = len(users_milling)
    suc_count = 0
    not_suc_count = 0

    for idx, user in enumerate(users_milling):
        try:
            await message.send_copy(user.telegram_id)
            suc_count += 1
        except Exception as e:
            logging.info(f'user {user.telegram_id} blocked bot')
            not_suc_count += 1
        progress = ((idx + 1) / total_users) * 100
        if progress % 20 == 0:
            await message_wait.edit_text(
                i18n.admin.text.admin_menu.milling.wait(percent=int(progress))
            )
        await asyncio.sleep(0.03)
    await message_wait.edit_text(
        i18n.admin.text.admin_menu.milling.result(
            all_count=total_users,
            suc_count=suc_count,
            not_suc_count=not_suc_count
        )
    )


async def show_payments(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    id_user = dialog_manager.dialog_data.get('id_user')
    if button.widget_id == 'payments_user' and id_user is not None:
        payments = await get_payments_user(session, id_user)
        name_document = 'Payments user'
        caption = i18n.admin.text.admin_menu.statistic.payment.caption.user()
    else:
        payments = await get_payments(session)
        name_document = 'Payments'
        caption = i18n.admin.text.admin_menu.statistic.payment.caption()
    text = ''
    number = 1
    for payment in payments:
        text += i18n.admin.text.admin_menu.statistic.payment(
            number=number,
            user_name=payment.payment_id.username,
            user_id=str(payment.user),
            payment_system=payment.payment_system,
            amount=payment.amount,
            date=payment.date_registered.strftime("%d.%m.%Y %H:%M")
        ) + '\n'
        number += 1
    if text == '':
        await callback.answer(
            i18n.admin.text.admin_menu.statistic.payment.not_caption()
        )
        return
    await send_document(callback.message, text, name_document=name_document,
                        caption=caption)


async def show_users(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    if button.widget_id == 'all_users':
        users = await get_all_user(session)
        name_document = 'All Users'
        caption = i18n.admin.text.admin_menu.statistic.all_users.caption()
    else:
        users = await get_users_status(session)
        name_document = 'Active Users'
        caption = i18n.admin.text.admin_menu.statistic.active.caption()
    text = ''
    number = 1
    for user in users:
        if user.status_subscription:
            sub = user.subscription.strftime('%d.%m.%Y %H:%M') + '✅'
        else:
            sub = '❌'
        # Проверяем, что lang_tg не None, если None, используем пустую строку
        lang_tg = user.lang_tg if user.lang_tg is not None else ''
        text += i18n.admin.text.admin_menu.statistic.all_users(
            number=number,
            fullname=user.fullname,
            username=user.username,
            telegram_id=str(user.telegram_id),
            lang=lang_tg,  # Используем проверенное значение
            date=user.date_registered.strftime("%d.%m.%Y %H:%M"),
            subscription=sub
        ) + '\n'
        number += 1
    if text == '':
        await callback.message.answer(
            i18n.admin.text.admin_menu.statistic.all_users.not_caption()
        )
        return
    await send_document(callback.message, text, name_document=name_document,
                        caption=caption)


async def input_id_user_handler(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    dialog_manager.show_mode = ShowMode.NO_UPDATE
    text = message.text
    try:
        id_user = await check_number_int(message, i18n, text)
    except ValueError:
        return
    user = await get_user_tg_id(session, id_user)
    if user is None:
        await message.answer(i18n.admin.text.admin_menu.user_control.not_user())
        return
    dialog_manager.show_mode = ShowMode.AUTO
    dialog_manager.dialog_data.update(
        id_user=id_user,
    )
    await dialog_manager.switch_to(StateAdmin.user_control_menu)



async def ban_unban_user_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    id_user = dialog_manager.dialog_data.get('id_user')
    value = await user_swith_ban(session, id_user)
    if value is None:
        await callback.message.answer(
            i18n.admin.error.user_not_found()
        )
        return
    if value:
        alert = i18n.admin.text.admin_menu.user_control.account.un_ban.alert()
        await callback.bot.unban_chat_member(
            chat_id=Config.ID_CHANNEL,
            user_id=id_user,
        )
    else:
        alert = i18n.admin.text.admin_menu.user_control.account.ban.alert()
        await callback.bot.ban_chat_member(
            chat_id=Config.ID_CHANNEL,
            user_id=id_user,
        )
    await callback.answer(alert)
    await dialog_manager.switch_to(StateAdmin.user_control_menu)

async def back_user_control_handler(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    id_user = dialog_manager.dialog_data.get('id_user')
    if id_user is None:
        await dialog_manager.switch_to(StateAdmin.admin_menu)
    else:
        await dialog_manager.switch_to(StateAdmin.user_control_menu)


async def message_user_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(StateAdmin.user_control_message)


async def input_message_user_handler(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    id_user = dialog_manager.dialog_data.get('id_user')
    try:
        await message.bot.send_message(
            id_user,
            i18n.admin.text.admin_menu.user_control.account.message_admin()
        )
        await message.send_copy(id_user)
        await message.answer(
            i18n.admin.text.message.success()
        )
    except Exception as e:
        logging.info(f'user blocked bot {e}')
        await message.answer(
            i18n.user.error.message.user_block_bot()
        )

async def add_time_user_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(StateAdmin.user_control_add_time)


async def ban_user_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    id_user = dialog_manager.dialog_data.get('id_user')
    
    # Получаем пользователя
    user = await get_user_tg_id(session, id_user)
    if user is None:
        await callback.message.answer(
            i18n.admin.error.user_not_found()
        )
        return
    
    # Если пользователь еще не заблокирован, блокируем его
    if not user.blocked:
        # Устанавливаем флаг blocked в True
        await user_swith_ban(session, id_user)
        # Баним пользователя в канале
        await callback.bot.ban_chat_member(
            chat_id=Config.ID_CHANNEL,
            user_id=id_user,
        )
        # Отправляем уведомление администратору
        await callback.answer(i18n.admin.text.admin_menu.user_control.account.ban.alert())
        # Отправляем сообщение пользователю о блокировке
        try:
            await callback.bot.send_message(
                id_user,
                i18n.user.text.account.banned()
            )
        except Exception as e:
            logging.info(f'Не удалось отправить сообщение о бане пользователю {id_user}: {e}')
    else:
        # Если пользователь уже заблокирован, сообщаем об этом
        await callback.answer(i18n.admin.text.admin_menu.user_control.account.already_banned())
    
    # Возвращаемся в меню управления пользователем
    await dialog_manager.switch_to(StateAdmin.user_control_menu)


async def on_date_selected(
        callback: CallbackQuery,
        widget: Calendar,
        dialog_manager: DialogManager,
        selected_date: date
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    id_user = dialog_manager.dialog_data.get('id_user')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    user = await get_user_tg_id(session, id_user)
    if selected_date < datetime.now().date():
        await end_subscription(user, i18n, session, callback.bot)
        await callback.message.answer(
            i18n.admin.text.account.add_time.reset.time(
                full_name=html.quote(user.fullname),
            )
        )
    else:
        user = await user_new_subscribe(
            session, user.telegram_id, selected_date
        )
        await callback.bot.send_message(
            user.telegram_id,
            i18n.user.text.subscription.add.time(
                new_date=user.subscription.strftime('%d.%m.%Y %H:%M'),
                link=Config.LINK_CHANNEL
            ),
            reply_markup=await link_chanel(i18n, Config.LINK_CHANNEL)
        )
        await callback.message.answer(
            i18n.admin.text.account.add_time.new.time(
                full_name=html.quote(user.fullname),
                new_date=user.subscription.strftime('%d.%m.%Y %H:%M')
            )
        )
    await dialog_manager.switch_to(
        StateAdmin.user_control_menu,
        ShowMode.DELETE_AND_SEND
    )
