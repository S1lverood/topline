from aiogram.filters.callback_data import CallbackData


class ReplyMessage(CallbackData, prefix='reply_message'):
    id_client: int


class ModerationVoteCallback(CallbackData, prefix='moderation_vote'): #пока что не нужно но оставлю
    user_id: int  # ID пользователя, которого модерируют
    approved: bool  # True - одобрен, False - отклонен


class RulesAcceptCallback(CallbackData, prefix='rules_accept'):
    """Callback для принятия правил группы"""
    pass