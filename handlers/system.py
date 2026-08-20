import os
import time

import aiohttp
import psutil
from pyrogram import Client as PyroClient
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from config import API_ID, API_HASH, MAIN_OWNER, SEARCH_API_URL, CHANNEL_URL, ADD_BOT_URL, SUPPORT_URL
from core.guards import check_abuse
from core.helpers import get_readable_time, to_bold_unicode, html_escape
from core.welcome import make_welcome_image


def _mention(user):
    name = html_escape(getattr(user, "first_name", None) or "User")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


async def ping_handler(client, message):
    start = time.time()
    response = await message.reply_text("🏓 <b>Pinging...</b>", parse_mode=ParseMode.HTML)
    tg_ping = round((time.time() - start) * 1000)
    api_ping = "N/A"
    try:
        api_start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(SEARCH_API_URL, timeout=aiohttp.ClientTimeout(total=5)):
                pass
        api_ping = f"{round((time.time() - api_start) * 1000)}ms"
    except Exception:
        api_ping = "Timeout"
    uptime = get_readable_time(int(time.time() - state.bot_start_time))
    cpu = psutil.cpu_percent(); mem = psutil.virtual_memory().percent; disk = psutil.disk_usage("/").percent
    msg = (f"🏓 <b>Pong!</b>\n\n📱 <b>Telegram:</b> <code>{tg_ping}ms</code>\n"
           f"🔍 <b>Search API:</b> <code>{api_ping}</code>\n\n"
           f"<blockquote>💻 <b>System</b>\n├ <b>Uptime:</b> <code>{uptime}</code>\n"
           f"├ <b>CPU:</b> <code>{cpu}%</code>\n├ <b>RAM:</b> <code>{mem}%</code>\n└ <b>Disk:</b> <code>{disk}%</code></blockquote>")
    await response.edit_text(msg, parse_mode=ParseMode.HTML)


async def start_handler(client, message):
    if await check_abuse(message.from_user.id):
        return
    user = message.from_user
    user_link = _mention(user)
    bot_name_bold = to_bold_unicode((client.me.first_name or "COPYx MUSIC").upper())
    caption = (
        f"✨ <b>HELLO</b> {user_link} 👋\n\n"
        f"🎵 <b>╾⃝⃤𝘾𝙊𝙋𝙔 ✘ 𝙈𝙐𝙎𝙄𝘾</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎧 <b>High Quality Music Streaming</b>\n"
        f"⚡ Fast voice-chat playback\n"
        f"🎶 Smart queue + controls\n"
        f"🛡️ Admin protected controls\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"•── ⋅ ⋅  ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•")
    buttons = [
        [InlineKeyboardButton("➕ ADD ME TO GROUP ➕", url=ADD_BOT_URL)],
        [InlineKeyboardButton("🔵 HELP & CMDS", callback_data="show_help"), InlineKeyboardButton("🔵 CHANNEL", url=CHANNEL_URL)],
        [InlineKeyboardButton("🔵 SUPPORT", url=SUPPORT_URL), InlineKeyboardButton("🟥 OWNER", url="tg://user?id=6983361101")],
        [InlineKeyboardButton("🔵 LANGUAGE", callback_data="language")],
    ]
    image_path = os.path.join("downloads", f"start_{client.me.id}.jpg")
    try:
        # Start image is a static branded card; welcome images are dynamic.
        from core.welcome import BASE_IMAGE
        await message.reply_photo(BASE_IMAGE, caption=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        await message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))


