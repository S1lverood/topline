import datetime

from datetime import datetime
from sqlalchemy.orm import declared_attr, declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from sqlalchemy import Float, DateTime, Boolean

from bot.database.main import engine


def current_time():
    return datetime.now()

class PreBase:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    date_registered = Column(DateTime, default=current_time)

Base = declarative_base(cls=PreBase)


class User(Base):
    telegram_id = Column(BigInteger, unique=True)
    status_subscription = Column(Boolean, default=False)
    notion_oneday = Column(Boolean, default=False)
    subscription = Column(DateTime, default=current_time)
    username = Column(String, default='@None')
    fullname = Column(String)
    lang_tg = Column(String, nullable=True)
    blocked = Column(Boolean, default=False)
    # Статус модерации: None - ожидает модерации, True - одобрен, False - отклонен
    moderation_status = Column(Boolean, nullable=True, default=None)
    payment = relationship('Payment', back_populates='payment_id')
    moderation_votes = relationship('ModerationVote', back_populates='user')


class Payment(Base):
    user = Column(BigInteger, ForeignKey("user.telegram_id"))
    payment_id = relationship(User, back_populates="payment")
    payment_system = Column(String)
    amount = Column(Float)
    id_payment = Column(String, nullable=True)
    period = Column(String, nullable=True)


class ModerationVote(Base):
    user_id = Column(BigInteger, ForeignKey("user.telegram_id"))
    user = relationship(User, back_populates="moderation_votes")
    admin_id = Column(BigInteger)
    approved = Column(Boolean)  # True - одобрено, False - отклонено
    vote_time = Column(DateTime, default=current_time)


async def create_all_table():
    async_engine = engine()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_engine
