import asyncio
import logging
import uuid

from yookassa import Configuration, Payment

from . import PaymentSystem

log = logging.getLogger(__name__)


class KassaSmart(PaymentSystem):
    CHECK_ID: str = None
    ID: str = None
    EMAIL: str

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.ACCOUNT_ID = int(self.YOOKASSA_SHOP_ID)
        self.SECRET_KEY = self.YOOKASSA_SECRET_KEY
        self.EMAIL = kwargs['email']

    async def create(self):
        self.ID = str(uuid.uuid4())
        
        # Добавляем комиссию 3.5% к цене
        commission_rate = 0.035  # 3.5%
        commission_amount = self.price * commission_rate
        self.price = round(self.price + commission_amount)  # Округляем до целого числа
        log.info(f"YooKassaSmart: added commission 3.5%, new price: {self.price}")

    async def check_payment(self):
        Configuration.account_id = self.ACCOUNT_ID
        Configuration.secret_key = self.SECRET_KEY
        tic = 0
        while tic < self.CHECK_PERIOD:
            res = await Payment.find_one(self.ID)
            if res.status == 'succeeded':
                await self.successful_payment(
                    self.price,
                    'YooKassaSmart (включая комиссию 3.5%)',
                    id_payment=self.ID
                )
                return
            tic += self.STEP
            await asyncio.sleep(self.STEP)
            if self.CHECK_PERIOD - tic <= self.TIME_DELETE:
                await self.delete_pay_button('YooKassaSmart')
        return

    async def invoice(self):
        bot = await self.message.bot.me()
        payment = await Payment.create({
            "amount": {
              "value": self.price,
              "currency": "RUB"
            },
            "receipt": {
                "customer": {
                    "full_name": self.message.from_user.full_name,
                    "email": self.EMAIL,
                },
                "items": [
                    {
                        "description":
                            self.i18n.user.text.subscription.description.payment(),
                        "quantity": "1.00",
                        "amount": {
                            "value": self.price,
                            "currency": "RUB"
                        },
                        "vat_code": "2",
                        "payment_mode": "full_payment",
                        "payment_subject": "commodity"
                    },
                ]
            },
            "confirmation": {
              "type": "redirect",
              "return_url": f'https://t.me/{bot.username}'
            },
            "capture": True,
            "description":
                self.i18n.user.text.subscription.description.payment(),
            "save_payment_method": False
        }, self.ID)
        self.ID = payment.id
        return payment.confirmation.confirmation_url

    @staticmethod
    async def auto_payment(
            config,
            i18n,
            payment_id,
            price,
    ):
        try:
            Configuration.account_id = config.yookassa_shop_id
            Configuration.secret_key = config.yookassa_secret_key
            payment = await Payment.create({
                "amount": {
                    "value": price,
                    "currency": "RUB"
                },
                "capture": True,
                "description": i18n.user.text.subscription.description.payment(),
                "payment_method_id": payment_id
            })
            tic = 0
            while tic < 60:
                res = await Payment.find_one(payment.id)
                if res.status == 'succeeded':
                    return res
                tic += 2
                await asyncio.sleep(2)
            return None
        except Exception as e:
            log.error(
                f'Error Auto Pay KassaSmart, ID payment {payment_id}\n{e}'
            )
            return None

    async def to_pay(self):
        await self.create()
        Configuration.account_id = self.ACCOUNT_ID
        Configuration.secret_key = self.SECRET_KEY
        link_invoice = await self.invoice()
        await self.pay_button(link_invoice, delete=False)
        log.info(
            f'Create payment link YooKassaSmart '
            f'User: (ID: {self.user_id}) - {self.price} RUB'
        )
        try:
            await self.check_payment()
        except BaseException as e:
            log.error(e, 'The payment period has expired')
        finally:
            await self.delete_pay_button('YooKassaSmart')
            log.info('exit check payment YooKassaSmart')

    def __str__(self):
        return 'YooKassaSmart payment system'
