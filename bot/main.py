import logging
import sys
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from fluentogram import TranslatorHub
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.database.models.main import create_all_table
from bot.handlers.errors.main import on_unknown_intent, on_unknown_state
from bot.middlewares.i18n import TranslatorRunnerMiddleware
from bot.middlewares.session import DbSessionMiddleware
from bot.middlewares.track_all_users import TrackAllUsersMiddleware
from bot.misc import Config
from bot.handlers.user import user_router
from bot.handlers.admin import admin_router
from bot.misc.commands import set_commands
from bot.misc.i18n import create_translator_hub
from bot.service.loop import loop

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(filename)s:%(lineno)d "
           "[%(asctime)s] - %(name)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            filename='logs/all.log',
            maxBytes=1024 * 1024 * 25,
            encoding='UTF-8',
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)


async def start_bot():
    bot = Bot(
        token=Config.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await set_commands(bot)
    dp = Dispatcher(
        storage=MemoryStorage(),
        fsm_strategy=FSMStrategy.USER_IN_CHAT
    )

    dp.include_routers(
        user_router,
        admin_router
    )
    async_engine =  await create_all_table()
    sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False)
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(
        on_unknown_state,
        ExceptionTypeFilter(UnknownState),
    )
    dp.update.outer_middleware(DbSessionMiddleware(sessionmaker))
    dp.message.outer_middleware(TrackAllUsersMiddleware())
    translator_hub: TranslatorHub = create_translator_hub()
    dp.update.middleware(TranslatorRunnerMiddleware())
    dp.errors.middleware(TranslatorRunnerMiddleware())

    setup_dialogs(dp)
    scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    scheduler.add_job(
        loop, "interval", seconds=15, args=(
            bot, translator_hub, sessionmaker
        )
    )
    logging.getLogger('apscheduler.executors.default').setLevel(
        logging.WARNING)
    scheduler.start()
    await dp.start_polling(bot, _translator_hub=translator_hub)
