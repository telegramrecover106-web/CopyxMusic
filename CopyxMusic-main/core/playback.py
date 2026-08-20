import asyncio
import logging
import os
import time
from html import escape

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserAlreadyParticipant
from pytgcalls import filters as fl
from pytgcalls.types import StreamEnded

import state
from clients import call_py, user_app
from core.api import download_song
from core.helpers import get_progress_bar, one_line_title, parse_duration_str
from config import BOT_BRAND, ADD_GROUP_URL

logger = logging.getLogger(__name__)

_ASSISTANT_JOIN_ERRORS = (
    "peeridinvalid", "peer_id_invalid", "channelprivate",
    "not in chat", "usernotparticipant", "groupcallinvalid",
    "invalid peer", "chatadminrequired", "channelinvalid",
    "channel_invalid", "no active group call",
)


async def _try_join_assistant(client, chat_id, status_msg):
    try:
        if status_msg:
            await status_msg.edit_text("🔄 <b>Assistant detected as missing — joining...</b>", parse_mode=ParseMode.HTML)
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception:
            link_obj = await client.create_chat_invite_link(chat_id)
            invite_link = link_obj.invite_link
        try:
            await user_app.join_chat(invite_link)
        except UserAlreadyParticipant:
            pass
        except Exception as join_err:
            err_s = str(join_err).lower()
            if any(x in err_s for x in ("expired", "invalid", "hash")):
                new_link = await client.create_chat_invite_link(chat_id)
                await user_app.join_chat(new_link.invite_link)
            else:
                raise
        await asyncio.sleep(1.2)
        return True
    except Exception as e:
        logger.warning("Assistant join failed for %s: %s", chat_id, e)
        return False


def _control_keyboard(chat_id, song):
    paused = chat_id in state.paused_chats
    pause_label = "▶️ Resume" if paused else "⏸ Pause"
    pause_data = "resume" if paused else "pause"
    rows = [
        [InlineKeyboardButton(pause_label, callback_data=pause_data),
         InlineKeyboardButton("⏭ Skip", callback_data="skip")],
        [InlineKeyboardButton("⏹ Stop", callback_data="stop"),
         InlineKeyboardButton("📜 Queue", callback_data="queue")],
        [InlineKeyboardButton("🔀 Shuffle", callback_data="shuffle"),
         InlineKeyboardButton("🔁 Loop", callback_data="loop")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
         InlineKeyboardButton("➕ Add Me", url=ADD_GROUP_URL)],
    ]
    if song.get("url"):
        rows.append([
            InlineKeyboardButton("▶️ Open on YouTube", url=song["url"]),
            InlineKeyboardButton("✖️ Close", callback_data="close")
        ])
    else:
        rows.append([InlineKeyboardButton("✖️ Close", callback_data="close")])
    return InlineKeyboardMarkup(rows)


async def update_progress_caption(chat_id, message, start_time, total_duration, base_caption, song):
    try:
        while True:
            elapsed = min(time.time() - start_time, total_duration) if total_duration else 0
            keyboard = _control_keyboard(chat_id, song)
            try:
                await message.edit_caption(
                    caption=base_caption,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                try:
                    await message.edit_text(
                        text=base_caption,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    break
            if total_duration and elapsed >= total_duration:
                break
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Progress updater failed")


async def play_music_core(client, chat_id, song_info, status_msg=None, retry_attempt=False):
    try:
        file_path = song_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            if status_msg:
                await status_msg.edit_text("⬇️ <b>Downloading audio...</b>", parse_mode=ParseMode.HTML)
            file_path = await download_song(song_info["url"])
            if not file_path or not os.path.exists(file_path):
                if status_msg:
                    await status_msg.edit_text("❌ <b>Download failed.</b>", parse_mode=ParseMode.HTML)
                if state.chat_queues.get(chat_id):
                    state.chat_queues[chat_id].pop(0)
                return
            song_info["file_path"] = file_path

        if status_msg:
            try:
                await status_msg.edit_text("🎧 <b>Starting playback...</b>", parse_mode=ParseMode.HTML)
            except Exception:
                pass

        try:
            await call_py.play(chat_id, file_path)
        except Exception as e:
            if any(k in str(e).lower() for k in _ASSISTANT_JOIN_ERRORS) and not retry_attempt:
                if await _try_join_assistant(client, chat_id, status_msg):
                    return await play_music_core(client, chat_id, song_info, status_msg, True)
            if status_msg:
                await status_msg.edit_text(
                    "❌ <b>Playback failed.</b>\n\n"
                    f"<code>{escape(str(e))}</code>",
                    parse_mode=ParseMode.HTML,
                )
            return

        old = state.progress_tasks.pop(chat_id, None)
        if old:
            old.cancel()
        state.paused_chats.discard(chat_id)

        title = one_line_title(song_info.get("title", "Unknown"))
        duration = parse_duration_str(song_info.get("duration", "0"))
        youtube = song_info.get("url", "")
        title_link = f"<a href='{youtube}'>{escape(title)}</a>" if youtube else escape(title)
        requester = song_info.get("req", "Unknown")

        base_caption = (
            f"🎧 ╾⃝⃤ <b>{escape(BOT_BRAND)}</b> · ᴍᴜsɪᴄ sᴛʀᴇᴀᴍɪɴɢ\n\n"
            f"🎵 <b>Now Playing</b>\n\n"
            f"🎧 {title_link}\n\n"
            f"⏱ <b>Duration:</b> {escape(song_info.get('duration','Unknown'))}\n"
            f"ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ: {requester}"
        )
        keyboard = _control_keyboard(chat_id, song_info)

        try:
            await status_msg.delete()
        except Exception:
            pass

        player_message = None
        thumb = song_info.get("thumb")
        if thumb and str(thumb).startswith(("http://", "https://")):
            try:
                player_message = await client.send_photo(
                    chat_id, photo=thumb, caption=base_caption,
                    reply_markup=keyboard, parse_mode=ParseMode.HTML,
                )
            except Exception:
                player_message = None
        if player_message is None:
            player_message = await client.send_message(
                chat_id, base_caption, reply_markup=keyboard,
                parse_mode=ParseMode.HTML, disable_web_page_preview=True,
            )

        if player_message:
            state.progress_tasks[chat_id] = asyncio.create_task(
                update_progress_caption(
                    chat_id, player_message, time.time(), duration, base_caption, song_info
                )
            )

    except Exception as e:
        logger.exception("Playback error in %s", chat_id)
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"❌ <b>Error:</b> <code>{escape(str(e))}</code>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass


@call_py.on_update(fl.stream_end())
async def on_stream_end(_, update: StreamEnded):
    chat_id = update.chat_id
    task = state.progress_tasks.pop(chat_id, None)
    if task:
        task.cancel()

    queue = state.chat_queues.get(chat_id, [])
    if not queue:
        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass
        return

    finished = queue.pop(0)
    fp = finished.get("file_path")
    if fp and os.path.exists(fp):
        try: os.remove(fp)
        except OSError: pass

    # If loop is enabled, put the finished track back at the front.
    if chat_id in state.loop_chats:
        finished["file_path"] = None
        queue.insert(0, finished)

    if queue:
        bot = state.active_clients.get(queue[0].get("bot_id")) or next(iter(state.active_clients.values()), None)
        if bot:
            await play_music_core(bot, chat_id, queue[0])
    else:
        state.chat_queues.pop(chat_id, None)
        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass
