from typing import TYPE_CHECKING

from aiogram import html
from aiogram.types import User
from aiogram_dialog import DialogManager
from fluentogram import TranslatorRunner
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from bot.database.crud.get import get_all_user, get_user_tg_id
from bot.database.models.main import User as UserModel, Payment
from bot.misc import Config

if TYPE_CHECKING:
    from bot.locales.stub import TranslatorRunner


async def get_admin_menu(
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
):
    return dict(
        main_text=i18n.admin.text.admin_menu(),
        milling=i18n.admin.button.milling(),
        statistic=i18n.admin.button.statistic(),
        user_control=i18n.admin.button.user_control(),
        back=i18n.user.button.back.general(),
    )

async def get_milling_group_admin(
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
):
    return dict(
        milling_group_text=i18n.admin.text.admin_menu.group_milling(),
        all_users=i18n.admin.button.milling.all(),
        subscribe_users=i18n.admin.button.milling.sub(),
        not_subscribe_users=i18n.admin.button.milling.not_sub(),
        back=i18n.user.button.back(),
    )

async def get_milling_active_admin(
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
):
    return dict(
        milling_text=i18n.admin.text.admin_menu.milling(),
        back=i18n.user.button.back(),
    )


async def get_statistic_admin(
    i18n: TranslatorRunner,
    event_from_user: User,
    session: AsyncSession,
    **kwargs,
):
    # Получаем статистику по пользователям
    total_users = await get_total_users_count(session)
    active_subs = await get_active_subscriptions_count(session)
    
    # Получаем статистику по заработку
    earned_today = await get_earnings_today(session)
    earned_month = await get_earnings_month(session)
    earned_total = await get_earnings_total(session)
    
    return dict(
        statistic_text=i18n.admin.text.admin_menu.statistic(
            total_users=str(total_users),
            active_subs=str(active_subs),
            earned_today=f"{earned_today}₽",
            earned_month=f"{earned_month}₽",
            earned_total=f"{earned_total}₽"
        ),
        payments=i18n.admin.button.payments(),
        all_users=i18n.admin.button.all_users(),
        active_users=i18n.admin.button.active_users(),
        back=i18n.user.button.back(),
    )


async def get_user_control_input(
    i18n: TranslatorRunner,
    event_from_user: User,
    session: AsyncSession,
    dialog_manager: DialogManager,
    **kwargs,
):
    users = await get_all_user(session, Config.LIMIT_CONTROL_USERS, True)
    text_users = ''
    count = 1
    for user in users:
        text_users += (
            f'{count}) '
            f'<b>{html.quote(user.fullname)}</b> - '
            f'<code>{user.telegram_id}</code>\n'
        )
        count+=1
    if text_users == '':
        text_users = i18n.admin.text.admin_menu.statistic.all_users.not_caption()

    return dict(
        user_control_text=i18n.admin.text.admin_menu.user_control.input(
            users=text_users,
        ),
        back=i18n.user.button.back(),
    )

async def get_user_control_account(
    i18n: TranslatorRunner,
    event_from_user: User,
    session: AsyncSession,
    dialog_manager: DialogManager,
    **kwargs,
):
    id_user = dialog_manager.dialog_data.get('id_user')
    user = await get_user_tg_id(session, id_user)
    if user.status_subscription:
        subscription = i18n.admin.text.admin_menu.user_control.account.sub(
            date=user.subscription.strftime('%d.%m.%Y %H:%M')
        )
    else:
        subscription = i18n.admin.text.admin_menu.user_control.account.no_sub()
    if user.blocked:
        blocked = i18n.admin.text.admin_menu.user_control.account.ban()
        blocked_btn = i18n.admin.button.user_control.unban()
    else:
        blocked = i18n.admin.text.admin_menu.user_control.account.un_ban()
        blocked_btn = i18n.admin.button.user_control.ban()
    user_text = i18n.admin.text.admin_menu.user_control.account(
        full_name=html.quote(user.fullname),
        username=html.quote(user.username),
        subscription=subscription,
        blocked=blocked,
        lang=user.lang_tg
    )
    return dict(
        user_control_account_text=user_text,
        ban_unban_user=blocked_btn,
        message_user=i18n.admin.button.user_control.message(),
        add_time=i18n.admin.button.user_control.add_time(),
        payments_user=i18n.admin.button.user_control.payments(),
        back=i18n.user.button.back(),
    )

async def get_user_control_message_user(
    i18n: TranslatorRunner,
    event_from_user: User,
    session: AsyncSession,
    dialog_manager: DialogManager,
    **kwargs,
):
    id_user = dialog_manager.dialog_data.get('id_user')
    user = await get_user_tg_id(session, id_user)
    return dict(
        user_control_message_user=i18n.admin.text.admin_menu
        .user_control.account.input_message_text(
            full_name=html.quote(user.fullname),
            username=html.quote(user.username),
        ),
        back=i18n.user.button.back(),
    )

async def get_user_control_add_time(
    i18n: TranslatorRunner,
    event_from_user: User,
    session: AsyncSession,
    dialog_manager: DialogManager,
    **kwargs,
):
    id_user = dialog_manager.dialog_data.get('id_user')
    user = await get_user_tg_id(session, id_user)
    return dict(
        user_control_add_time=i18n.admin.text.admin_menu
        .user_control.account.add_time(),
        back=i18n.user.button.back(),
    )


# Функции для получения статистических данных
async def get_total_users_count(session: AsyncSession) -> int:
    """
    Получает общее количество пользователей
    """
    result = await session.execute(select(func.count()).select_from(UserModel))
    return result.scalar() or 0


async def get_active_subscriptions_count(session: AsyncSession) -> int:
    """
    Получает количество активных подписок
    """
    result = await session.execute(
        select(func.count())
        .select_from(UserModel)
        .where(UserModel.status_subscription == True)
    )
    return result.scalar() or 0


async def get_earnings_today(session: AsyncSession) -> int:
    """
    Получает сумму заработка за сегодня
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    result = await session.execute(
        select(func.sum(Payment.amount))
        .select_from(Payment)
        .where(and_(Payment.date_registered >= today, Payment.date_registered < tomorrow))
    )
    return result.scalar() or 0


async def get_earnings_month(session: AsyncSession) -> int:
    """
    Получает сумму заработка за текущий месяц
    """
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    result = await session.execute(
        select(func.sum(Payment.amount))
        .select_from(Payment)
        .where(Payment.date_registered >= start_of_month)
    )
    return result.scalar() or 0


async def get_earnings_total(session: AsyncSession) -> int:
    """
    Получает общую сумму заработка за всё время
    """
    result = await session.execute(
        select(func.sum(Payment.amount))
        .select_from(Payment)
    )
    return result.scalar() or 0
