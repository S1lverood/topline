from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from bot.database.models.main import User


async def upsert_user(
    session: AsyncSession,
    telegram_id: int,
    username: str,
    fullname: str,
    lang_tg: str | None = None,
    moderation_status: bool | None = None,
):
    try:
        new_username = '@'+username
    except Exception as e:
        new_username = username

    if new_username is None:
        new_username = '@None'

    stmt = insert(User).values(
        telegram_id=telegram_id,
        username=new_username,
        fullname=fullname,
        lang_tg=lang_tg,
        moderation_status=moderation_status,  # Используем переданный статус модерации
    ).on_conflict_do_update(
        index_elements=['telegram_id'],
        set_={
            "username": new_username,
            "fullname": fullname,
            "lang_tg": lang_tg,
            # Обновляем статус модерации только если он не None
            "moderation_status": moderation_status if moderation_status is not None else User.moderation_status,
        },
    )

    await session.execute(stmt)
    await session.commit()
