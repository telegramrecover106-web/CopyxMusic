from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import ChatMemberUpdated

from config import BOT_NAME
from core.player_ui import welcome_caption, welcome_buttons


async def on_bot_added(client, update: ChatMemberUpdated):
    """Send welcome when this bot is added to a group/supergroup."""
    try:
        if not update.new_chat_member:
            return
        new = update.new_chat_member
        # Only when bot itself is added
        if new.user.id != client.me.id:
            return
        if new.status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
            return
        # Avoid leave events
        old = update.old_chat_member
        if old and old.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
            return

        chat = update.chat
        title = chat.title or "Group"
        username = chat.username
        caption = welcome_caption(title, chat.id, username)
        buttons = welcome_buttons(client.me.username or "COPYxMUSIC_BOT")
        try:
            await client.send_message(
                chat.id,
                caption,
                parse_mode=ParseMode.HTML,
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
        except Exception:
            try:
                await client.send_message(chat.id, caption, parse_mode=ParseMode.HTML)
            except Exception:
                pass
    except Exception:
        pass
