from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from core.playback import play_music_core
from handlers.music import (
    stop_playback, skip_command, pause_command, resume_command,
    clear_command, queue_command, shuffle_command, loop_command
)
import state


async def callback_handler(client, query: CallbackQuery):
    data = query.data
    chat_id = query.message.chat.id

    if data == "progress":
        return await query.answer("🎵 Playback is active.")

    if data == "show_help":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 Music", callback_data="help_music")],
            [InlineKeyboardButton("🛡️ Admin", callback_data="help_admin")],
            [InlineKeyboardButton("🏠 Back", callback_data="go_back")],
        ])
        return await query.message.edit_text(
            "📖 <b>COPYx MUSIC Commands</b>\n\nChoose a section:",
            parse_mode=ParseMode.HTML, reply_markup=kb
        )

    if data == "go_back":
        from handlers.system import start_handler
        await query.answer()
        return await start_handler(client, query.message)

    if data == "help_music":
        text = (
            "<blockquote>🎵 <b>Music Commands</b></blockquote>\n\n"
            "<code>/play song</code> — Search and play\n"
            "<code>/skip</code> — Skip current track\n"
            "<code>/stop</code> — Stop and clear\n"
            "<code>/pause</code> — Pause\n"
            "<code>/resume</code> — Resume\n"
            "<code>/queue</code> — Show queue\n"
            "<code>/clear</code> — Clear upcoming songs\n"
            "<code>/shuffle</code> — Shuffle queue\n"
            "<code>/loop</code> — Toggle loop"
        )
        return await query.message.edit_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_help")]])
        )

    if data == "help_admin":
        return await query.message.edit_text(
            "<blockquote>🛡️ <b>Group Commands</b></blockquote>\n\n"
            "Music controls are available to all group members.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_help")]])
        )

    actions = {
        "stop": stop_playback,
        "skip": lambda cid: skip_command(client, query.message),
        "pause": lambda cid: pause_command(client, query.message),
        "resume": lambda cid: resume_command(client, query.message),
        "queue": lambda cid: queue_command(client, query.message),
        "shuffle": lambda cid: shuffle_command(client, query.message),
        "loop": lambda cid: loop_command(client, query.message),
        "clear": lambda cid: clear_command(client, query.message),
    }
    if data in actions:
        try:
            if data == "stop":
                await stop_playback(chat_id)
                await query.message.edit_text(
                    f"⏹ <b>Stream stopped by <a href='tg://user?id={query.from_user.id}'>{query.from_user.first_name}</a>.</b>",
                    parse_mode=ParseMode.HTML,
                )
            else:
                await actions[data](chat_id)
            return await query.answer("✅ Done")
        except Exception as e:
            return await query.answer(f"Error: {str(e)[:150]}", show_alert=True)

    if data == "refresh":
        await query.answer("🔄 Refreshed")
        return

    if data == "close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return await query.answer("Closed")

    await query.answer()
