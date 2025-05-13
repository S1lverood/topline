import logging
from typing import TYPE_CHECKING

from aiogram.types import (
    FSInputFile,
    Message,
    InlineKeyboardMarkup,
    WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from fluentogram import TranslatorRunner

from bot.database.crud.create import add_payment
from bot.database.crud.update import user_subscribe
from bot.keyboards.user_inline import link_chanel
from bot.misc import Config

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

from bot.misc.config import ConfigBot

log = logging.getLogger(__name__)


class PaymentSystem:
    TOKEN: str
    CHECK_PERIOD = 50 * 60
    STEP = 5
    TIME_DELETE: int = 5 * 60
    TYPE_PAYMENT: str
    KEY_ID: int
    MESSAGE_ID_PAYMENT: Message = None
    CONFIG: ConfigBot
    i18n: TranslatorRunner
    TYPE_PAYMENT_BUTTON = ['default', 'webapp', 'default_tg']
    SESSION: AsyncSession
    #TOKEN PAYMENT
    CRYPTO_BOT_API: str = None
    CRYPTOMUS_KEY_PAYMENT: str = None
    CRYPTOMUS_KEY_UUID: str = None
    YOOKASSA_SHOP_ID: str = None
    YOOKASSA_SECRET_KEY: str = None
    LAVA_TOKEN_SECRET: str = None
    LAVA_PROJECT_ID: str = None
    STARS_TOKEN: str = None
    TINKOFF_TERMINAL: str = None
    TINKOFF_SECRET: str = None
    YOOMONEY_TOKEN: str = None
    YOOMONEY_WALLET: str = None

    def __init__(self, **kwargs):
        self.message: Message = kwargs['message']
        self.user_id = kwargs['user_id']
        self.price = kwargs['price']
        self.period = kwargs['period']
        self.TYPE_PAYMENT = kwargs['type_payment']
        self.CONFIG = kwargs['config']
        self.i18n = kwargs['i18n']
        self.SESSION = kwargs['session']

        self.CRYPTO_BOT_API = self.CONFIG.CRYPTO_BOT_API
        self.CRYPTOMUS_KEY_PAYMENT = self.CONFIG.CRYPTOMUS_KEY
        self.CRYPTOMUS_KEY_UUID = self.CONFIG.CRYPTOMUS_UUID
        self.YOOKASSA_SHOP_ID = self.CONFIG.YOOKASSA_SHOP_ID
        self.YOOKASSA_SECRET_KEY = self.CONFIG.YOOKASSA_SECRET_KEY
        self.LAVA_TOKEN_SECRET = self.CONFIG.LAVA_TOKEN_SECRET
        self.LAVA_PROJECT_ID = self.CONFIG.LAVA_ID_PROJECT
        self.STARS_TOKEN = self.CONFIG.TOKEN_STARS
        self.TINKOFF_TERMINAL = self.CONFIG.TINKOFF_TERMINAL
        self.TINKOFF_SECRET = self.CONFIG.TINKOFF_SECRET
        self.YOOMONEY_TOKEN = self.CONFIG.YOOMONEY_TOKEN
        self.YOOMONEY_WALLET = self.CONFIG.YOOMONEY_WALLET

    async def to_pay(self):
        raise NotImplementedError()

    async def pay_button(
            self,
            link_pay='',
            delete=True,
            type_payment=TYPE_PAYMENT_BUTTON[0]
    ):
        if delete:
            try:
                await self.message.delete()
            except Exception:
                log.info('error delete message')
        self.MESSAGE_ID_PAYMENT = await self.message.answer_photo(
            FSInputFile('bot/img/payment.png'),
            self.i18n.user.text.subscription.description.amount(
                amount=self.price
            ),
            reply_markup=await self.pay_and_check(link_pay, type_payment)
        )

    async def pay_and_check(
            self,
            link_invoice: str,
            type_payment
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        text = self.i18n.user.text.subscription.description.payment()
        if type_payment == 'default':
            kb.button(text=text, url=link_invoice)
        elif type_payment == 'webapp':
            kb.button(
                text=text,
                web_app=WebAppInfo(url=link_invoice)
            )
        elif type_payment == 'default_tg':
            kb.button(text=text, pay=True)
        else:
            raise ValueError(f'Not found payment type - {type_payment}')
        kb.button(
            text=self.i18n.user.button.back.general(),
            callback_data='answer_back_general_menu_btn',
        )
        kb.adjust(1)
        return kb.as_markup()


    async def delete_pay_button(self, name_payment):
        if self.MESSAGE_ID_PAYMENT is not None:
            try:
                await self.message.bot.delete_message(
                    self.user_id,
                    self.MESSAGE_ID_PAYMENT.message_id
                )
                log.info(
                    f'user ID: {self.user_id}'
                    f' delete payment {self.price} RUB '
                    f'Payment - {name_payment}'
                )
            except Exception as e:
                log.error(
                    f'error delete pay button {e} payment {name_payment}'
                )
            finally:
                self.MESSAGE_ID_PAYMENT = None

    async def successful_payment(
            self, total_amount, name_payment, id_payment=None
    ):
        log.info(
            f'user ID: {self.user_id}'
            f' success payment {total_amount} RUB Payment - {name_payment}'
        )
        await add_payment(
            session=self.SESSION,
            telegram_id=self.user_id,
            deposit=total_amount,
            payment_system=name_payment,
            id_payment=id_payment,
            period=self.period
        )
        await user_subscribe(self.SESSION, self.user_id, self.period)
        await self.message.answer_photo(
            photo=FSInputFile('bot/img/sub.png'),
            caption=self.i18n.user.text.subscription.link(
                link=Config.LINK_CHANNEL
            ),
            reply_markup=await link_chanel(
                i18n=self.i18n,
                link_channel=Config.LINK_CHANNEL
            )
        )
