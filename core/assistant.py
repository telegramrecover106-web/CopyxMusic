import asyncio
import logging

from pyrogram.errors import (
    UserAlreadyParticipant,
    FloodWait,
    ChatAdminRequired,
    InviteHashExpired,
    InviteHashInvalid,
    UserBannedInChannel,
)

import state
from clients import user_app
from core.guards import assistant_in_chat, bot_can_invite

logger = logging.getLogger(__name__)


async def ensure_assistant_in_chat(client, chat_id, status_callback=None):
    """
    Make sure the assistant account is a member of the chat.
    Returns (ok: bool, error_message: str|None)
    """
    try:
        if await assistant_in_chat(user_app, chat_id):
            return True, None
    except Exception:
        pass

    if status_callback:
        try:
            await status_callback("⏳ Inviting assistant to your chat...")
        except Exception:
            pass

    can_invite = await bot_can_invite(client, chat_id)
    if not can_invite:
        return False, (
            "⚠️ Bot needs the <b>Invite Users via Link</b> permission to work properly.\n\n"
            "Make the bot an admin with invite permission, then try again."
        )

    # Try join via invite link
    for attempt in range(2):
        try:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                link_obj = await client.create_chat_invite_link(chat_id)
                invite_link = link_obj.invite_link

            try:
                await user_app.join_chat(invite_link)
            except UserAlreadyParticipant:
                return True, None
            except (InviteHashExpired, InviteHashInvalid):
                link_obj = await client.create_chat_invite_link(chat_id)
                await user_app.join_chat(link_obj.invite_link)
            except FloodWait as fw:
                await asyncio.sleep(min(int(fw.value), 15))
                continue
            except UserBannedInChannel:
                return False, "❌ Assistant is banned in this chat."
            except ChatAdminRequired:
                return False, (
                    "⚠️ Bot needs the <b>Invite Users via Link</b> permission to work properly."
                )

            await asyncio.sleep(1.5)
            if await assistant_in_chat(user_app, chat_id):
                return True, None
        except Exception as e:
            logger.warning(f"Assistant invite attempt {attempt}: {e}")
            if attempt == 1:
                return False, f"❌ Could not invite assistant: {e}"

    return False, "❌ Assistant invite failed. Add the assistant manually and retry."


async def safe_leave_call(call_py, chat_id):
    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass
