from typing import TYPE_CHECKING
from fluentogram import TranslatorRunner
from .payment_systems import PaymentSystem

from ...misc import Config
from .KassaSmart import KassaSmart
from .Tinkoff import TinkoffPay
from .YooMoney import YooMoney
from .Lava import Lava
from .CryptoBot import CryptoBot
from .Cryptomus import Cryptomus
from .Stars import Stars

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner



def get_all_subclasses(cls):
    """
    Рекурсивно находит все подклассы для заданного класса.

    :param cls: Класс, для которого нужно найти подклассы.
    :return: Список всех подклассов.
    """
    subclasses = cls.__subclasses__()
    all_subclasses = []

    for subclass in subclasses:
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses

all_payments = {clas.__name__: clas for clas in get_all_subclasses(PaymentSystem)}


async def get_active_payment_system(
        i18n: TranslatorRunner
) -> list[tuple[str,str]]:
    payments = []
    if Config.YOOKASSA_SHOP_ID != '' and Config.YOOKASSA_SECRET_KEY != '':
        payments.append(
            (i18n.get('user-button-kassasmart'), KassaSmart.__name__)
        )
    if Config.YOOMONEY_TOKEN != '':
        payments.append(
            (i18n.get('user-button-yoomoney'), YooMoney.__name__)
        )
    if Config.CRYPTOMUS_KEY != "" and Config.CRYPTOMUS_UUID != '':
        payments.append(
            (i18n.get('user-button-cryptomus'), Cryptomus.__name__)
        )
    if Config.CRYPTO_BOT_API != '':
        payments.append(
            (i18n.get('user-button-cryptobot'), CryptoBot.__name__)
        )
    if Config.LAVA_TOKEN_SECRET != '' and Config.LAVA_ID_PROJECT != '':
        payments.append(
            (i18n.get('user-button-lava'), Lava.__name__)
        )
    if Config.TOKEN_STARS != 'off':
        payments.append(
            (i18n.get('user-button-stars'), Stars.__name__)
        )
    if len(payments) == 0:
        payments.append(
            (i18n.get('user-button-no_payment'), str(None))
        )
    return payments

