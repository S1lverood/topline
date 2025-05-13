import asyncio
import logging
import uuid

from cryptomus import Client
from cryptomus.payments import Payment
from cryptomus.payouts import Payout

from . import PaymentSystem

log = logging.getLogger(__name__)


class Cryptomus(PaymentSystem):
    PAYMENT: Payment
    ID: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.PAYMENT = Client.payment(
            self.CRYPTOMUS_KEY_PAYMENT,
            self.CRYPTOMUS_KEY_UUID
        )

    async def create_id(self):
        self.ID = str(uuid.uuid4())

    async def new_payment(self):
        return {
            'amount': str(self.price),
            'currency': 'RUB',
            'order_id': self.ID,
            'lifetime': self.CHECK_PERIOD - 30,
        }

    async def check_pay_wallet(self, uuid_order):
        tic = 0
        while tic < self.CHECK_PERIOD:
            order_info = self.PAYMENT.info(
                {'uuid': uuid_order}
            )
            if order_info['status'] == "paid":
                await self.successful_payment(
                    self.price,
                    'Cryptomus'
                )
                return
            tic += self.STEP
            await asyncio.sleep(self.STEP)
            if self.CHECK_PERIOD - tic <= self.TIME_DELETE:
                await self.delete_pay_button('Cryptomus')
        return

    async def to_pay(self):
        await self.create_id()
        data = await self.new_payment()
        result = self.PAYMENT.create(data)
        await self.pay_button(result['url'])
        log.info(
            f'Create payment link Cryptomus '
            f'User: ID: {self.user_id}'
        )
        try:
            await self.check_pay_wallet(result['uuid'])
        except BaseException as e:
            log.error(e, 'The payment period has expired')
        finally:
            await self.delete_pay_button('Cryptomus')
            log.info('exit check payment Cryptomus')

    def __str__(self):
        return 'Платежная система Cryptomus'
