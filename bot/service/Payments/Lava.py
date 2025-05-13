import asyncio
import logging
import uuid

from aiolava import LavaBusinessClient

from . import PaymentSystem


log = logging.getLogger(__name__)


class Lava(PaymentSystem):
    ID: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.CLIENT = LavaBusinessClient(
            private_key=self.LAVA_TOKEN_SECRET,
            shop_id=self.LAVA_PROJECT_ID
        )

    async def create_id(self):
        self.ID = str(uuid.uuid4())

    async def create_invoice(self):
        invoice = await self.CLIENT.create_invoice(
            sum_=self.price,
            order_id=self.ID
        )
        return invoice

    async def check_payment(self):
        tic = 0
        while tic < self.CHECK_PERIOD:
            status = await self.CLIENT.check_invoice_status(order_id=self.ID)
            if status.data.status == 'success':
                await self.successful_payment(self.price, 'Lava')
                return
            tic += self.STEP
            await asyncio.sleep(self.STEP)
            if self.CHECK_PERIOD - tic <= self.TIME_DELETE:
                await self.delete_pay_button('Lava')
        return

    async def to_pay(self):
        await self.create_id()
        invoice = await self.create_invoice()
        await self.pay_button(invoice.data.url)
        log.info(
            f'Create payment link Lava '
            f'User: ID: {self.user_id}'
        )
        try:
            await self.check_payment()
        except BaseException as e:
            log.error(e, 'The payment period has expired')
        finally:
            await self.delete_pay_button('Lava')
            log.info('exit check payment Lava')

    def __str__(self):
        return 'Lava payment system'
