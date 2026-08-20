import os
import re
import asyncio
import random
from html import escape

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from clients import call_py
from core.api import fetch_youtube_link
from core.guards import check_abuse
from core.playback import play_music_core


def _active_call(call_py_obj, chat_id):
    try:
        return call_py_obj.get_call(chat_id)
    except Exception:
        return None


async def _is_voice_chat_active(chat_id):
    try:
        call = await call_py.get_call(chat_id)
        return call is not None
    except Exception:
        return False


async def play_command(client, message):
    chat_id = message.chat.id
    state.known_groups.add(chat_id)

    if await check_abuse(message.from_user.id):
        return await message.reply_text("⏳ **Slow down a little and try again.**")

    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text("❌ **Usage:** `/play <song name or url>`")

    if not await _is_voice_chat_active(chat_id):
        return await message.reply_text(
            "📵 **No active voice chat found.**\n\n"
            "Please start a voice chat and try again.💔"
        )

    status_msg = await message.reply_text("🔎 <b>Searching</b> …", parse_mode=ParseMode.HTML)

    # Short, non-blocking visual search sequence.
    for frame in ("🔎 <b>Searching</b> …", "💃 <b>Finding your track</b> …"):
        try:
            await status_msg.edit_text(frame, parse_mode=ParseMode.HTML)
        except Exception:
            break
        await asyncio.sleep(0.45)

    if "youtu.be" in query:
        m = re.search(r"youtu\.be/([^?&]+)", query)
        if m:
            query = f"https://www.youtube.com/watch?v={m.group(1)}"

    result = await fetch_youtube_link(query)
    if not result:
        return await status_msg.edit_text("❌ <b>No results found.</b>", parse_mode=ParseMode.HTML)

    title = result.get("title") or "Unknown title"
    url = result.get("link") or result.get("url") or ""
    duration = str(result.get("duration", "0"))
    thumb = result.get("thumbnail")
    requester = message.from_user.mention if message.from_user else "Unknown"

    song_info = {
        "title": title,
        "url": url,
        "duration": duration,
        "thumb": thumb,
        "req": requester,
        "user_id": message.from_user.id,
        "file_path": None,
        "bot_id": client.me.id,
    }

    queue = state.chat_queues.setdefault(chat_id, [])
    queue.append(song_info)

    if len(queue) == 1:
        await play_music_core(client, chat_id, song_info, status_msg)
    else:
        queue_pos = len(queue) - 1
        await status_msg.edit_text(
            f"✨ <b>Added to queue</b>\n\n"
            f"🎵 <b>{escape(title)}</b>\n"
            f"📍 Position: <code>{queue_pos}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📜 Queue", callback_data="queue"),
                 InlineKeyboardButton("⏭ Skip", callback_data="skip")]
            ]),
        )


async def stop_command(client, message):
    chat_id = message.chat.id
    await stop_playback(chat_id)
    try:
        who = message.from_user.mention if message.from_user else "User"
        await message.reply_text(f"⏹ <b>Stream stopped by {who}.</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def stop_playback(chat_id):
    task = state.progress_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    queue = state.chat_queues.pop(chat_id, [])
    state.paused_chats.discard(chat_id)
    state.loop_chats.discard(chat_id)
    for item in queue:
        fp = item.get("file_path")
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except OSError:
                pass
    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass


async def skip_command(client, message):
    chat_id = message.chat.id
    queue = state.chat_queues.get(chat_id, [])
    if not queue:
        return await message.reply_text("❌ **Nothing is playing.**")

    current = queue.pop(0)
    fp = current.get("file_path")
    if fp and os.path.exists(fp):
        try: os.remove(fp)
        except OSError: pass

    task = state.progress_tasks.pop(chat_id, None)
    if task: task.cancel()
    state.paused_chats.discard(chat_id)

    if queue:
        await message.reply_text("⏭ **Skipping...**")
        await play_music_core(client, chat_id, queue[0])
    else:
        await stop_playback(chat_id)
        await message.reply_text("✅ **Queue ended.**")


async def clear_command(client, message):
    chat_id = message.chat.id
    queue = state.chat_queues.get(chat_id, [])
    if len(queue) <= 1:
        return await message.reply_text("❌ **Queue is already empty.**")
    removed = queue[1:]
    state.chat_queues[chat_id] = queue[:1]
    for item in removed:
        fp = item.get("file_path")
        if fp and os.path.exists(fp):
            try: os.remove(fp)
            except OSError: pass
    await message.reply_text("🗑 **Queue cleared.**")


async def pause_command(client, message):
    try:
        await call_py.pause(message.chat.id)
        state.paused_chats.add(message.chat.id)
        await message.reply_text("⏸ **Paused.**")
    except Exception as e:
        await message.reply_text(f"❌ Could not pause: `{e}`")


async def resume_command(client, message):
    try:
        await call_py.resume(message.chat.id)
        state.paused_chats.discard(message.chat.id)
        await message.reply_text("▶️ **Resumed.**")
    except Exception as e:
        await message.reply_text(f"❌ Could not resume: `{e}`")


async def queue_command(client, message):
    queue = state.chat_queues.get(message.chat.id, [])
    if not queue:
        return await message.reply_text("📭 <b>Queue is empty.</b>", parse_mode=ParseMode.HTML)
    lines = ["📜 <b>Current Queue</b>", ""]
    for i, item in enumerate(queue, 1):
        lines.append(f"<code>{i:02}</code> · {escape(item.get('title','Unknown'))}")
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def shuffle_command(client, message):
    queue = state.chat_queues.get(message.chat.id, [])
    if len(queue) <= 2:
        return await message.reply_text("🔀 <b>Not enough queued songs to shuffle.</b>", parse_mode=ParseMode.HTML)
    current = queue[0]
    rest = queue[1:]
    random.shuffle(rest)
    state.chat_queues[message.chat.id] = [current] + rest
    await message.reply_text("🔀 <b>Queue shuffled.</b>", parse_mode=ParseMode.HTML)


async def loop_command(client, message):
    chat_id = message.chat.id
    if chat_id in state.loop_chats:
        state.loop_chats.remove(chat_id)
        text = "🔁 <b>Loop disabled.</b>"
    else:
        state.loop_chats.add(chat_id)
        text = "🔁 <b>Loop enabled.</b>"
    await message.reply_text(text, parse_mode=ParseMode.HTML)
