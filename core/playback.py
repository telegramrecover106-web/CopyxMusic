import asyncio
import logging
import os
import time

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageIdInvalid, MessageNotModified
from pytgcalls import filters as fl
from pytgcalls.types import StreamEnded

import state
from clients import call_py, user_app
from core.api import download_song, fetch_related
from core.assistant import ensure_assistant_in_chat, safe_leave_call
from core.database import add_history, bump_songs_played
from core.helpers import parse_duration_str, format_time
from core.player_ui import build_player_caption, build_control_keyboard
from core.queue import current_song, pop_current, queue_count, get_queue, clear_queue

logger = logging.getLogger(__name__)


async def has_active_voice_chat(client, chat_id) -> bool:
    """Best-effort detection of an active group voice/video chat."""
    # Prefer known state from service messages
    if chat_id in state.vc_active:
        return True
    # Try PyTgCalls / group call APIs when available
    try:
        # pytgcalls may expose group call info via the user client
        from pyrogram.raw.functions.phone import GetGroupCall
        from pyrogram.raw.types import InputGroupCall
        # Fallback: attempt to see if we can get call
        chat = await client.get_chat(chat_id)
        # Some clients store group_call on chat
        gc = getattr(chat, "group_call", None) or getattr(chat, "voice_chat", None)
        if gc:
            state.vc_active.add(chat_id)
            return True
    except Exception:
        pass
    # Last resort: try a lightweight play probe is too heavy; rely on play error
    return chat_id in state.vc_active


async def play_music_core(client, chat_id, song_info, status_msg=None, retry_attempt=False):
    lock = state.chat_locks[chat_id]
    async with lock:
        try:
            await _play_inner(client, chat_id, song_info, status_msg, retry_attempt)
        except Exception as e:
            logger.error(f"Playback error in chat {chat_id}: {e}")
            if status_msg:
                try:
                    await status_msg.edit_text(f"❌ <b>Error:</b> {e}", parse_mode=ParseMode.HTML)
                except Exception:
                    pass


