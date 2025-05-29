import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.get import get_user_tg_id, get_user_moderation_vote
from bot.database.models.main import Payment, ModerationVote


async def add_payment(
        session: AsyncSession,
        telegram_id,
        deposit,
        payment_system,
        id_payment,
        period
):
    person = await get_user_tg_id(session, telegram_id)
    if person is not None:
        payment = Payment(
            amount=deposit,
            payment_system=payment_system,
            id_payment=id_payment,
            period=period
        )
        payment.user = person.telegram_id
        session.add(payment)
        await session.commit()
        logging.info(
            f'DB write new payment user:{telegram_id} amount:{deposit}'
        )


async def add_moderation_vote(
        session: AsyncSession,
        user_id: int,
        admin_id: int,
        approved: bool
):
    """
    Добавить или обновить голос модерации от администратора
    :return: Объект голоса или None в случае ошибки
    """
    logging.info(f'CRITICAL: Starting add_moderation_vote for user:{user_id} admin:{admin_id} approved:{approved}')
    
    # Проверяем, существует ли пользователь в базе данных
    try:
        # Используем уже импортированные модели вместо повторного импорта
        from .get import get_user_tg_id
        
        # Получаем пользователя из базы данных
        user = await get_user_tg_id(session, user_id)
        
        if not user:
            logging.error(f'CRITICAL: User {user_id} not found in database when adding moderation vote')
            return None
        
        logging.info(f'CRITICAL: Found user {user_id} in database, user.id={user.id}, moderation_status={user.moderation_status}')
    except Exception as e:
        logging.error(f'CRITICAL: Error checking user existence: user:{user_id} - {str(e)}')
    
    try:
        # Проверяем, голосовал ли уже этот админ за этого пользователя
        existing_vote = await get_user_moderation_vote(session, user_id, admin_id)
        logging.info(f'CRITICAL: Checked for existing vote: user:{user_id} admin:{admin_id} exists:{existing_vote is not None}')
        
        if existing_vote:
            # Если голос уже существует, обновляем его
            logging.info(f'CRITICAL: Updating existing vote: user:{user_id} admin:{admin_id} old_approved:{existing_vote.approved} new_approved:{approved}')
            existing_vote.approved = approved
            await session.commit()
            logging.info(f'CRITICAL: DB updated moderation vote: user:{user_id} admin:{admin_id} approved:{approved}')
            return existing_vote
        else:
            # Если голоса нет, создаем новый
            logging.info(f'CRITICAL: Creating new vote: user:{user_id} (user.id={user.id}) admin:{admin_id} approved:{approved}')
            vote = ModerationVote(
                user_id=user.id,  # Используем user.id из базы данных вместо telegram_id
                admin_id=admin_id,
                approved=approved
            )
            session.add(vote)
            await session.commit()
            await session.refresh(vote)  # Обновляем объект из базы данных
            logging.info(f'CRITICAL: DB created new moderation vote: user:{user_id} admin:{admin_id} approved:{approved} vote_id:{vote.id}')
            return vote
    except Exception as e:
        # В случае ошибки откатываем транзакцию и логируем ошибку
        await session.rollback()
        import traceback
        logging.error(f'CRITICAL: Ошибка при добавлении голоса модерации: user:{user_id} admin:{admin_id} - {str(e)}')
        logging.error(f'CRITICAL: Traceback: {traceback.format_exc()}')
        return None
