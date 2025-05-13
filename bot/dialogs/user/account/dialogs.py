from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Button, Group, Column, Url

from bot.dialogs.user.account.getters import *
from bot.dialogs.user.account.handlers import button_payments_user
from bot.dialogs.user.main.handlers import *
from bot.states.state_user import StateAccount

account_dialog = Dialog(
    Window(
        Format('{account_text}'),
        DynamicMedia(
            selector='images'
        ),
        Column(
            Url(
                url=Format('{link_channel}'),
                text=Format('{link_channel_text}'),
                id='link_channel',
                when=F['status_subscription']
            ),
            Button(
                text=Format('{account_payment}'),
                id='account_payment',
                on_click=button_payments_user
            ),
            Button(
            text=Format('{back}'),
            id='back',
            on_click=back_general
            )
        ),
        getter=get_account_menu,
        state=StateAccount.account_general,
    ),
    Window(
        Format('{list_payment_text}'),
        Column(
            Button(
            text=Format('{back}'),
            id='back_account',
            on_click=button_back
            )
        ),
        getter=get_payments_user_getter,
        state=StateAccount.list_payments,
    ),
)