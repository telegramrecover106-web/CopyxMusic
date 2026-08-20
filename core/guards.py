import time

from pyrogram.enums import ChatMemberStatus, ChatMembersFilter

import state
from config import MAIN_OWNER, RATE_LIMIT_COUNT, RATE_LIMIT_WINDOW, EVERYONE_CAN_CONTROL, OWNER_ID


async def is_admin(client, chat_id, user_id):
    if user_id in (MAIN_OWNER, OWNER_ID):
        return True
    if user_id == getattr(client, "clone_owner", None):
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def can_control(client, chat_id, user_id):
    if EVERYONE_CAN_CONTROL:
        return True
    return await is_admin(client, chat_id, user_id)


async def is_owner(user_id):
    return user_id in (MAIN_OWNER, OWNER_ID)


async def check_abuse(user_id):
    now = time.time()
    if user_id not in state.user_command_history:
        state.user_command_history[user_id] = []
    history = [t for t in state.user_command_history[user_id] if now - t < RATE_LIMIT_WINDOW]
    if len(history) >= RATE_LIMIT_COUNT:
        return True
    history.append(now)
    state.user_command_history[user_id] = history
    return False


async def bot_can_invite(client, chat_id):
    """Check whether the bot has permission to invite users via link."""
    try:
        me = await client.get_chat_member(chat_id, "me")
        if me.status == ChatMemberStatus.OWNER:
            return True
        if me.status == ChatMemberStatus.ADMINISTRATOR:
            privileges = getattr(me, "privileges", None)
            if privileges is not None:
                return bool(getattr(privileges, "can_invite_users", False))
            # Older pyrogram
            return bool(getattr(me, "can_invite_users", False))
        return False
    except Exception:
        return False


async def assistant_in_chat(user_app, chat_id):
    try:
        await user_app.get_chat_member(chat_id, "me")
        return True
    except Exception:
        return False
