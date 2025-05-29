import logging
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
    logging.info(f"CRITICAL: Getting moderation votes for user {user_id}")
    
    try:
        # Сначала проверим, существует ли пользователь в базе данных
        user_stmt = select(User).filter(User.telegram_id == user_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            logging.error(f"CRITICAL: User {user_id} not found in database when getting votes")
            return []
        
        logging.info(f"CRITICAL: Found user {user_id} in database, user.id={user.id}, moderation_status={user.moderation_status}")
        
        # Получаем голоса по telegram_id пользователя
        # Сначала попробуем найти по user_id в таблице ModerationVote
        statement = select(ModerationVote).filter(ModerationVote.user_id == user_id)
        result = await session.execute(statement)
        votes = result.scalars().all()
        
        # Если не нашли голоса по telegram_id, попробуем по user.id в базе данных
        if not votes:
            logging.info(f"CRITICAL: No votes found by telegram_id, trying by user.id={user.id}")
            statement = select(ModerationVote).filter(ModerationVote.user_id == user.id)
            result = await session.execute(statement)
            votes = result.scalars().all()
        
        # Логируем каждый голос
        logging.info(f"CRITICAL: Found {len(votes)} votes for user {user_id}")
        
        # Логируем голоса в отдельном try-except блоке, чтобы не потерять голоса при ошибке логирования
        try:
            for i, vote in enumerate(votes):
                logging.info(f"CRITICAL: Vote {i+1}: admin_id={vote.admin_id}, approved={vote.approved}")
        except Exception as e:
            logging.error(f"CRITICAL: Error logging votes details: {e}")
        
        # Возвращаем голоса в любом случае
        return votes
    except Exception as e:
        import traceback
        logging.error(f"CRITICAL: Error getting moderation votes for user {user_id}: {e}")
        logging.error(f"CRITICAL: Traceback: {traceback.format_exc()}")
        # Возвращаем пустой список в случае ошибки
        return []


async def get_user_moderation_vote(session: AsyncSession, user_id: int, admin_id: int):
    """
    Получить голос конкретного администратора для конкретного пользователя
    """
    logging.info(f"CRITICAL: Getting moderation vote for user {user_id} from admin {admin_id}")
    
    # Сначала ищем голос по telegram_id
    statement = select(ModerationVote).filter(
        ModerationVote.user_id == user_id,
        ModerationVote.admin_id == admin_id
    )
    result = await session.execute(statement)
    vote = result.scalar_one_or_none()
    
    # Если голос найден, возвращаем его
    if vote:
        logging.info(f"CRITICAL: Found vote by telegram_id for user {user_id} from admin {admin_id}")
        return vote
    
    # Если голос не найден, пробуем получить пользователя из базы данных
    try:
        user = await get_user_tg_id(session, user_id)
        if user:
            # Ищем голос по user.id
            statement = select(ModerationVote).filter(
                ModerationVote.user_id == user.id,
                ModerationVote.admin_id == admin_id
            )
            result = await session.execute(statement)
            vote = result.scalar_one_or_none()
            
            if vote:
                logging.info(f"CRITICAL: Found vote by user.id={user.id} for user {user_id} from admin {admin_id}")
            else:
                logging.info(f"CRITICAL: No vote found for user {user_id} from admin {admin_id}")
            
            return vote
    except Exception as e:
        logging.error(f"CRITICAL: Error getting user for vote: {e}")
    
    return None
