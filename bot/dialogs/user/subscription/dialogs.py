from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Button, Group, Column, Row, Url, Select

from bot.dialogs.user.main.handlers import back_general, button_back
from bot.dialogs.user.subscription.getters import *
from bot.dialogs.user.subscription.handlers import button_choosing_month, \
    month_selection, payment_selection, input_email_handler
from bot.states.state_user import StateSubscription

subscription_general_dialog = Dialog(
    Window(
        Format('{subscription_status}'),
        StaticMedia(
            path='bot/img/sub.png',
            type=ContentType.PHOTO
        ),
        Group(
            Column(
                Button(
                text=Format('{subscription_pay}'),
                id='user_pay',
                on_click=button_choosing_month
                ),
                Url(
                    text=Format('{button_subscription_link}'),
                    id='subscription_pay_friend',
                    url=Format('{subscription_link}'),
                ),
                Button(
                    text=Format('{back}'),
                    id='back',
                    on_click=back_general
                )
            )
        ),
        getter=get_sub_general_menu,
        state=StateSubscription.subscription_general,
    ),
    Window(
        Format('{choosing_time}'),
        StaticMedia(
            path='bot/img/sub.png',
            type=ContentType.PHOTO
        ),
        Group(
            Group(
                Select(
                    Format('{item[0]}'),
                    id='mont',
                    item_id_getter=lambda x: x[1],
                    items='month',
                    on_click=month_selection
                ),
                width=2
            ),
            Button(
                text=Format('{back}'),
                id='back',
                on_click=button_back
            )
        ),
        getter=get_sub_month,
        state=StateSubscription.choosing_month,
    ),
    Window(
        Format('{choosing_payment}'),
        StaticMedia(
            path='bot/img/payment.png',
            type=ContentType.PHOTO
        ),
        Group(
            Group(
                Select(
                    Format('{item[0]}'),
                    id='payment',
                    item_id_getter=lambda x: x[1],
                    items='payments',
                    on_click=payment_selection
                ),
                width=2
            ),
            Button(
                text=Format('{back}'),
                id='back',
                on_click=button_back
            )
        ),
        getter=get_sub_payments,
        state=StateSubscription.choosing_payment,
    ),
    Window(
        Format('{input_email_message}'),
        StaticMedia(
            path='bot/img/sub.png',
            type=ContentType.PHOTO
        ),
        MessageInput(
            func=input_email_handler,
            content_types=ContentType.TEXT
        ),
        Button(
            text=Format('{back}'),
            id='back',
            on_click=back_general
        ),
        getter=get_input_email,
        state=StateSubscription.input_email,
    ),
)