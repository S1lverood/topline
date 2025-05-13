from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models.main import User, Payment, ModerationVote


async def get_user_tg_id(session: AsyncSession, telegram_id):
    statement = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    return user


async def get_payments_user(session: AsyncSession, telegram_id):
    statement = (
        select(Payment).options(joinedload(Payment.payment_id))
        .filter(Payment.user == telegram_id)
        .order_by(desc(Payment.date_registered))
    )
    result = await session.execute(statement)
    payments = result.scalars().all()
    return payments

async def get_payments(session: AsyncSession):
    statement = select(Payment).options(
            joinedload(Payment.payment_id)
    ).order_by(
        desc(Payment.date_registered)
    )
    result = await session.execute(statement)
    payments = result.scalars().all()
    return payments


async def get_users_status(
        session: AsyncSession,
        status_subscription=True
):
    statement = select(User).filter(
        User.status_subscription == status_subscription
    ).order_by(
        desc(User.subscription)
    )
    result = await session.execute(statement)
    users = result.scalars().all()
    return users

async def get_all_user(
        session: AsyncSession,
        limit: int = None,
        order_new=False
):
    if order_new:
        order = desc(User.date_registered)
    else:
        order = User.date_registered
    statement = select(User).order_by(order).limit(limit)
    result = await session.execute(statement)
    users = result.scalars().all()
    return users


async def get_users_pending_moderation(session: AsyncSession):
    """
    Получить всех пользователей, ожидающих модерации
    """
    statement = select(User).filter(User.moderation_status.is_(None))
    result = await session.execute(statement)
    users = result.scalars().all()
    return users


async def get_moderation_votes(session: AsyncSession, user_id: int):
    """
    Получить все голоса модерации для конкретного пользователя
    """
    statement = select(ModerationVote).filter(ModerationVote.user_id == user_id)
    result = await session.execute(statement)
    votes = result.scalars().all()
    return votes


async def get_user_moderation_vote(session: AsyncSession, user_id: int, admin_id: int):
    """
    Получить голос конкретного администратора для конкретного пользователя
    """
    statement = select(ModerationVote).filter(
        ModerationVote.user_id == user_id,
        ModerationVote.admin_id == admin_id
    )
    result = await session.execute(statement)
    vote = result.scalar_one_or_none()
    return vote
