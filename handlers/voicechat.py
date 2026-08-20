import logging

from pyrogram import filters
from pyrogram.enums import ParseMode

import state
from core.playback import stop_playback
from core.queue import clear_queue

logger = logging.getLogger(__name__)


async def on_voice_chat_started(client, message):
    """Telegram service message: video/voice chat started."""
    chat_id = message.chat.id
    if chat_id in state.vc_active:
        return  # already notified
    state.vc_active.add(chat_id)
    try:
        await message.reply_text("😍 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ🥳")
    except Exception:
        pass


async def on_voice_chat_ended(client, message):
    """Telegram service message: video/voice chat ended."""
    chat_id = message.chat.id
    state.vc_active.discard(chat_id)
    try:
        await stop_playback(client, chat_id)
    except Exception as e:
        logger.warning(f"VC end cleanup: {e}")
        clear_queue(chat_id, keep_current=False)
    try:
        await message.reply_text(
            "😕ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ💔\n\nQueue and playback records have been cleared."
        )
    except Exception:
        pass
