from typing import TYPE_CHECKING

from aiogram import html, Bot
from aiogram.enums import ContentType
from aiogram.types import User
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.get import get_user_tg_id, get_payments_user
from bot.misc import Config

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def get_account_menu(
    i18n: TranslatorRunner,
    event_from_user: User,
    session: AsyncSession,
    bot: Bot,
    **kwargs,
):
    profile_pictures = await bot.get_user_profile_photos(
        user_id=event_from_user.id,
        limit=1
    )
    if len(profile_pictures.photos) != 0:
        images = MediaAttachment(
            ContentType.PHOTO,
            file_id=MediaId(
                dict((profile_pictures.photos[0][0])).get('file_id')
            ),
        )
    else:
        images = MediaAttachment(
            ContentType.PHOTO,
            path='bot/img/logo.png'
        )
    user = await get_user_tg_id(session, event_from_user.id)
    payments = await get_payments_user(session, event_from_user.id)
    if len(payments) != 0:
        date_amount = (
            f'{payments[0].date_registered.strftime("%d.%m.%Y %H:%M")} '
            f'{payments[0].amount}₽'
        )
    else:
        date_amount = i18n.user.text.account.no.payment()
    if user.status_subscription:
        time_sub = user.subscription.strftime('%d.%m.%Y %H:%M')
    else:
        time_sub = i18n.user.text.account.no.subscription()

    account_text = i18n.user.text.account.info(
        full_name=html.quote(event_from_user.full_name),
        id_user=str(event_from_user.id),
        date_sub=time_sub,
        date_amount=date_amount,
        date_registred=user.date_registered.strftime('%d.%m.%Y')
    )
    return dict(
        account_text=account_text,
        link_channel_text=i18n.user.button.open.channel.v2(),
        link_channel=Config.LINK_CHANNEL,
        status_subscription=user.status_subscription,
        images=images,
        account_payment=i18n.user.button.account.payment(),
        back=i18n.user.button.back(),
    )

async def get_payments_user_getter(
    i18n: TranslatorRunner,
    session: AsyncSession,
    event_from_user: User,
    **kwargs,
) -> dict[str, str]:
    payments = await get_payments_user(session, event_from_user.id)
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
    if len(payments) == 0:
        account_payment += f'\n{i18n.user.text.account.list_payment_text.no()}'
    return dict(
        list_payment_text=account_payment,
        back=i18n.user.button.back(),
    )