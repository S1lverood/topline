import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.main import ModerationVote


async def delete_moderation_votes(session: AsyncSession, user_id: int) -> bool:
    """
    Удаляет все голоса модерации для указанного пользователя
    :param session: Сессия базы данных
    :param user_id: ID пользователя
    :return: True если операция выполнена успешно, False в противном случае
    """
    try:
        # Создаем запрос на удаление всех голосов для пользователя
        delete_query = delete(ModerationVote).where(ModerationVote.user_id == user_id)
        
        # Выполняем запрос
        result = await session.execute(delete_query)
        
        # Сохраняем изменения
        await session.commit()
        
        # Логируем результат
        logging.info(f"Удалены голоса модерации для пользователя {user_id}")
        
        return True
    except Exception as e:
        # В случае ошибки откатываем транзакцию и логируем ошибку
        await session.rollback()
        logging.error(f"Ошибка при удалении голосов модерации для пользователя {user_id}: {e}")
        return False