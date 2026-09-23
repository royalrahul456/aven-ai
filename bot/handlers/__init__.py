"""AVEN AI Master Handlers Router."""
from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.help import router as help_router
from bot.handlers.models import router as models_router
from bot.handlers.settings import router as settings_router
from bot.handlers.tools import router as tools_router
from bot.handlers.code import router as code_router
from bot.handlers.special import router as special_router
from bot.handlers.image import router as image_router
from bot.handlers.chat import router as chat_router


def get_main_router() -> Router:
    main_router = Router(name="main_master_router")
    main_router.include_router(start_router)
    main_router.include_router(help_router)
    main_router.include_router(models_router)
    main_router.include_router(settings_router)
    main_router.include_router(tools_router)
    main_router.include_router(code_router)
    main_router.include_router(special_router)
    main_router.include_router(image_router)
    main_router.include_router(chat_router)  # chat_router has natural text fallback, include last
    return main_router
