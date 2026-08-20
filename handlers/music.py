import os
import re

from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from clients import call_py
from core.api import fetch_youtube_link, get_lyrics, fetch_related
from core.database import add_favourite, remove_favourite, get_favourites
from core.guards import check_abuse, can_control, is_admin
from core.helpers import format_time, mention_html, one_line_title, get_progress_bar, parse_duration_str
from core.playback import play_music_core, stop_playback, skip_playback, has_active_voice_chat
from core.player_ui import build_player_caption, build_control_keyboard
from core.queue import (
    add_to_queue, get_queue, clear_queue, shuffle_queue, queue_count, current_song,
)


def _group_only(message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return True
    return False


async def play_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")

    if await check_abuse(message.from_user.id):
        return await message.reply_text("⏳ **Slow down.**")

    chat_id = message.chat.id
    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text(
            "🎵 <b>Usage:</b> <code>/play [song name or URL]</code>\n\n"
            "<b>Example:</b> <code>/play Blinding Lights</code>",
            parse_mode=ParseMode.HTML,
        )

    status_msg = await message.reply_text("🔎 <b>Searching...</b>", parse_mode=ParseMode.HTML)

    if "youtu.be" in query:
        m = re.search(r"youtu\.be/([^?&]+)", query)
        if m:
            query = f"https://www.youtube.com/watch?v={m.group(1)}"

    try:
        await status_msg.edit_text("💃 <b>Processing...</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass

    result = await fetch_youtube_link(query)
    if not result:
        return await status_msg.edit_text("❌ No results found. Try a different query.")

    user = message.from_user
    song_info = {
        "title": result.get("title") or "Unknown",
        "url": result.get("link") or result.get("url"),
        "duration": result.get("duration") or 0,
        "thumb": result.get("thumbnail") or result.get("thumb"),
        "views": result.get("views"),
        "req": user.mention,
        "req_name": user.first_name or "User",
        "user_id": user.id,
        "file_path": None,
        "bot_id": client.me.id,
    }

    try:
        pos = add_to_queue(chat_id, song_info)
    except ValueError as e:
        return await status_msg.edit_text(f"❌ {e}")

    state.stats["users_served"].add(user.id)
    state.stats["groups_served"].add(chat_id)

    if pos == 0:
        await play_music_core(client, chat_id, song_info, status_msg)
    else:
        queue_text = (
            f"<b>✨ Added to queue</b>\n\n"
            f"<b>❍ Title:</b> {one_line_title(song_info['title'])}\n"
            f"<b>❍ Position:</b> #{pos}\n"
            f"<b>❍ Duration:</b> {format_time(parse_duration_str(str(song_info.get('duration', 0))))}"
        )
        await status_msg.edit_text(
            queue_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ Skip", callback_data="cb_skip"),
                InlineKeyboardButton("📜 Queue", callback_data="cb_queue"),
            ]]),
        )


async def vplay_command(client, message):
    # Same as play for now (audio stream); video streaming needs more PyTgCalls setup
    return await play_command(client, message)


async def stop_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    chat_id = message.chat.id
    await stop_playback(client, chat_id, by_user=message.from_user)
    user_html = mention_html(message.from_user.id, message.from_user.first_name or "User")
    await message.reply_text(
        f"⏹ Stream stopped by {user_html}.",
        parse_mode=ParseMode.HTML,
    )


async def skip_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    ok, msg = await skip_playback(client, message.chat.id)
    await message.reply_text(msg)


async def pause_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    try:
        await call_py.pause(message.chat.id)
        state.paused_chats.add(message.chat.id)
        await message.reply_text("⏸ <b>Paused.</b>", parse_mode=ParseMode.HTML)
    except Exception:
        await message.reply_text("❌ Nothing is playing or already paused.")


async def resume_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    try:
        await call_py.resume(message.chat.id)
        state.paused_chats.discard(message.chat.id)
        await message.reply_text("▶️ <b>Resumed.</b>", parse_mode=ParseMode.HTML)
    except Exception:
        await message.reply_text("❌ Nothing to resume.")


async def clear_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    clear_queue(message.chat.id, keep_current=True)
    await message.reply_text("🗑 <b>Queue cleared</b> (current song kept).", parse_mode=ParseMode.HTML)