async def welcome_new_members(client, message):
    members = getattr(message, "new_chat_members", None) or []
    if not members:
        return
    group_name = getattr(message.chat, "title", None) or "Telegram Group"
    for member in members:
        if getattr(member, "is_deleted", False):
            continue
        avatar = None
        try:
            if getattr(getattr(member, "photo", None), "big_file_id", None):
                avatar = await client.download_media(member.photo.big_file_id, file_name=f"downloads/welcome_avatar_{member.id}.jpg")
        except Exception:
            avatar = None
        try:
            out = f"downloads/welcome_{message.chat.id}_{member.id}.jpg"
            make_welcome_image(member, group_name, out, avatar)
            username = f"@{member.username}" if member.username else "@N/A"
            text = (f"𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 <b>{html_escape(group_name)}</b> 🎉\n"
                    f"➖➖➖➖➖➖➖➖➖➖➖\n"
                    f"๏ 𝗡𝗔𝗠𝗘 ➠ {_mention(member)}\n"
                    f"๏ 𝗜𝗗 ➠ <code>{member.id}</code>\n"
                    f"๏ 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 ➠ <a href='tg://user?id={member.id}'>{html_escape(username)}</a>\n"
                    f"๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ <a href='{CHANNEL_URL}'>COPYx MUSIC</a>\n"
                    f"➖➖➖➖➖➖➖➖➖➖➖")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("⊕ ADD ME ⊕", url=ADD_BOT_URL)]])
            await message.reply_photo(out, caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception as e:
            await message.reply_text(f"𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 <b>{html_escape(group_name)}</b> 🎉\n๏ 𝗡𝗔𝗠𝗘 ➠ {_mention(member)}\n๏ 𝗜𝗗 ➠ <code>{member.id}</code>\n๏ 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 ➠ {html_escape('@'+member.username if member.username else '@N/A')}\n๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ <a href='{CHANNEL_URL}'>COPYx MUSIC</a>", parse_mode=ParseMode.HTML)
        finally:
            if avatar and os.path.exists(avatar):
                try: os.remove(avatar)
                except Exception: pass
            if 'out' in locals() and os.path.exists(out):
                try: os.remove(out)
                except Exception: pass


async def video_chat_event_handler(client, message):
    """Handle ONLY Telegram's voice/video-chat lifecycle service messages.

    This is deliberately paired with dedicated custom filters in router.py.
    Using the broad `filters.service` filter here caused the generic welcome
    service handler to consume the update before this handler could see it.
    """
    started = getattr(message, "video_chat_started", None)
    ended = getattr(message, "video_chat_ended", None)

    if started is not None:
        # Mark the chat active immediately so /play can be used on the very
        # next message, even before PyTgCalls has joined the call.
        state.active_voice_chats.add(message.chat.id)
        await message.reply_text(
            "😍 <b>ᴠɪᴅᴇᴏ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ🥳</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if ended is not None:
        from handlers.music import reset_chat_playback
        await reset_chat_playback(client, message.chat.id, delete_files=True)
        await message.reply_text(
            "😕 <b>ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ💔</b>\n"
            "<b>Queue and playback records have been cleared.</b>",
            parse_mode=ParseMode.HTML,
        )


async def clone_command(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply_text("❌ <b>Usage:</b> <code>/clone BOT_TOKEN</code>", parse_mode=ParseMode.HTML)
    token = message.command[1]
    status = await message.reply_text("⏳ <b>Initializing clone...</b>", parse_mode=ParseMode.HTML)
    try:
        new_client = PyroClient(f"clone_{token.split(':')[0]}", api_id=API_ID, api_hash=API_HASH, bot_token=token)
        await new_client.start(); me = await new_client.get_me()
        new_client.clone_owner = user_id; new_client.is_main = False
        from handlers.router import register_handlers
        register_handlers(new_client); state.active_clients[me.id] = new_client
        clone_count = len([c for c in state.active_clients.values() if not getattr(c, "is_main", False)])
        await status.edit_text(f"✅ <b>Bot cloned successfully!</b>\n\n🤖 @{me.username}\n👑 Owner: <code>{user_id}</code>\n🔢 Clones: <code>{clone_count}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await status.edit_text(f"❌ <b>Clone failed:</b>\n<code>{e}</code>", parse_mode=ParseMode.HTML)


async def active_bots_command(client, message):
    if message.from_user.id != MAIN_OWNER:
        return await message.reply_text("❌ <b>Restricted to main owner.</b>", parse_mode=ParseMode.HTML)
    if not state.active_clients:
        return await message.reply_text("❌ <b>No active bots found.</b>", parse_mode=ParseMode.HTML)
    text = f"🌐 <b>Active Bots</b> — Total: {len(state.active_clients)}\n\n"
    for _, c in state.active_clients.items():
        username = c.me.username if c.me else "Unknown"; owner = getattr(c, "clone_owner", "Main")
        text += f"├ @{username} · {'✅ Main' if getattr(c, 'is_main', False) else f'🔗 Clone · Owner: <code>{owner}</code>'}\n"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


async def help_command(client, message):
    text = ("<blockquote>🎧 <b>MUSIC COMMANDS</b></blockquote>\n\n"
            "🎵 <code>/play song</code> — play music\n📋 <code>/queue</code> — show queue\n⏭ <code>/skip</code> — next track\n"
            "⏸ <code>/pause</code> — pause\n▶️ <code>/resume</code> — resume\n⏹ <code>/stop</code> — stop & clear\n"
            "🗑 <code>/clear</code> — clear queue\n🏓 <code>/ping</code> — bot status")
    await message.reply_text(text, parse_mode=ParseMode.HTML)
