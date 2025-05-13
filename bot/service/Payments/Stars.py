from typing import TYPE_CHECKING
import logging

from aiogram import F, Router
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from . import PaymentSystem
from bot.misc.config import Config

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

stars_router = Router()
log = logging.getLogger(__name__)


class Stars(PaymentSystem):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.TOKEN = self.STARS_TOKEN

    async def to_pay(self):
        await self.message.delete()
        amount = self.price // 2
        title = self.i18n.user.text.subscription.description.payment()
        description = self.i18n.user.text.subscription.description.amount(
            amount=self.price
        )
        prices = [LabeledPrice(label="XTR", amount=amount)]
        await self.message.answer_invoice(
            title=title,
            description=description,
            prices=prices,
            provider_token=self.TOKEN,
            payload=
            f'{self.price}'
            f':{self.period}'
            f':{self.TYPE_PAYMENT}',
            currency="XTR",
            reply_markup=await self.pay_and_check(
                str(None), self.TYPE_PAYMENT_BUTTON[2]
            )
        )
        log.info(
            f'Create payment Stars '
            f'User: ID: {self.user_id}'
        )
        return self.price


@stars_router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@stars_router.message(F.successful_payment)
async def on_successful_payment(
    message: Message,
    i18n: TranslatorRunner,
    session: AsyncSession,
):
    data = message.successful_payment.invoice_payload.split(':')
    price = int(data[0])
    period = data[1]
    payment_system = PaymentSystem(
        message=message,
        user_id=message.from_user.id,
        type_payment=data[2],
        price=price,
        period=period,
        config=Config,
        session=session,
        i18n=i18n
    )
    try:
        await payment_system.successful_payment(
            price,
            'Telegram Stars'
        )
    except BaseException as e:
        log.error(e, 'The payment period has expired')
    finally:
        log.info('exit check payment Stars')

