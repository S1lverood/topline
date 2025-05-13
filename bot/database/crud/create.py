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
    try:
        # Проверяем, голосовал ли уже этот админ за этого пользователя
        existing_vote = await get_user_moderation_vote(session, user_id, admin_id)
        
        if existing_vote:
            # Если голос уже существует, обновляем его
            existing_vote.approved = approved
            await session.commit()
            logging.info(f'DB updated moderation vote: user:{user_id} admin:{admin_id} approved:{approved}')
            return existing_vote
        else:
            # Если голоса нет, создаем новый
            vote = ModerationVote(
                user_id=user_id,
                admin_id=admin_id,
                approved=approved
            )
            session.add(vote)
            await session.commit()
            await session.refresh(vote)  # Обновляем объект из базы данных
            logging.info(f'DB created new moderation vote: user:{user_id} admin:{admin_id} approved:{approved}')
            return vote
    except Exception as e:
        # В случае ошибки откатываем транзакцию и логируем ошибку
        await session.rollback()
        logging.error(f'Ошибка при добавлении голоса модерации: user:{user_id} admin:{admin_id} - {str(e)}')
        return None
