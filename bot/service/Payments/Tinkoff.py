import asyncio
import logging
import uuid

from tinkoff_acquiring import TinkoffAcquiringAPIClient, TinkoffAPIException

from . import PaymentSystem

log = logging.getLogger(__name__)


class TinkoffPay(PaymentSystem):
    CLIENT: TinkoffAcquiringAPIClient

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.CLIENT = TinkoffAcquiringAPIClient(
            self.TINKOFF_TERMINAL,
            self.TINKOFF_SECRET
        )

    async def new_order(self):
        return await self.CLIENT.init_payment(
            amount=float(self.price),
            order_id=str(uuid.uuid4()),
            description=self.i18n.user.text.subscription.description.payment()
        )

    async def check_pay_wallet(self, payment_id):
        tic = 0
        while tic < self.CHECK_PERIOD:
            order_preview = await self.CLIENT.get_payment_state(payment_id)
            if order_preview['Status'] == "CONFIRMED":
                await self.successful_payment(
                    self.price,
                    'TinkoffPay'
                )
                return
            tic += self.STEP
            await asyncio.sleep(self.STEP)
            if self.CHECK_PERIOD - tic <= self.TIME_DELETE:
                await self.delete_pay_button('TinkoffPay')
        return

    async def to_pay(self):
        response = await self.new_order()
        payment_id = response['PaymentId']
        link_pay = response['PaymentURL']
        await self.pay_button(link_pay)
        log.info(
            f'Create payment link TinkoffPay '
            f'User: ID: {self.user_id}'
        )
        try:
            await self.check_pay_wallet(payment_id)
        except BaseException as e:
            log.error(e, 'The payment period has expired')
        finally:
            await self.delete_pay_button('TinkoffPay')
            log.info('exit check payment TinkoffPay')

    def __str__(self):
        return 'Платежная система TinkoffPay'
