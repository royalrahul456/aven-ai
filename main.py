"""AVEN AI — Production Telegram Bot Entrypoint with Render HTTP Health Server, Keep-Awake Pinger & Supabase Support."""
import asyncio
import os
import sys
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.exceptions import TelegramNetworkError
from aiohttp import web

from config import settings
from database.db import db_manager
from utils.logger import logger
from bot.middlewares import ThrottlingMiddleware, UserSessionMiddleware, ErrorHandlerMiddleware
from bot.handlers import get_main_router


async def setup_bot_commands(bot: Bot) -> None:
    """Registers official command menu with Telegram Bot API."""
    commands = [
        BotCommand(command="start", description="Start AVEN AI"),
        BotCommand(command="help", description="Complete command list"),
        BotCommand(command="chat", description="Chat with AVEN"),
        BotCommand(command="ask", description="Ask anything"),
        BotCommand(command="think", description="Deep reasoning mode"),
        BotCommand(command="explain", description="Explain a topic"),
        BotCommand(command="summarize", description="Summarize text"),
        BotCommand(command="rewrite", description="Rewrite/improve text"),
        BotCommand(command="translate", description="Translate text"),
        BotCommand(command="code", description="Generate code"),
        BotCommand(command="debug", description="Debug code"),
        BotCommand(command="explaincode", description="Explain code"),
        BotCommand(command="optimize", description="Optimize code"),
        BotCommand(command="review", description="Review code"),
        BotCommand(command="convert", description="Convert code"),
        BotCommand(command="image", description="Generate AI image (FLUX.1)"),
        BotCommand(command="imagine", description="Generate AI artwork"),
        BotCommand(command="models", description="Select AI model"),
        BotCommand(command="web", description="Web mode"),
        BotCommand(command="auto", description="Automatic model selection"),
        BotCommand(command="settings", description="Bot settings"),
        BotCommand(command="theme", description="Interface theme"),
        BotCommand(command="temperature", description="Response creativity"),
        BotCommand(command="instructions", description="Custom AI instructions"),
        BotCommand(command="reset", description="Reset settings"),
        BotCommand(command="status", description="System status"),
        BotCommand(command="ping", description="Test bot latency & status"),
        BotCommand(command="about", description="About AVEN AI"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info(f"Registered {len(commands)} commands in Telegram command menu.")
    except Exception as e:
        logger.warning(f"Could not set bot commands automatically: {e}")


async def health_handler(request: web.Request) -> web.Response:
    """Health check endpoint for Render Web Service deployment."""
    db_type = "Supabase PostgreSQL" if db_manager.is_postgres else "SQLite"
    return web.json_response({
        "status": "online",
        "service": "AVEN AI Telegram Platform",
        "version": settings.BOT_VERSION,
        "database": db_type,
        "bot_handle": settings.BOT_USERNAME
    })


async def start_health_server(port: int) -> web.AppRunner:
    """Starts a minimal asynchronous health check server on the specified port."""
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info(f"🌐 Render Health Check Server listening on http://0.0.0.0:{port}/")
    return runner


async def keep_awake_pinger() -> None:
    """Periodically pings the Render public URL to prevent free tier from sleeping (15-min limit)."""
    target_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PING_URL")
    if not target_url:
        logger.info("ℹ️ To enable built-in keep-awake on Render, set RENDER_EXTERNAL_URL in your environment variables.")
        return

    target_health = target_url.rstrip("/") + "/health"
    logger.info(f"🔄 Keep-Awake Pinger active for {target_health} (pinging every 10 minutes).")

    # Initial delay before starting pings
    await asyncio.sleep(60)
    while True:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(target_health) as resp:
                    logger.info(f"💓 Keep-awake ping sent to {target_health} (HTTP {resp.status})")
        except Exception as e:
            logger.warning(f"Keep-awake ping failed: {e}")
        # Ping every 10 minutes (600 seconds)
        await asyncio.sleep(600)


async def main() -> None:
    logger.info("Initializing AVEN AI Platform...")

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured! Please configure it in .env")
        print("\n[!] ERROR: TELEGRAM_BOT_TOKEN is missing from .env\n")
        return

    # 1. Initialize Database (Supabase PostgreSQL / SQLite)
    await db_manager.initialize()

    # 2. Start Health Check Server for Render (if PORT is set or default 8080)
    port = int(os.getenv("PORT", str(settings.PORT)))
    runner: web.AppRunner | None = None
    try:
        runner = await start_health_server(port)
    except Exception as e:
        logger.warning(f"Health server could not bind to port {port}: {e}. Continuing in polling-only mode.")

    # 3. Start Keep-Awake Background Task
    pinger_task = asyncio.create_task(keep_awake_pinger())

    # 4. Setup Bot with resilient AIOHTTP Session
    session = AiohttpSession(timeout=60.0)
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    # 5. Register Middlewares
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(UserSessionMiddleware())
    dp.callback_query.middleware(UserSessionMiddleware())

    # 6. Include Handlers
    dp.include_router(get_main_router())

    # 7. Register commands
    await setup_bot_commands(bot)

    # 8. Start Polling with auto-reconnect resilience
    logger.info("⚡ AVEN AI is now online and polling for updates!")
    
    retry_delay = 3
    while True:
        try:
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
            break
        except (TelegramNetworkError, asyncio.TimeoutError, TimeoutError) as net_err:
            logger.warning(f"Telegram network glitch: {net_err}. Auto-reconnecting in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 30)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutdown signal received.")
            break
        except Exception as e:
            logger.exception(f"Unexpected error in polling loop: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
        finally:
            pass

    pinger_task.cancel()
    if runner:
        await runner.cleanup()
    await db_manager.close()
    await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("AVEN AI bot stopped.")
