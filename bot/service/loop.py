import logging
import datetime as dt
from datetime import datetime
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.types import FSInputFile
from fluentogram import TranslatorHub, TranslatorRunner
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.database.crud.get import get_users_status
from bot.database.crud.update import user_swith_one_day, user_swith_sub
from bot.database.models.main import User
from bot.keyboards.user_inline import pay_subscribe
from bot.misc import Config
from bot.misc.config import timezone_offset

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner

log = logging.getLogger(__name__)

COUNT_SECOND_DAY = 86400


async def loop(
        bot: Bot,
        translator_hub: TranslatorHub,
        session_pool: async_sessionmaker
):
    try:
        async with session_pool() as session:
            for user in await get_users_status(session):
                await check_user(user, translator_hub, session, bot)
    except Exception as e:
        log.error(e)

async def check_user(
        user: User,
        translator_hub: TranslatorHub,
        session: AsyncSession,
        bot: Bot
):
    if user.lang_tg is not None:
        language_code = user.lang_tg
    else:
        language_code = Config.DEFAULT_LANGUAGE
    i18n: TranslatorRunner = translator_hub.get_translator_by_locale(
        locale=language_code
    )
    user_time = user.subscription.replace(tzinfo=timezone_offset)
    if user.notion_oneday:
        if user_time < datetime.now(timezone_offset) + dt.timedelta(
                days=Config.DAY_SHOW_ALERT
        ):
            if not user.blocked:
                try:
                    await bot.send_photo(
                        photo=FSInputFile('bot/img/warning.png'),
                        chat_id=user.telegram_id,
                        caption=i18n.user.text.subscription.one_day(
                            day=Config.DAY_SHOW_ALERT
                        ),
                        reply_markup=await pay_subscribe(i18n)
                    )
                except Exception:
                    log.info(f'User {user.telegram_id} banned bot')
            await user_swith_one_day(session, user.telegram_id, False)
            return
    if user_time > datetime.now(timezone_offset):
        return
    await end_subscription(user, i18n, session, bot)
    logging.info(f'user {user.telegram_id} banned channel')


async def end_subscription(
    user: User,
    i18n: TranslatorRunner,
    session: AsyncSession,
    bot: Bot
):
    if not user.blocked:
        try:
            await bot.send_photo(
                photo=FSInputFile('bot/img/end_sub.png'),
                chat_id=user.telegram_id,
                caption=i18n.user.text.subscription.end(),
                reply_markup=await pay_subscribe(i18n)
            )
        except Exception:
            log.info(f'User {user.telegram_id} banned bot')
    try:
        await bot.ban_chat_member(
            chat_id=Config.ID_CHANNEL,
            user_id=user.telegram_id,
        )
    except Exception as e:
        log.critical(e)
    await bot.unban_chat_member(
        chat_id=Config.ID_CHANNEL,
        user_id=user.telegram_id,
    )
    await user_swith_sub(session, user.telegram_id, False)
