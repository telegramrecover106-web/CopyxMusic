import os
import re

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from clients import call_py
from core.api import fetch_youtube_link
from core.helpers import html_escape
from core.playback import play_music_core


def _mention(user):
    name = html_escape(getattr(user, "first_name", None) or "User")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


async def _voice_chat_is_active(chat_id):
    if chat_id in state.active_voice_chats:
        return True
    # Service updates can be missed after a restart, so ask PyTgCalls/MTProto directly when available.
    import inspect
    for method_name in ("get_call", "get_active_call"):
        method = getattr(call_py, method_name, None)
        if not method:
            continue
        try:
            result = method(chat_id)
            if inspect.isawaitable(result):
                result = await result
            if result is not None:
                state.active_voice_chats.add(chat_id)
                return True
        except Exception:
            continue
    return False


async def _animate_search(status_msg):
    frames = ["🔎 <b>sᴇʀᴇᴀʀᴄʜɪɴɢ...</b>", "🔎 <b>sᴇᴀʀᴄʜɪɴɢ... ✨</b>", "💃 <b>ᴄᴏᴍɪɴɢ ᴜᴘ...</b>", "💃 <b>ᴅᴀɴᴄɪɴɢ...</b>"]
    i = 0
    try:
        while True:
            try:
                await status_msg.edit_text(frames[i % len(frames)], parse_mode=ParseMode.HTML)
            except Exception:
                pass
            i += 1
            await __import__('asyncio').sleep(0.55)
    except __import__('asyncio').CancelledError:
        return


async def play_command(client, message):
    # /play is intentionally group-only, but we explicitly answer in private chat.
    chat_type = getattr(getattr(message.chat, "type", None), "value", getattr(message.chat, "type", ""))
    if str(chat_type).lower() not in ("group", "supergroup"):
        return await message.reply_text("⚠️ <b>This command can only be used in a group.</b>", parse_mode=ParseMode.HTML)

    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text("❌ <b>Usage:</b> <code>/play &lt;song name or URL&gt;</code>", parse_mode=ParseMode.HTML)

    if not await _voice_chat_is_active(message.chat.id):
        return await message.reply_text(
            "📵 <b>No active voice chat found.</b>\n\nPlease start a voice chat and try again.💔",
            parse_mode=ParseMode.HTML,
        )

    status_msg = await message.reply_text("🔎 <b>sᴇᴀʀᴄʜɪɴɢ...</b>", parse_mode=ParseMode.HTML)
    animation_task = __import__('asyncio').create_task(_animate_search(status_msg))

    if "youtu.be" in query:
        m = re.search(r"youtu\.be/([^?&]+)", query)
        if m:
            query = f"https://www.youtube.com/watch?v={m.group(1)}"

    result = await fetch_youtube_link(query)
    animation_task.cancel()
    if not result:
        return await status_msg.edit_text("❌ <b>No matching track found.</b>\nTry another search.", parse_mode=ParseMode.HTML)

    song_info = {
        "title": result.get("title") or "Unknown track",
        "url": result.get("link") or result.get("url"),
        "duration": str(result.get("duration", "0")),
        "thumb": result.get("thumbnail"),
        "req": _mention(message.from_user),
        "user_id": message.from_user.id,
        "requester_name": getattr(message.from_user, "first_name", "User"),
        "file_path": None,
        "bot_id": client.me.id,
    }

    if not song_info["url"]:
        return await status_msg.edit_text("❌ <b>Track URL unavailable.</b>", parse_mode=ParseMode.HTML)

    state.chat_queues.setdefault(message.chat.id, []).append(song_info)

    # Short animated-style status sequence without delaying playback with long sleeps.
    try:
        await status_msg.edit_text("🔎 <b>sᴇᴀʀᴄʜɪɴɢ... 💫</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass

    if len(state.chat_queues[message.chat.id]) == 1:
        await play_music_core(client, message.chat.id, song_info, status_msg)
    else:
        queue_pos = len(state.chat_queues[message.chat.id]) - 1
        queue_text = (
            f"✨ <b>ADDED TO QUEUE:</b>\n\n"
            f"🎵 <b>TITLE:</b> {html_escape(song_info['title'])}\n"
            f"👤 <b>REQUESTED BY:</b> {song_info['req']}\n"
            f"📍 <b>POSITION:</b> <code>{queue_pos}</code>"
        )
        await status_msg.edit_text(
            queue_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ Skip", callback_data="skip"), InlineKeyboardButton("🗑️ Clear", callback_data="clear")],
            ]),
        )


