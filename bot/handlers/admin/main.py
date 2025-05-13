from aiogram import Router

from bot.dialogs.admin.main.dialogs import admin_menu_dialog
from bot.filters.main import IsAdmin
from bot.handlers.admin.moderation import moderation_router

admin_router = Router()
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())

# Включаем модуль модерации
moderation_router.message.filter(IsAdmin())
moderation_router.callback_query.filter(IsAdmin())

admin_router.include_routers(
    admin_menu_dialog,
    moderation_router
)