async def _play_inner(client, chat_id, song_info, status_msg, retry_attempt):
    # 1. Download if needed
    file_path = song_info.get("file_path")
    if not file_path or not os.path.exists(file_path):
        if status_msg:
            try:
                await status_msg.edit_text("⬇️ <b>Downloading audio...</b>", parse_mode=ParseMode.HTML)
            except Exception:
                pass
        file_path = await download_song(song_info["url"])
        if not file_path or not os.path.exists(file_path):
            if status_msg:
                try:
                    await status_msg.edit_text("❌ <b>Download failed. Try another song.</b>", parse_mode=ParseMode.HTML)
                except Exception:
                    pass
            # Remove broken item and try next
            q = get_queue(chat_id)
            if q and q[0] is song_info:
                pop_current(chat_id)
            if get_queue(chat_id):
                asyncio.create_task(play_music_core(client, chat_id, get_queue(chat_id)[0], status_msg))
            return
        song_info["file_path"] = file_path

    # 2. Ensure assistant is present
    if status_msg:
        try:
            await status_msg.edit_text("🎧 <b>Starting playback...</b>", parse_mode=ParseMode.HTML)
        except Exception:
            pass

    async def _status(text):
        if status_msg:
            try:
                await status_msg.edit_text(text, parse_mode=ParseMode.HTML)
            except Exception:
                pass

    ok, err = await ensure_assistant_in_chat(client, chat_id, status_callback=_status)
    if not ok:
        if status_msg:
            try:
                await status_msg.edit_text(err or "❌ Assistant error", parse_mode=ParseMode.HTML)
            except Exception:
                pass
        return

    # 3. Play
    try:
        await call_py.play(chat_id, file_path)
    except Exception as e:
        err_s = str(e).lower()
        no_vc = any(k in err_s for k in (
            "no active", "not in a call", "groupcall", "group call",
            "no group call", "call not found", "not found",
        ))
        join_err = any(k in err_s for k in (
            "peeridinvalid", "peer_id_invalid", "channelprivate",
            "usernotparticipant", "not in chat", "chatadminrequired",
        ))

        if no_vc:
            state.vc_active.discard(chat_id)
            msg = (
                "📵 <b>No active voice chat found.</b>\n\n"
                "Please start a voice chat and try again.💔"
            )
            if status_msg:
                try:
                    await status_msg.edit_text(msg, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
            return

        if join_err and not retry_attempt:
            ok, err = await ensure_assistant_in_chat(client, chat_id, status_callback=_status)
            if ok:
                return await _play_inner(client, chat_id, song_info, status_msg, retry_attempt=True)

        if status_msg:
            try:
                await status_msg.edit_text(
                    f"❌ <b>Playback failed:</b>\n<code>{e}</code>\n\n"
                    f"Make sure a voice chat is active and the assistant is in the group.",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
        return

    # 4. Success — update state & UI
    state.vc_active.add(chat_id)
    if chat_id in state.progress_tasks:
        state.progress_tasks[chat_id].cancel()
        del state.progress_tasks[chat_id]
    state.paused_chats.discard(chat_id)

    total_duration = parse_duration_str(str(song_info.get("duration", "0")))
    if not total_duration and isinstance(song_info.get("duration"), (int, float)):
        total_duration = int(song_info["duration"])

    start_ts = time.time()
    state.now_playing_meta[chat_id] = {
        "start": start_ts,
        "duration": total_duration,
        "title": song_info.get("title"),
        "url": song_info.get("url"),
        "user_id": song_info.get("user_id"),
    }

    q = get_queue(chat_id)
    caption = build_player_caption(
        song_info,
        position=1,
        total_in_queue=len(q),
        elapsed=0,
    )
    keyboard = build_control_keyboard(chat_id, 0, total_duration)

    if status_msg:
        try:
            await status_msg.delete()
        except Exception:
            pass

    player_message = None
    thumb = song_info.get("thumb") or song_info.get("thumbnail")
    if thumb and str(thumb).startswith("http"):
        try:
            player_message = await client.send_photo(
                chat_id,
                photo=thumb,
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            player_message = None

    if not player_message:
        try:
            player_message = await client.send_message(
                chat_id,
                caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Failed to send player: {e}")

    if player_message:
        state.player_messages[chat_id] = player_message
        task = asyncio.create_task(
            _progress_loop(chat_id, player_message, start_ts, total_duration, song_info)
        )
        state.progress_tasks[chat_id] = task

    # Stats / history
    try:
        bump_songs_played()
        state.stats["songs_played"] = state.stats.get("songs_played", 0) + 1
        state.stats["groups_served"].add(chat_id)
        if song_info.get("user_id"):
            state.stats["users_served"].add(song_info["user_id"])
        add_history({
            "title": song_info.get("title"),
            "url": song_info.get("url"),
            "duration": total_duration,
            "user_id": song_info.get("user_id"),
            "chat_id": chat_id,
        })
    except Exception:
        pass


async def _progress_loop(chat_id, message, start_time, total_duration, song_info):
    try:
        while True:
            elapsed = time.time() - start_time
            if total_duration > 0 and elapsed > total_duration + 2:
                break
            if chat_id in state.paused_chats:
                await asyncio.sleep(5)
                continue
            q = get_queue(chat_id)
            caption = build_player_caption(
                song_info,
                position=1,
                total_in_queue=len(q),
                elapsed=elapsed,
            )
            keyboard = build_control_keyboard(chat_id, elapsed, total_duration)
            try:
                if message.photo:
                    await message.edit_caption(
                        caption=caption, reply_markup=keyboard, parse_mode=ParseMode.HTML
                    )
                else:
                    await message.edit_text(
                        caption, reply_markup=keyboard, parse_mode=ParseMode.HTML
                    )
            except MessageNotModified:
                pass
            except (MessageIdInvalid, FloodWait):
                break
            except Exception as e:
                if "MESSAGE_NOT_MODIFIED" not in str(e).upper():
                    break
            await asyncio.sleep(12)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Progress update error: {e}")


async def stop_playback(client, chat_id, by_user=None):
    lock = state.chat_locks[chat_id]
    async with lock:
        if chat_id in state.progress_tasks:
            state.progress_tasks[chat_id].cancel()
            del state.progress_tasks[chat_id]
        state.paused_chats.discard(chat_id)
        state.now_playing_meta.pop(chat_id, None)
        # Clean files
        q = get_queue(chat_id)
        for song in q:
            fp = song.get("file_path")
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass
        clear_queue(chat_id, keep_current=False)
        await safe_leave_call(call_py, chat_id)
        state.player_messages.pop(chat_id, None)


async def skip_playback(client, chat_id):
    lock = state.chat_locks[chat_id]
    async with lock:
        if chat_id in state.progress_tasks:
            state.progress_tasks[chat_id].cancel()
            del state.progress_tasks[chat_id]
        state.paused_chats.discard(chat_id)

        done = pop_current(chat_id)
        if done:
            fp = done.get("file_path")
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass

        # Loop current?
        if state.loop_mode.get(chat_id, 0) == 1 and done:
            # Re-queue same song at front
            from core.queue import ensure_queue
            ensure_queue(chat_id).insert(0, {**done, "file_path": done.get("file_path")})

        nxt = current_song(chat_id)
        if nxt:
            asyncio.create_task(play_music_core(client, chat_id, nxt))
            return True, "⏭ Skipping..."

        # Autoplay
        if chat_id in state.autoplay_chats and done:
            related = await fetch_related(done.get("url") or done.get("title") or "", limit=3)
            if related:
                r = related[0]
                song = {
                    "title": r.get("title"),
                    "url": r.get("url") or r.get("link"),
                    "duration": r.get("duration") or 0,
                    "thumb": r.get("thumb") or r.get("thumbnail"),
                    "req": "AutoPlay",
                    "req_name": "AutoPlay",
                    "user_id": None,
                    "file_path": None,
                    "bot_id": client.me.id,
                }
                from core.queue import add_to_queue
                add_to_queue(chat_id, song)
                asyncio.create_task(play_music_core(client, chat_id, song))
                return True, "🔁 AutoPlay: next related track"

        await safe_leave_call(call_py, chat_id)
        state.now_playing_meta.pop(chat_id, None)
        return False, "✅ Queue ended."


@call_py.on_update(fl.stream_end())
async def on_stream_end(_, update: StreamEnded):
    chat_id = update.chat_id
    if chat_id in state.progress_tasks:
        state.progress_tasks[chat_id].cancel()
        del state.progress_tasks[chat_id]

    # Find a client for this chat
    target_client = None
    q = get_queue(chat_id)
    if q:
        bot_id = q[0].get("bot_id")
        target_client = state.active_clients.get(bot_id)
    if not target_client:
        for c in state.active_clients.values():
            target_client = c
            break

    if not target_client:
        await safe_leave_call(call_py, chat_id)
        return

    # Reuse skip logic
    success, _ = await skip_playback(target_client, chat_id)
    if not success:
        await safe_leave_call(call_py, chat_id)
