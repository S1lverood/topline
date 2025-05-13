import os
from datetime import timezone, timedelta
from os import environ
from typing import Final

from dotenv import load_dotenv

load_dotenv()


class ConfigBot:
    TOKEN: Final = environ.get('TOKEN', 'define me!')
    ADMINS_ID: list[int] = list(map(int, environ.get('ADMINS_ID', []).split(',')))
    PERIOD: list
    AMOUNT: list
    ID_CHANNEL: str
    LINK_CHANNEL: str
    NAME_CHANNEL: str
    UTC_TIME: int
    TOKEN_STARS: str
    YOOMONEY_TOKEN: str
    YOOMONEY_WALLET: str
    LAVA_TOKEN_SECRET: str
    LAVA_ID_PROJECT: str
    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str
    CRYPTOMUS_KEY: str
    CRYPTOMUS_UUID: str
    CRYPTO_BOT_API: str
    DEBUG: bool = True
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    TINKOFF_TERMINAL: str
    TINKOFF_SECRET: str
    TYPE_PAYMENT: dict = {
        0: 'new_sub',
        1: 'extend_sub',
    }
    LIMIT_CONTROL_USERS: int = 10
    DAY_SHOW_ALERT = 1
    DEFAULT_LANGUAGE: str = 'ru'

    def __init__(self):
        self.read_evn()

    def read_evn(self):
        try:
            admin_id = os.getenv('ADMINS_ID')
            self.ADMINS_ID = list(map(int, admin_id.split(',')))
        except Exception:
            raise ValueError('Write your ID Telegram to ADMINS_ID')

        self.TOKEN = os.getenv('TG_TOKEN')
        if self.TOKEN is None:
            raise ValueError('Write your TOKEN TelegramBot to TG_TOKEN')

        try:
            self.PERIOD = os.getenv('PERIOD').split(',')
            if self.PERIOD is None:
                raise ValueError('Write your count month to PERIOD')
        except Exception as e:
            raise ValueError(
                'You filled in the PERIOD field incorrectly', e
            )

        try:
            self.AMOUNT = os.getenv('AMOUNT').split(',')
            if self.AMOUNT is None:
                raise ValueError('Write your price month to AMOUNT')
        except Exception as e:
            raise ValueError(
                'You filled in the PERIOD field incorrectly', e
            )

        if len(self.PERIOD) != len(self.AMOUNT):
            raise ValueError(
                'AMOUNT and PERIOD must have same length'
            )

        self.ID_CHANNEL = os.getenv('ID_CHANNEL')
        if self.ID_CHANNEL == '':
            raise ValueError('Write your ID channel to ID_CHANNEL')

        self.LINK_CHANNEL = os.getenv('LINK_CHANNEL')
        if self.LINK_CHANNEL == '':
            raise ValueError('Write your link channel to LINK_CHANNEL')

        self.NAME_CHANNEL = os.getenv('NAME_CHANNEL')
        if self.NAME_CHANNEL == '':
            raise ValueError('Write your name channel to NAME_CHANNEL')
            
        # Устанавливаем DEBUG из переменных окружения или используем значение по умолчанию
        debug_env = os.getenv('DEBUG')
        if debug_env is not None:
            if debug_env.lower() in ('true', '1', 'yes'):
                self.DEBUG = True
            else:
                self.DEBUG = False

        utc_time = os.getenv('UTC_TIME')
        if utc_time == '':
            raise ValueError('Write your UTC TIME to UTC_TIME')
        self.UTC_TIME = int(utc_time)

        token_stars = os.getenv('TG_STARS')
        self.TOKEN_STARS = '' if token_stars != 'off' else token_stars
        token_stars = os.getenv('TG_STARS_DEV')
        self.TOKEN_STARS = '' if token_stars == 'run' else self.TOKEN_STARS
        self.YOOMONEY_TOKEN = os.getenv('YOOMONEY_TOKEN', '')
        self.YOOMONEY_WALLET = os.getenv('YOOMONEY_WALLET', '')
        self.LAVA_TOKEN_SECRET = os.getenv('LAVA_TOKEN_SECRET', '')
        self.LAVA_ID_PROJECT = os.getenv('LAVA_ID_PROJECT', '')
        self.YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', '')
        self.YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', '')
        self.TINKOFF_TERMINAL = os.getenv('TINKOFF_TERMINAL', '')
        self.TINKOFF_SECRET = os.getenv('TINKOFF_SECRET', '')
        self.CRYPTOMUS_KEY = os.getenv('CRYPTOMUS_KEY', '')
        self.CRYPTOMUS_UUID = os.getenv('CRYPTOMUS_UUID', '')
        self.CRYPTO_BOT_API = os.getenv('CRYPTO_BOT_API', '')
        self.DEBUG = os.getenv('DEBUG') == 'True'
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', '')
        if self.POSTGRES_DB == '':
            raise ValueError('Write your name DB to POSTGRES_DB')
        self.POSTGRES_USER = os.getenv('POSTGRES_USER', '')
        if self.POSTGRES_USER == '':
            raise ValueError('Write your login DB to POSTGRES_USER')
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
        if self.POSTGRES_PASSWORD == '':
            raise ValueError('Write your password DB to POSTGRES_PASSWORD')
        pg_email = os.getenv('PGADMIN_DEFAULT_EMAIL', '')
        if pg_email == '':
            raise ValueError('Write your email to PGADMIN_DEFAULT_EMAIL')
        pg_password = os.getenv('PGADMIN_DEFAULT_PASSWORD', '')
        if pg_password == '':
            raise ValueError('Write your password to PGADMIN_DEFAULT_PASSWORD')


Config = ConfigBot()

timezone_offset = timezone(timedelta(hours=Config.UTC_TIME))