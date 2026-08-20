import asyncio
import logging
import os
import time

from pyrogram.enums import ParseMode
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytgcalls import filters as fl
from pytgcalls.types import StreamEnded

import state
from clients import call_py, user_app
from core.api import download_song
from core.helpers import get_progress_bar, one_line_title, parse_duration_str, format_time, html_escape

logger = logging.getLogger(__name__)
_ASSISTANT_JOIN_ERRORS = ("peeridinvalid", "peer_id_invalid", "channelprivate", "not in chat", "usernotparticipant", "groupcallinvalid", "invalid peer", "chatadminrequired", "channelinvalid", "channel_invalid", "chat_admin_required")


async def _try_join_assistant(client, chat_id, status_msg):
    try:
        if status_msg:
            await status_msg.edit_text("💃 <b>ᴄᴏɴɴᴇᴄᴛɪɴɢ...</b>", parse_mode=ParseMode.HTML)
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
            if any(x in str(join_err).lower() for x in ("expired", "invalid", "hash")):
                new_link = await client.create_chat_invite_link(chat_id)
                await user_app.join_chat(new_link.invite_link)
            else:
                raise
        await asyncio.sleep(0.3)
        return True
    except Exception as e:
        logger.warning("Assistant join failed for %s: %s", chat_id, e)
        return False


def _build_control_keyboard(chat_id, progress_bar):
    paused = chat_id in state.paused_chats
    auto = chat_id not in state.auto_mode_chats
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(progress_bar, callback_data="progress")],
        [InlineKeyboardButton("▶️", callback_data="resume"), InlineKeyboardButton("⏸️", callback_data="pause"), InlineKeyboardButton("🔄", callback_data="restart"), InlineKeyboardButton("⏭️", callback_data="skip"), InlineKeyboardButton("⏹️", callback_data="stop")],
        [InlineKeyboardButton("Suggest", callback_data="suggest"), InlineKeyboardButton("FAV", callback_data="fav"), InlineKeyboardButton(f"🔁 AUTO {'ON' if auto else 'OFF'}", callback_data="auto")],
        [InlineKeyboardButton("📋 QUEUE", callback_data="queue_panel")],
        [InlineKeyboardButton("✖ CLOSE", callback_data="close")],
    ])


async def update_progress_caption(chat_id, message, start_time, total_duration, base_caption):
    try:
        while True:
            elapsed = time.time() - start_time
            if total_duration > 0 and elapsed > total_duration: elapsed = total_duration
            try:
                await message.edit_caption(caption=base_caption, reply_markup=_build_control_keyboard(chat_id, get_progress_bar(elapsed, total_duration)), parse_mode=ParseMode.HTML)
            except Exception as e:
                if "MESSAGE_NOT_MODIFIED" not in str(e): break
            if total_duration > 0 and elapsed >= total_duration: break
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Progress update error: %s", e)


async def play_music_core(client, chat_id, song_info, status_msg=None, retry_attempt=False):
    try:
        file_path = song_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            if status_msg:
                await status_msg.edit_text("💃 <b>ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...</b>\n▰▰▰▰▱▱▱▱▱▱", parse_mode=ParseMode.HTML)
            file_path = await download_song(song_info["url"])
            if not file_path or not os.path.exists(file_path):
                if status_msg: await status_msg.edit_text("❌ <b>Download failed.</b>", parse_mode=ParseMode.HTML)
                if state.chat_queues.get(chat_id):
                    state.chat_queues[chat_id].pop(0)
                return
            song_info["file_path"] = file_path

        if status_msg:
            await status_msg.edit_text("💃 <b>ᴘʟᴀʏɪɴɢ...</b> ✨", parse_mode=ParseMode.HTML)

        try:
            await call_py.play(chat_id, file_path)
        except Exception as e:
            if any(k in str(e).lower() for k in _ASSISTANT_JOIN_ERRORS) and not retry_attempt:
                if await _try_join_assistant(client, chat_id, status_msg):
                    return await play_music_core(client, chat_id, song_info, status_msg, retry_attempt=True)
            ast_mention = f"@{state.ASSISTANT_USERNAME}" if state.ASSISTANT_USERNAME else "the assistant"
            if status_msg:
                await status_msg.edit_text(f"❌ <b>Playback failed:</b>\n<code>{html_escape(e)}</code>\n\nAdd {ast_mention} to this group and retry.", parse_mode=ParseMode.HTML)
            return

        if chat_id in state.progress_tasks:
            state.progress_tasks[chat_id].cancel(); state.progress_tasks.pop(chat_id, None)
        state.paused_chats.discard(chat_id)
        state.active_voice_chats.add(chat_id)

        title = html_escape(one_line_title(song_info.get("title")))
        yt = html_escape(song_info.get("url") or "")
        total_duration = parse_duration_str(song_info.get("duration", "0"))
        title_link = f"<a href='{yt}'>{title}</a>" if yt.startswith("http") else title
        duration_text = format_time(total_duration) if total_duration > 0 else str(song_info.get('duration') or '0')
        base_caption = (
            "<blockquote><b>🎧 ╾⃝⃤𝘾𝙊𝙋𝙔 ✘ 𝙈𝙐𝙎𝙄𝘾 · ᴍᴜsɪᴄ sᴛʀᴇᴀᴍɪɴɢ</b></blockquote>\n\n"
            "<b>🎵 Now Playing</b>\n\n"
            f"🎧 <b>{title_link}</b>\n\n"
            f"⏱ <b>Duration:</b> <code>{html_escape(duration_text)}</code>\n"
            f"👤 <b>ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:</b> {song_info.get('req') or 'User'}"
        )
        keyboard = _build_control_keyboard(chat_id, get_progress_bar(0, total_duration))
        if status_msg:
            try: await status_msg.delete()
            except Exception: pass

        player_message = None
        if song_info.get("thumb") and song_info["thumb"].startswith("http"):
            try:
                player_message = await client.send_photo(chat_id, photo=song_info["thumb"], caption=base_caption, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except Exception: pass
        if not player_message:
            player_message = await client.send_message(chat_id, base_caption, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        task = asyncio.create_task(update_progress_caption(chat_id, player_message, time.time(), total_duration, base_caption))
        state.progress_tasks[chat_id] = task
    except Exception as e:
        logger.error("Playback error in chat %s: %s", chat_id, e)
        if status_msg:
            try: await status_msg.edit_text(f"❌ <b>Error:</b> <code>{html_escape(e)}</code>", parse_mode=ParseMode.HTML)
            except Exception: pass


@call_py.on_update(fl.stream_end())
async def on_stream_end(_, update: StreamEnded):
    chat_id = update.chat_id
    task = state.progress_tasks.pop(chat_id, None)
    if task: task.cancel()
    if not state.chat_queues.get(chat_id):
        state.active_voice_chats.discard(chat_id)
        try: await call_py.leave_call(chat_id)
        except Exception: pass
        return
    finished = state.chat_queues[chat_id].pop(0)
    fp = finished.get("file_path")
    if fp and os.path.exists(fp):
        try: os.remove(fp)
        except Exception: pass
    if state.chat_queues.get(chat_id):
        if chat_id in state.auto_mode_chats:
            state.active_voice_chats.discard(chat_id)
            try: await call_py.leave_call(chat_id)
            except Exception: pass
            return
        next_song = state.chat_queues[chat_id][0]
        target_client = state.active_clients.get(next_song.get("bot_id"))
        if target_client:
            await play_music_core(target_client, chat_id, next_song)
    else:
        state.active_voice_chats.discard(chat_id)
        try: await call_py.leave_call(chat_id)
        except Exception: pass
