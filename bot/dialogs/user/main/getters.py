from typing import TYPE_CHECKING

from aiogram.types import User
from fluentogram import TranslatorRunner

from bot.service.service import check_admin

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def get_general_menu(
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
):
    return {
        'main_text': i18n.user.text.main(),
        'subscribe': i18n.user.button.subscribe(),
        'account': i18n.user.button.account(),
        'support': i18n.user.button.support(),
        'faq': i18n.user.button.faq(),
        'admin_panel': i18n.admin.button.menu(),
        'is_admin': await check_admin(event_from_user.id)
    }


async def get_faq(
    i18n: TranslatorRunner,
    **kwargs,
) -> dict[str, str]:
    return {
        'faq_text': i18n.user.text.faq(),
        'back': i18n.user.button.back(),
    }


async def get_support(
    i18n: TranslatorRunner,
    **kwargs,
) -> dict[str, str]:
    return {
        'support_text': i18n.user.text.support(),
        'input_support': i18n.user.button.input.support(),
        'support_faq': i18n.user.button.link.faq(),
        'support_link_faq': i18n.user.link.support.faq(),
        'back': i18n.user.button.back(),
    }


async def get_support_input(
    i18n: TranslatorRunner,
    **kwargs,
) -> dict[str, str]:
    return {
        'support_input_text': i18n.user.text.support.input(),
        'back': i18n.user.button.back(),
    }
