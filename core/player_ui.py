from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.helpers import one_line_title, format_time, mention_html, yt_link_html, get_progress_bar
from config import BOT_NAME
import state


def build_player_caption(song_info, position=1, total_in_queue=1, elapsed=0):
    title = song_info.get("title") or "Unknown"
    url = song_info.get("url") or song_info.get("link") or ""
    duration = song_info.get("duration") or 0
    try:
        duration = int(duration)
    except Exception:
        duration = 0
    req_name = song_info.get("req_name") or "User"
    req_id = song_info.get("user_id")
    views = song_info.get("views")

    title_html = yt_link_html(title, url)
    if req_id:
        req_html = mention_html(req_id, req_name)
    else:
        req_html = song_info.get("req") or req_name

    lines = [
        f"<b>🎧 ╾⃝⃤𝘾𝙊𝙋𝙔 ✘ 𝙈𝙐𝙎𝙄𝘾 · ᴍᴜsɪᴄ sᴛʀᴇᴀᴍɪɴɢ</b>",
        "",
        f"🎵 <b>Now Playing</b>",
        f"🎧 {title_html}",
        f"⏱ Duration: {format_time(duration)}",
        f"ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ: {req_html}",
    ]
    if views:
        try:
            v = int(views)
            if v >= 1_000_000:
                vstr = f"{v/1_000_000:.1f}M"
            elif v >= 1_000:
                vstr = f"{v/1_000:.1f}K"
            else:
                vstr = str(v)
            lines.append(f"👁 Views: {vstr}")
        except Exception:
            pass
    lines.append("📺 Source: YouTube")
    lines.append(f"📍 Queue: #{position}")
    lines.append(f"🎵 Queue count: {total_in_queue}")
    return "\n".join(lines)


def build_control_keyboard(chat_id, elapsed=0, total=0):
    is_paused = chat_id in state.paused_chats
    auto_on = chat_id in state.autoplay_chats
    loop_on = state.loop_mode.get(chat_id, 0) > 0

    play_pause = (
        InlineKeyboardButton("▶️", callback_data="cb_resume")
        if is_paused
        else InlineKeyboardButton("⏸", callback_data="cb_pause")
    )

    row1 = [
        play_pause,
        InlineKeyboardButton("🔄", callback_data="cb_replay"),
        InlineKeyboardButton("⏭", callback_data="cb_skip"),
        InlineKeyboardButton("⏹", callback_data="cb_stop"),
    ]
    row2 = [
        InlineKeyboardButton("💡 Suggest", callback_data="cb_suggest"),
        InlineKeyboardButton("❤️ Fav", callback_data="cb_fav"),
        InlineKeyboardButton(
            "🔁 AUTO" if auto_on else "🔁 Auto",
            callback_data="cb_autoplay",
        ),
    ]
    row3 = [
        InlineKeyboardButton("📜 Queue", callback_data="cb_queue"),
        InlineKeyboardButton("🎤 Lyrics", callback_data="cb_lyrics"),
        InlineKeyboardButton("🔀 Shuffle", callback_data="cb_shuffle"),
    ]
    row4 = [
        InlineKeyboardButton("❌ CLOSE", callback_data="cb_close"),
    ]
    # Optional progress row
    if total > 0:
        bar = get_progress_bar(elapsed, total)
        rows = [
            [InlineKeyboardButton(bar, callback_data="cb_progress")],
            row1, row2, row3, row4,
        ]
    else:
        rows = [row1, row2, row3, row4]
    return InlineKeyboardMarkup(rows)


def start_private_caption(user_name, bot_username):
    return (
        f"✨ <b>HELLO {user_name}</b>\n\n"
        f"🎵 <b>╾⃝⃤𝘾𝙊𝙋𝙔 ✘ 𝙈𝙐𝙎𝙄𝘾</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎧 High Quality Music Streaming\n"
        f"⚡ Fast voice-chat playback\n"
        f"🎶 Smart queue + controls\n"
        f"🛡️ Admin protected controls\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"•── ⋅ ⋅  ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•"
    )


def start_private_buttons(bot_username, owner_url, support_url, updates_url):
    add_url = f"https://t.me/{bot_username}?startgroup=true"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 CHAT WITH ME 🟢", url=f"https://t.me/{bot_username}")],
        [
            InlineKeyboardButton("🔵 HELP & CMDS", callback_data="show_help"),
            InlineKeyboardButton("🔵 SUPPORT", url=support_url),
        ],
        [
            InlineKeyboardButton("🔵 UPDATES", url=updates_url),
            InlineKeyboardButton("🔴 Owner", url=owner_url),
        ],
        [InlineKeyboardButton("🟢 ➕ ADD ME TO GROUP ➕", url=add_url)],
    ])


def welcome_caption(chat_title, chat_id, username):
    uname = f"@{username}" if username else "Private"
    return (
        f"<b>𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 {chat_title}</b>\n\n"
        f"➖➖➖➖➖➖➖➖➖➖➖\n\n"
        f"๏ <b>𝗡𝗔𝗠𝗘</b> ➠ {chat_title}\n"
        f"๏ <b>𝗜𝗗</b> ➠ <code>{chat_id}</code>\n"
        f"๏ <b>𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄</b> ➠ {uname}\n"
        f"๏ <b>𝐌𝐀𝐃𝐄 𝐁𝐘</b> ➠ <a href=\"https://t.me/CopymusicOfficial\">COPYxMUSIC</a>\n\n"
        f"➖➖➖➖➖➖➖➖➖➖➖"
    )


def welcome_buttons(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ADD ME TO GROUP", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("📢 Updates", url="https://t.me/CopymusicOfficial")],
    ])
