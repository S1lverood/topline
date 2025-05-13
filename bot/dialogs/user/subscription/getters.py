from typing import TYPE_CHECKING

from aiogram.types import User
from fluentogram import TranslatorRunner

from bot.misc import Config
from bot.service.Payments import get_active_payment_system

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

async def get_sub_general_menu(
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
):
    return dict(
        subscription_status=i18n.user.text.subscription.active.no(),
        subscription_pay=i18n.user.button.subscription.pay(),
        subscription_pay_friend=i18n.user.button.subscription.pay.friend(),
        button_subscription_link=i18n.user.button.subscription.link(),
        subscription_link=i18n.user.link.subscription(),
        back=i18n.user.button.back(),
    )

async def get_sub_month(
    i18n: TranslatorRunner,
    **kwargs,
):
    month = []
    for i in range(len(Config.PERIOD)):
        type_period = Config.PERIOD[i].split('.')
        period = i18n.user.text.subscription.mon()
        match type_period[0]:
            case 'min':
                period = i18n.user.text.subscription.minute()
            case 'day':
                period = i18n.user.text.subscription.day()
            case 'year':
                period = i18n.user.text.subscription.year()

        text = i18n.user.button.subscription.month(
            count=type_period[1],
            period=period,
            amount=Config.AMOUNT[i]
        )
        month_id = f'{Config.PERIOD[i]}:{Config.AMOUNT[i]}'
        month.append(
            (text, month_id)
        )
    return dict(
        choosing_time=i18n.user.text.subscription.month(),
        month=month,
        back=i18n.user.button.back(),
    )

async def get_sub_payments(
    i18n: TranslatorRunner,
    **kwargs,
):
    payments = await get_active_payment_system(i18n)
    return dict(
        choosing_payment=i18n.user.text.subscription.month(),
        payments=payments,
        back=i18n.user.button.back(),
    )

async def get_input_email(
    i18n: TranslatorRunner,
    **kwargs,
):
    return dict(
        input_email_message=i18n.user.text.subscription.input.email(),
        back=i18n.user.button.back.general(),
    )