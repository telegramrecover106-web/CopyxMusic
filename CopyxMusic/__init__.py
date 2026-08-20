# ==========================================================
# Copyright (c) 2026 CopyMusic
# All Rights Reserved.
#
# Project      : CopyMusic API Telegram Music Bot
# Powered By   : Copy Music
# Type         : API Based Telegram Music Bot
# 
# Bot          : @CopyxMusicBot
# Channel      : https://t.me/copymusic
# GitHub       : https://github.com/yourusername/CopyxMusic
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
import asyncio
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import List

# Configure logging
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

# Reduce noise from third-party libraries
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

logger = logging.getLogger("CopyxMusic")

# Version
__version__ = "3.0.1"

# Load configuration
from config import Config

config = Config()
config.check()

# Global task list for background tasks
tasks: List = []
boot: float = time.time()

# Initialize bot client
from CopyxMusic.core.bot import Bot
app = Bot()

# Ensure required directories exist
from CopyxMusic.core.dir import ensure_dirs
ensure_dirs()

# Initialize userbot/assistant clients
from CopyxMusic.core.userbot import Userbot
userbot = Userbot()

# Initialize database connection
from CopyxMusic.core.mongo import MongoDB
db = MongoDB()

# Initialize language system
from CopyxMusic.core.lang import Language
lang = Language()

# Initialize Telegram and YouTube utilities
from CopyxMusic.core.telegram import Telegram
from CopyxMusic.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

# Initialize preload manager for background track downloading
from CopyxMusic.core.preload import PreloadManager
preload = PreloadManager()

# Initialize queue manager
from CopyxMusic.helpers import Queue
queue = Queue()

# Initialize preload manager for next-track downloading
from CopyxMusic.helpers._preload import PreloadManager
preload = PreloadManager()

# Initialize call handler
from CopyxMusic.core.calls import TgCall
tune = TgCall()


async def stop() -> None:
    """
    Gracefully shutdown the bot and all its components.
    
    This function:
    - Cancels all running background tasks
    - Closes bot and userbot connections
    - Closes database connection
    - Logs shutdown completion
    """
    logger.info("🛑 Stopping bot...")
    
    # Cancel all background tasks
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            # Expected when cancelling tasks - suppress the error
            pass
        except Exception:
            pass
    
    # Close all connections
    await app.exit()
    await userbot.exit()
    await db.close()
    
    logger.info("✅ Bot stopped successfully.\n")
