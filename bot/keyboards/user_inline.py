from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner
from bot.misc.callback_data import RulesAcceptCallback

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def link_chanel(
        i18n: TranslatorRunner,
        link_channel
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=i18n.user.button.open.channel(),
        url=link_channel
    )
    kb.button(
        text=i18n.user.button.back.general(),
        callback_data='answer_back_general_menu_btn',
    )
    kb.adjust(1)
    return kb.as_markup()


async def pay_subscribe(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=i18n.user.button.subscribe(),
        callback_data='subscribe_btn',
    )
    kb.adjust(1)
    return kb.as_markup()


async def back_btn(
        i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=i18n.user.button.back.general(),
        callback_data='answer_back_general_menu_btn',
    )
    kb.adjust(1)
    return kb.as_markup()


async def rules_accept_keyboard(
        i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для принятия правил группы
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text=i18n.user.button.accept_rules(),
        callback_data=RulesAcceptCallback()
    )
    kb.adjust(1)
    return kb.as_markup()