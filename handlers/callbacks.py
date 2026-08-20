import asyncio

from pyrogram.enums import ParseMode
from pyrogram.errors import MessageIdInvalid, MessageNotModified
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import state
from clients import call_py
from core.api import fetch_related, get_lyrics
from core.database import add_favourite
from core.guards import can_control
from core.helpers import one_line_title, format_time, parse_duration_str
from core.playback import play_music_core, stop_playback, skip_playback
from core.queue import get_queue, clear_queue, shuffle_queue, current_song, add_to_queue
from handlers.system import start_handler


async def callback_handler(client, query: CallbackQuery):
    data = query.data or ""
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    try:
        await _handle(client, query, data, chat_id, user_id)
    except MessageNotModified:
        try:
            await query.answer()
        except Exception:
            pass
    except MessageIdInvalid:
        try:
            await query.answer("Message expired.", show_alert=True)
        except Exception:
            pass
    except Exception as e:
        try:
            await query.answer(f"Error: {str(e)[:100]}", show_alert=True)
        except Exception:
            pass


async def _handle(client, query, data, chat_id, user_id):
    if data == "cb_progress":
        return await query.answer("🎵 Live playback")

    if data == "cb_close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return await query.answer()

    if data == "show_help":
        buttons = [
            [
                InlineKeyboardButton("🎵 Music", callback_data="help_music"),
                InlineKeyboardButton("⚙️ More", callback_data="help_more"),
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="go_back")],
        ]
        return await query.message.edit_text(
            "📜 <b>Commands</b>\n\nChoose a category:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    if data == "go_back":
        return await start_handler(client, query.message)

    if data == "help_music":
        return await query.message.edit_text(
            "<b>🎵 Music Commands</b>\n\n"
            "<code>/play</code> — Play song or URL\n"
            "<code>/vplay</code> — Play (video mode)\n"
            "<code>/skip</code> — Skip current\n"
            "<code>/stop</code> — Stop & clear\n"
            "<code>/pause</code> / <code>/resume</code>\n"
            "<code>/queue</code> — Show queue\n"
            "<code>/nowplaying</code> — Now playing\n"
            "<code>/seek</code> — Seek seconds\n"
            "<code>/loop</code> — Loop current\n"
            "<code>/shuffle</code> — Shuffle queue\n"
            "<code>/autoplay</code> — Toggle autoplay\n"
            "<code>/lyrics</code> — Song lyrics\n"
            "<code>/fav</code> / <code>/unfav</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_help")]]),
        )

    if data == "help_more":
        return await query.message.edit_text(
            "<b>⚙️ System</b>\n\n"
            "<code>/ping</code> — Latency\n"
            "<code>/stats</code> — Bot stats\n"
            "<code>/restart</code> — Owner only",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_help")]]),
        )

    # Playback controls
    control_keys = {
        "cb_pause", "cb_resume", "cb_skip", "cb_stop", "cb_replay",
        "cb_autoplay", "cb_shuffle", "cb_queue", "cb_fav", "cb_lyrics", "cb_suggest",
        "stop", "skip", "pause", "resume", "clear",
    }
    if data in control_keys or data.startswith("suggest_"):
        if data in ("cb_pause", "cb_resume", "cb_skip", "cb_stop", "cb_replay",
                    "cb_autoplay", "cb_shuffle", "stop", "skip", "pause", "resume", "clear"):
            if not await can_control(client, chat_id, user_id):
                return await query.answer("❌ No permission", show_alert=True)

    if data in ("cb_pause", "pause"):
        try:
            await call_py.pause(chat_id)
            state.paused_chats.add(chat_id)
            await query.answer("⏸ Paused")
        except Exception:
            await query.answer("Nothing playing", show_alert=True)
        return

    if data in ("cb_resume", "resume"):
        try:
            await call_py.resume(chat_id)
            state.paused_chats.discard(chat_id)
            await query.answer("▶️ Resumed")
        except Exception:
            await query.answer("Nothing to resume", show_alert=True)
        return

    if data in ("cb_skip", "skip"):
        ok, msg = await skip_playback(client, chat_id)
        await query.answer(msg[:200])
        return

    if data in ("cb_stop", "stop"):
        await stop_playback(client, chat_id, by_user=query.from_user)
        try:
            await query.message.edit_text(
                f"⏹ Stream stopped by {query.from_user.mention}.",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        await query.answer("Stopped")
        return

    if data == "cb_replay":
        song = current_song(chat_id)
        if not song:
            return await query.answer("Nothing playing", show_alert=True)
        # Restart current by seeking to 0 or re-play
        try:
            await call_py.seek_stream(chat_id, 0)
            await query.answer("🔄 Replaying")
        except Exception:
            asyncio.create_task(play_music_core(client, chat_id, song))
            await query.answer("🔄 Replaying")
        return

    if data == "cb_autoplay":
        if chat_id in state.autoplay_chats:
            state.autoplay_chats.discard(chat_id)
            await query.answer("AutoPlay OFF")
        else:
            state.autoplay_chats.add(chat_id)
            await query.answer("AutoPlay ON")
        return

    if data == "cb_shuffle":
        if shuffle_queue(chat_id):
            await query.answer("🔀 Shuffled")
        else:
            await query.answer("Not enough songs", show_alert=True)
        return

    if data == "cb_queue":
        q = get_queue(chat_id)
        if not q:
            return await query.answer("Queue empty", show_alert=True)
        lines = ["📜 Queue\n"]
        for i, s in enumerate(q[:10]):
            lines.append(f"{i}. {one_line_title(s.get('title'), 35)}")
        await query.answer()
        try:
            await query.message.reply_text("\n".join(lines))
        except Exception:
            pass
        return

    if data == "cb_fav":
        song = current_song(chat_id)
        if not song:
            return await query.answer("Nothing playing", show_alert=True)
        if add_favourite(user_id, song):
            await query.answer("❤️ Added to favourites")
        else:
            await query.answer("Already favourited")
        return

    if data == "cb_lyrics":
        song = current_song(chat_id)
        if not song:
            return await query.answer("Nothing playing", show_alert=True)
        await query.answer("Searching lyrics...")
        lyrics = await get_lyrics(song.get("title") or "")
        if not lyrics:
            try:
                await query.message.reply_text("❌ Lyrics not found.")
            except Exception:
                pass
            return
        try:
            await query.message.reply_text(
                f"<b>🎤 {one_line_title(song.get('title'))}</b>\n\n<code>{lyrics[:3500]}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        return

    if data == "cb_suggest":
        song = current_song(chat_id)
        if not song:
            return await query.answer("Nothing playing", show_alert=True)
        await query.answer("Finding suggestions...")
        related = await fetch_related(song.get("url") or song.get("title") or "", limit=5)
        if not related:
            return await query.message.reply_text("❌ No suggestions found.")
        buttons = []
        for i, r in enumerate(related[:5]):
            title = one_line_title(r.get("title"), 30)
            buttons.append([InlineKeyboardButton(
                f"🎵 {title}",
                callback_data=f"suggest_{i}",
            )])
        # Stash related in state briefly
        state.related_cache[chat_id] = related
        await query.message.reply_text(
            "💡 <b>Suggestions</b> — tap to queue:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("suggest_"):
        try:
            idx = int(data.split("_")[1])
        except Exception:
            return await query.answer("Invalid")
        related = state.related_cache.get(chat_id) or []
        if idx >= len(related):
            return await query.answer("Expired", show_alert=True)
        r = related[idx]
        song = {
            "title": r.get("title"),
            "url": r.get("url") or r.get("link"),
            "duration": r.get("duration") or 0,
            "thumb": r.get("thumb") or r.get("thumbnail"),
            "req": query.from_user.mention,
            "req_name": query.from_user.first_name or "User",
            "user_id": user_id,
            "file_path": None,
            "bot_id": client.me.id,
        }
        try:
            pos = add_to_queue(chat_id, song)
        except ValueError as e:
            return await query.answer(str(e), show_alert=True)
        if pos == 0:
            asyncio.create_task(play_music_core(client, chat_id, song))
            await query.answer("▶ Playing")
        else:
            await query.answer(f"Queued #{pos}")
        return

    if data == "clear":
        clear_queue(chat_id, keep_current=True)
        await query.answer("Queue cleared")
        return

    try:
        await query.answer()
    except Exception:
        pass
