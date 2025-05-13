from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Button, Group, Column, Row, Url

from bot.dialogs.user.main.getters import (
    get_general_menu,
    get_faq,
    get_support, get_support_input
)
from bot.dialogs.user.main.handlers import *
from bot.states.state_user import StartSG, StateFAQ, StateSupport

start_dialog = Dialog(
    Window(
        Format('{main_text}'),
        StaticMedia(
            path='bot/img/logo.png',
            type=ContentType.PHOTO
        ),
        Group(
            Column(
                Button(
                    text=Format('{subscribe}'),
                    id='subscribe',
                    on_click=button_subscribe_click
                ),
                Button(
                    text=Format('{account}'),
                    id='account',
                    on_click=button_account_click
                ),
            ),
            Row(
                Button(
                    text=Format('{support}'),
                    id='support',
                    on_click=button_support_click
                ),
                Button(
                    text=Format('{faq}'),
                    id='faq',
                    on_click=button_faq_click
                ),
            ),
            Column(
                Button(
                text=Format('{admin_panel}'),
                id='admin_panel',
                on_click=button_admin_click,
                when=F['is_admin']
                ),
            )
        ),
        getter=get_general_menu,
        state=StartSG.start,
    ),
)


faq_dialog = Dialog(
    Window(
        Format('{faq_text}'),
        StaticMedia(
            path='bot/img/logo.png',
            type=ContentType.PHOTO
        ),
        Button(
            text=Format('{back}'),
            id='back',
            on_click=back_general
        ),
        getter=get_faq,
        state=StateFAQ.faq
    )
)


support_dialog = Dialog(
    Window(
        Format('{support_text}'),
        StaticMedia(
            path='bot/img/support.png',
            type=ContentType.PHOTO
        ),
        Column(
            Button(
                text=Format('{input_support}'),
                id='button_input_support',
                on_click=button_next
            ),
            Url(
                text=Format('{support_faq}'),
                url=Format('{support_link_faq}'),
                id='button_support_link'
            ),
            Button(
            text=Format('{back}'),
            id='back',
            on_click=back_general
            )
        ),
        getter=get_support,
        state=StateSupport.support_menu
    ),
    Window(
        Format('{support_input_text}'),
        StaticMedia(
            path='bot/img/support.png',
            type=ContentType.PHOTO
        ),
        MessageInput(
            func=support_input_handler,
            content_types=ContentType.ANY
        ),
        Button(
            text=Format('{back}'),
            id='back',
            on_click=button_back
        ),
        getter=get_support_input,
        state=StateSupport.input_message
    )
)
