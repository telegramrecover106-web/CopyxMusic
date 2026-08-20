from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import state
from core.playback import play_music_core
from handlers.music import clear_command, pause_command, resume_command, skip_command, stop_command, queue_command
from handlers.system import start_handler


async def callback_handler(client, query: CallbackQuery):
    data = query.data or ""
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if data == "progress":
        return await query.answer("🎵 Live Playback")
    if data == "language":
        return await query.answer("🌐 English / Hindi support can be added here.")
    if data == "suggest":
        return await query.answer("💡 Use /play <song> to add a suggestion.", show_alert=True)
    if data == "fav":
        items = state.chat_queues.get(chat_id, [])
        if not items:
            return await query.answer("❌ Nothing is playing.", show_alert=True)
        item = items[0]
        favs = state.favourite_tracks.setdefault(user_id, [])
        url = item.get("url")
        if url in favs:
            favs.remove(url); return await query.answer("💔 Removed from FAV")
        favs.append(url); return await query.answer("❤️ Added to FAV")
    if data == "auto":
        if chat_id in state.auto_mode_chats:
            state.auto_mode_chats.discard(chat_id); await query.answer("🔁 Auto-play ON")
        else:
            state.auto_mode_chats.add(chat_id); await query.answer("🔁 Auto-play OFF")
        return
    if data == "queue_panel":
        return await queue_command(client, query.message)
    if data == "close":
        try: await query.message.delete()
        except Exception: pass
        return await query.answer("Closed")
    if data == "restart":
        items = state.chat_queues.get(chat_id, [])
        if not items:
            return await query.answer("❌ Nothing is playing.", show_alert=True)
        item = items[0]
        await query.answer("🔄 Restarting...")
        await play_music_core(client, chat_id, item)
        return
    if data == "verify_assistant":
        if state.chat_queues.get(chat_id):
            await query.answer("🔄 Retrying playback...")
            await play_music_core(client, chat_id, state.chat_queues[chat_id][0], query.message)
        else:
            await query.answer("❌ Queue is empty.", show_alert=True)
        return
    if data == "show_help":
        buttons = [[InlineKeyboardButton("🎵 Music", callback_data="help_music"), InlineKeyboardButton("🛡️ Admin", callback_data="help_admin")], [InlineKeyboardButton("🏠 Back", callback_data="go_back")]]
        return await query.message.edit_text("📜 <b>Commands</b>\n\nChoose a category:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
    if data == "go_back":
        return await start_handler(client, query.message)
    if data == "help_music":
        return await query.message.edit_text("<blockquote>🎵 <b>Music Commands</b></blockquote>\n\n<code>/play</code> — Play a song\n<code>/skip</code> — Skip\n<code>/stop</code> — Stop & clear\n<code>/pause</code> — Pause\n<code>/resume</code> — Resume\n<code>/queue</code> — Queue\n<code>/clear</code> — Clear queue", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_help")]]))
    if data == "help_admin":
        return await query.message.edit_text("<blockquote>🛡️ <b>Admin Commands</b></blockquote>\n\n<code>/kick</code> · <code>/ban</code> · <code>/unban</code> · <code>/mute</code> · <code>/unmute</code>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_help")]]))
    if data in {"stop", "skip", "pause", "resume", "clear"}:
        await query.answer()
        if data == "stop": await stop_command(client, query.message)
        elif data == "skip": await skip_command(client, query.message)
        elif data == "pause": await pause_command(client, query.message)
        elif data == "resume": await resume_command(client, query.message)
        elif data == "clear": await clear_command(client, query.message)
        return
