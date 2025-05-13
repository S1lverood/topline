from typing import TYPE_CHECKING

from aiogram import html
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from bot.keyboards.admin_inline import reply_message
from bot.service.service import send_admin
from bot.states.state_user import (
    StartSG,
    StateFAQ,
    StateSupport,
    StateSubscription, StateAccount, StateAdmin
)

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def button_subscribe_click(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(
        state=StateSubscription.subscription_general,
        mode=StartMode.RESET_STACK
    )


async def button_account_click(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(
        state=StateAccount.account_general,
        mode=StartMode.RESET_STACK
    )


async def button_support_click(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(
        state=StateSupport.support_menu,
        mode=StartMode.RESET_STACK
    )


async def button_faq_click(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(state=StateFAQ.faq, mode=StartMode.RESET_STACK)


async def button_admin_click(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    await dialog_manager.start(
        state=StateAdmin.admin_menu,
        mode=StartMode.RESET_STACK
    )


async def back_general(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


async def button_next(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
):
    await dialog_manager.next()


async def button_back(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
):
    await dialog_manager.back()


async def button_done(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
):
    await dialog_manager.done()


async def support_input_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    await send_admin(
        message,
        text=i18n.admin.text.support(
            full_name=html.quote(message.from_user.full_name),
            user_id=str(message.from_user.id),
        ),
    )
    result = await send_admin(
        message,
        reply_markup=await reply_message(i18n, message.from_user.id)
    )
    if result:
        await message.answer(i18n.user.text.support.input.succes())
    else:
        await message.answer(i18n.user.text.support.input.error())