async def reset_chat_playback(client, chat_id, delete_files=True):
    task = state.progress_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    state.paused_chats.discard(chat_id)
    state.auto_mode_chats.discard(chat_id)
    items = state.chat_queues.pop(chat_id, [])
    if delete_files:
        for item in items:
            fp = item.get("file_path")
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass
    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass
    state.active_voice_chats.discard(chat_id)


async def stop_command(client, message):
    chat_id = message.chat.id
    await reset_chat_playback(client, chat_id, delete_files=True)
    await message.reply_text(f"⏹ <b>Stream stopped by {_mention(message.from_user)}.</b>", parse_mode=ParseMode.HTML)


async def skip_command(client, message):
    chat_id = message.chat.id
    items = state.chat_queues.get(chat_id, [])
    if not items:
        return await message.reply_text("❌ <b>Nothing to skip.</b>", parse_mode=ParseMode.HTML)
    if chat_id in state.progress_tasks:
        state.progress_tasks[chat_id].cancel(); state.progress_tasks.pop(chat_id, None)
    state.paused_chats.discard(chat_id)
    done = items.pop(0)
    fp = done.get("file_path")
    if fp and os.path.exists(fp):
        try: os.remove(fp)
        except Exception: pass
    if items:
        await message.reply_text("⏭️ <b>Skipping...</b>", parse_mode=ParseMode.HTML)
        await play_music_core(client, chat_id, items[0])
    else:
        await reset_chat_playback(client, chat_id, delete_files=False)
        await message.reply_text("✅ <b>Queue ended.</b>", parse_mode=ParseMode.HTML)


async def clear_command(client, message):
    chat_id = message.chat.id
    items = state.chat_queues.get(chat_id, [])
    if len(items) <= 1:
        return await message.reply_text("❌ <b>Queue is already empty.</b>", parse_mode=ParseMode.HTML)
    for item in items[1:]:
        fp = item.get("file_path")
        if fp and os.path.exists(fp):
            try: os.remove(fp)
            except Exception: pass
    state.chat_queues[chat_id] = [items[0]]
    await message.reply_text("🗑️ <b>Queue cleared.</b>", parse_mode=ParseMode.HTML)


async def pause_command(client, message):
    try:
        await call_py.pause(message.chat.id)
        state.paused_chats.add(message.chat.id)
        await message.reply_text("⏸️ <b>Stream paused.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ <b>Pause failed:</b> <code>{html_escape(e)}</code>", parse_mode=ParseMode.HTML)


async def resume_command(client, message):
    try:
        await call_py.resume(message.chat.id)
        state.paused_chats.discard(message.chat.id)
        await message.reply_text("▶️ <b>Stream resumed.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ <b>Resume failed:</b> <code>{html_escape(e)}</code>", parse_mode=ParseMode.HTML)


async def queue_command(client, message):
    chat_id = message.chat.id
    items = state.chat_queues.get(chat_id, [])
    if not items:
        return await message.reply_text("🎵 <b>Queue is empty.</b>", parse_mode=ParseMode.HTML)
    lines = ["<blockquote>🎶 <b>UP NEXT</b></blockquote>", ""]
    for idx, item in enumerate(items[:10], 1):
        lines.append(f"<b>{idx}.</b> 🎧 {html_escape(item.get('title') or 'Unknown track')}")
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
