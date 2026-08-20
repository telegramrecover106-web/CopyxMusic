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
from pathlib import Path

from CopyxMusic import logger


def ensure_dirs():
    """
    Create necessary directories if they don't exist.

    Creates:
    - cache/: For temporary cache files
    - downloads/: For downloaded media files
    """
    # List of required directories
    for dir in ["cache", "downloads"]:
        # Create directory (and parents if needed)
        Path(dir).mkdir(parents=True, exist_ok=True)
    logger.info("📁 Cache directories updated.")
