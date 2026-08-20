import time
import os
import aiohttp
from pyrogram import Client as PyroClient
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from config import (
    API_ID, API_HASH, MAIN_OWNER, SEARCH_API_URL, BOT_BRAND,
    CHANNEL_URL, ADD_GROUP_URL, SUPPORT_URL, WELCOME_IMAGE
)
from core.guards import check_abuse
from core.helpers import get_readable_time, to_bold_unicode


def _user_mention(user):
    if not user:
        return "Unknown"
    return f"<a href='tg://user?id={user.id}'>{user.first_name or 'User'}</a>"


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
    await response.edit_text(
        f"🏓 <b>Pong!</b>\n\n"
        f"📱 <b>Telegram:</b> <code>{tg_ping}ms</code>\n"
        f"🔍 <b>Search API:</b> <code>{api_ping}</code>\n\n"
        f"<blockquote>💻 <b>System</b>\n"
        f"├ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"├ <b>CPU:</b> <code>{__import__('psutil').cpu_percent()}%</code>\n"
        f"├ <b>RAM:</b> <code>{__import__('psutil').virtual_memory().percent}%</code>\n"
        f"└ <b>Disk:</b> <code>{__import__('psutil').disk_usage('/').percent}%</code></blockquote>",
        parse_mode=ParseMode.HTML,
    )


async def start_handler(client, message):
    if message.from_user and await check_abuse(message.from_user.id):
        return await message.reply_text("⏳ Please wait a moment and try again.")

    private = message.chat.type == "private"
    user = _user_mention(message.from_user)
    bot_name = to_bold_unicode(BOT_BRAND)

    caption = (
        f"✨ <b>HELLO {user}</b>\n\n"
        f"🎵 <b>{bot_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎧 High Quality Music Streaming\n"
        f"⚡ Fast voice-chat playback\n"
        f"🎶 Smart queue + controls\n"
        f"🛡️ Admin protected controls\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"•── ⋅ ⋅ ────── ⋅᯽⋅ ────── ⋅ ⋅ ⋅──•"
    )

    buttons = [
        [InlineKeyboardButton("➕ Add Me", url=ADD_GROUP_URL)],
        [
            InlineKeyboardButton("📖 Commands", callback_data="show_help"),
            InlineKeyboardButton("📢 Updates", url=CHANNEL_URL),
        ],
        [
            InlineKeyboardButton("💬 Support", url=SUPPORT_URL),
            InlineKeyboardButton("👑 Owner", url=f"tg://user?id={MAIN_OWNER}"),
        ],
    ]

    # Telegram can send a local file only when the bot process has the asset.
    try:
        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=not private,
        )
    except Exception:
        await message.reply_text(
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=not private,
        )


async def clone_command(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ <b>Usage:</b> <code>/clone BOT_TOKEN</code>", parse_mode=ParseMode.HTML
        )
    token = message.command[1]
    status = await message.reply_text("⏳ <b>Initializing clone...</b>", parse_mode=ParseMode.HTML)
    try:
        new_client = PyroClient(
            f"clone_{token.split(':')[0]}", api_id=API_ID, api_hash=API_HASH, bot_token=token
        )
        await new_client.start()
        me = await new_client.get_me()
        new_client.clone_owner = user_id
        new_client.is_main = False
        from handlers.router import register_handlers
        register_handlers(new_client)
        state.active_clients[me.id] = new_client
        await status.edit_text(
            f"✅ <b>Bot cloned successfully!</b>\n\n"
            f"<blockquote>🤖 <b>Bot:</b> @{me.username}\n"
            f"👑 <b>Owner:</b> <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await status.edit_text(f"❌ <b>Clone failed:</b>\n<code>{e}</code>", parse_mode=ParseMode.HTML)


async def active_bots_command(client, message):
    if message.from_user.id != MAIN_OWNER:
        return await message.reply_text("❌ Restricted to main owner.")
    if not state.active_clients:
        return await message.reply_text("❌ No active bots found.")
    text = f"🌐 <b>Active Bots</b> — {len(state.active_clients)}\n\n"
    for _, c in state.active_clients.items():
        username = c.me.username if c.me else "Unknown"
        owner = getattr(c, "clone_owner", "Main")
        text += f"• @{username} · Owner: <code>{owner}</code>\n"
    await message.reply_text(text, parse_mode=ParseMode.HTML)