async def queue_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    q = get_queue(message.chat.id)
    if not q:
        return await message.reply_text("📭 Queue is empty.")
    lines = ["<b>📜 Queue</b>\n"]
    for i, s in enumerate(q[:15]):
        marker = "▶️" if i == 0 else f"`{i}.`"
        title = one_line_title(s.get("title"), 40)
        dur = format_time(parse_duration_str(str(s.get("duration", 0))))
        req = s.get("req_name") or "User"
        lines.append(f"{marker} <b>{title}</b> [{dur}] — {req}")
    if len(q) > 15:
        lines.append(f"\n… and {len(q) - 15} more")
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def nowplaying_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    chat_id = message.chat.id
    song = current_song(chat_id)
    if not song:
        return await message.reply_text("❌ Nothing is playing.")
    meta = state.now_playing_meta.get(chat_id) or {}
    import time
    elapsed = time.time() - meta.get("start", time.time())
    total = meta.get("duration") or parse_duration_str(str(song.get("duration", 0)))
    bar = get_progress_bar(elapsed, total)
    status = "⏸ Paused" if chat_id in state.paused_chats else "▶️ Playing"
    text = (
        f"<b>{status}</b>\n\n"
        f"🎧 {one_line_title(song.get('title'))}\n"
        f"{bar}\n"
        f"Queue: {queue_count(chat_id)} track(s)"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)


async def seek_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /seek &lt;seconds&gt;", parse_mode=ParseMode.HTML)
    try:
        seconds = int(message.command[1])
        if seconds < 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Provide a positive integer (seconds).")
    try:
        await call_py.seek_stream(message.chat.id, seconds)
        await message.reply_text(f"⏩ Seeked to {format_time(seconds)}")
    except Exception as e:
        await message.reply_text(f"❌ Seek failed: {e}")


async def loop_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    chat_id = message.chat.id
    arg = (message.command[1] if len(message.command) > 1 else "").lower()
    if arg in ("off", "0", "disable"):
        state.loop_mode[chat_id] = 0
        await message.reply_text("🔁 Loop <b>off</b>.", parse_mode=ParseMode.HTML)
    elif arg in ("1", "one", "current", "on"):
        state.loop_mode[chat_id] = 1
        await message.reply_text("🔁 Looping <b>current song</b>.", parse_mode=ParseMode.HTML)
    else:
        cur = state.loop_mode.get(chat_id, 0)
        state.loop_mode[chat_id] = 0 if cur else 1
        await message.reply_text(
            f"🔁 Loop {'on (current song)' if state.loop_mode[chat_id] else 'off'}.",
            parse_mode=ParseMode.HTML,
        )


async def shuffle_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    if shuffle_queue(message.chat.id):
        await message.reply_text("🔀 Queue shuffled.")
    else:
        await message.reply_text("❌ Not enough songs to shuffle.")


async def autoplay_command(client, message):
    if _group_only(message):
        return await message.reply_text("⚠️ This command can only be used in a group.")
    if not await can_control(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You don't have permission.")
    chat_id = message.chat.id
    if chat_id in state.autoplay_chats:
        state.autoplay_chats.discard(chat_id)
        await message.reply_text("🔁 AutoPlay <b>disabled</b>.", parse_mode=ParseMode.HTML)
    else:
        state.autoplay_chats.add(chat_id)
        await message.reply_text("🔁 AutoPlay <b>enabled</b>. Related tracks will play when queue ends.", parse_mode=ParseMode.HTML)


async def fav_command(client, message):
    user_id = message.from_user.id
    song = None
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        song = current_song(message.chat.id)
    if not song:
        return await message.reply_text("❌ No song playing to favourite. Use in a group while music plays.")
    if add_favourite(user_id, song):
        await message.reply_text(f"❤️ Added to favourites:\n<b>{one_line_title(song.get('title'))}</b>", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("ℹ️ Already in your favourites.")


async def unfav_command(client, message):
    user_id = message.from_user.id
    song = current_song(message.chat.id) if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) else None
    if not song:
        return await message.reply_text("❌ No current song. Specify while a song is playing.")
    if remove_favourite(user_id, song.get("url") or ""):
        await message.reply_text("💔 Removed from favourites.")
    else:
        await message.reply_text("ℹ️ Not in your favourites.")


async def lyrics_command(client, message):
    query = " ".join(message.command[1:]).strip()
    if not query and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        song = current_song(message.chat.id)
        if song:
            query = song.get("title") or ""
    if not query:
        return await message.reply_text("Usage: /lyrics &lt;song name&gt;", parse_mode=ParseMode.HTML)
    status = await message.reply_text("🔎 Searching lyrics...")
    lyrics = await get_lyrics(query)
    if not lyrics:
        return await status.edit_text("❌ Lyrics not found.")
    text = f"<b>🎤 Lyrics — {one_line_title(query)}</b>\n\n<code>{lyrics[:3500]}</code>"
    await status.edit_text(text, parse_mode=ParseMode.HTML)
