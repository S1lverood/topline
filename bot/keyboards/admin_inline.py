from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from bot.misc.callback_data import ReplyMessage, ModerationVoteCallback

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def reply_message(
        i18n: TranslatorRunner,
        id_client
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=i18n.admin.button.reply.message(),
        callback_data=ReplyMessage(id_client=id_client)
    )
    kb.adjust(1)
    return kb.as_markup()


async def moderation_keyboard(
        i18n: TranslatorRunner,
        user_id: int
) -> InlineKeyboardMarkup:
    """
    Клавиатура для модерации пользователя
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Одобрить",  # Галочка Одобрить
        callback_data=ModerationVoteCallback(user_id=user_id, approved=True)
    )
    kb.button(
        text="❌ Отклонить",  # Крестик Отклонить
        callback_data=ModerationVoteCallback(user_id=user_id, approved=False)
    )
    kb.adjust(2)
    return kb.as_markup()