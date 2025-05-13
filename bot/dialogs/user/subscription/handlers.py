import logging
import re
from typing import TYPE_CHECKING

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.misc import Config
from bot.service.Payments import all_payments, KassaSmart
from bot.states.state_user import StateSubscription

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def button_choosing_month(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data.update(method_payment=button.widget_id)
    await dialog_manager.next()


async def month_selection(
        callback: CallbackQuery,
        widget: Select,
        dialog_manager: DialogManager,
        item_id: str):
    dialog_manager.dialog_data.update(month=item_id)
    await dialog_manager.next()



async def payment_selection(
        callback: CallbackQuery,
        widget: Select,
        dialog_manager: DialogManager,
        item_id: str):
    if item_id == 'None':
        return
    dialog_manager.dialog_data.update(payment=item_id)
    if item_id == KassaSmart.__name__:
        await dialog_manager.switch_to(StateSubscription.input_email)
        return
    dialog_manager.show_mode = ShowMode.NO_UPDATE
    data = dialog_manager.dialog_data.copy()
    period = data.get('month').split(':')[0]
    price = int(data.get('month').split(':')[1])
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    state: FSMContext = dialog_manager.middleware_data.get('state')
    await state.clear()
    await callback.answer()
    await payment(
        item_id,
        callback.message,
        callback.from_user.id,
        price,
        period,
        Config.TYPE_PAYMENT.get(0),
        i18n,
        session
    )


async def input_email_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    email = message.text.strip()
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    if not email_pattern.match(email):
        await message.answer(i18n.user.text.subscription.input.email.error())
        return
    dialog_manager.show_mode = ShowMode.NO_UPDATE
    data = dialog_manager.dialog_data.copy()
    period = data.get('month').split(':')[0]
    price = int(data.get('month').split(':')[1])
    payment_str = data.get('payment')
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    await payment(
        payment_str,
        message,
        message.from_user.id,
        price,
        period,
        Config.TYPE_PAYMENT.get(0),
        i18n,
        session,
        email=email
    )


async def payment(
    payment_str,
    message,
    user_id,
    price,
    period,
    type_payment,
    i18n,
    session,
    email=None
):
    payment_system = all_payments.get(payment_str)(
        message=message,
        user_id=user_id,
        price=price,
        period=period,
        type_payment=type_payment,
        config=Config,
        i18n=i18n,
        session=session,
        email=email
    )
    await payment_system.to_pay()

