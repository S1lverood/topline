import asyncio
import logging
import random
import uuid

from aiohttp import client_exceptions
from yoomoney_async import Quickpay, Client

from . import PaymentSystem

log = logging.getLogger(__name__)


class YooMoney(PaymentSystem):
    CHECK_ID: str = None
    ID: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.TOKEN = self.YOOMONEY_TOKEN
        self.TOKEN_WALLET = self.YOOMONEY_WALLET

    async def create(self):
        self.ID = str(uuid.uuid4())
        
        # Добавляем комиссию 3.5% к цене
        commission_rate = 0.035  # 3.5%
        commission_amount = self.price * commission_rate
        self.price = round(self.price + commission_amount)  # Округляем до целого числа
        log.info(f"YooMoney: added commission 3.5%, new price: {self.price}")

    async def check_payment(self):
        client = Client(self.TOKEN)
        tic = 0
        while tic < self.CHECK_PERIOD:
            try:
                history = await client.operation_history(label=self.ID)
                for operation in history.operations:
                    # Учитываем, что цена уже включает комиссию 3.5%
                    await self.successful_payment(self.price, 'YooMoney (включая комиссию 3.5%)')
                    return
            except client_exceptions.ClientOSError as e:
                await asyncio.sleep(self.STEP + random.randint(0, 3))
                log.info('Error 104  YooMoney -- OK')
                continue
            tic += self.STEP
            await asyncio.sleep(self.STEP)
            if self.CHECK_PERIOD - tic <= self.TIME_DELETE:
                await self.delete_pay_button('YooMoney')
        return

    async def invoice(self):
        quick_pay = await Quickpay(
            receiver=self.TOKEN_WALLET,
            quickpay_form="shop",
            targets='Deposit balance',
            paymentType="SB",
            sum=self.price,
            label=self.ID
        ).start()
        return quick_pay.base_url

    async def to_pay(self):
        await self.create()
        link_invoice = await self.invoice()
        await self.pay_button(link_invoice)
        log.info(
            f'Create payment link YooMoney '
            f'User: {self.user_id} - {self.price} RUB'
        )
        try:
            await self.check_payment()
        except BaseException as e:
            log.error(e, 'The payment period has expired')
        finally:
            await self.delete_pay_button('YooMoney')
            log.info('exit check payment YooMoney')

    def __str__(self):
        return 'Платежная система YooMoney'
