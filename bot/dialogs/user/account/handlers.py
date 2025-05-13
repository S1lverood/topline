from typing import TYPE_CHECKING

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.get import get_payments_user
from bot.service.service import send_document

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def button_payments_user(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    payments = await get_payments_user(session, callback.from_user.id)
    if len(payments) <= 15:
        await dialog_manager.next()
        return
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    account_payment = i18n.user.text.account.list_payment_text()
    for payment in payments:
        date = payment.date_registered.strftime('%d.%m.%Y %H:%M')
        amount = payment.amount
        text = (
            f'\n➖➖➖➖➖➖➖➖➖➖➖➖'
            f'\n{i18n.user.text.account.list_payment_text.date(date=date)}'
            f'\n{i18n.user.text.account.list_payment_text.amount(amount=amount)}'
        )
        account_payment += text
    await send_document(
        callback.message,
        account_payment,
        'Your payments',
        i18n.user.text.account.list_payment_file()
    )
    await callback.answer()
