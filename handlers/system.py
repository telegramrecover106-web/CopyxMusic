import os
import sys
import time

import aiohttp
import psutil
from pyrogram import Client as PyroClient
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from config import (
    API_ID, API_HASH, MAIN_OWNER, OWNER_ID, SEARCH_API_URL,
    SUPPORT_URL, UPDATES_URL, OWNER_URL, BOT_NAME,
)
from core.database import load_stats, save_group_user_counts
from core.guards import check_abuse, is_owner
from core.helpers import get_readable_time, to_bold_unicode
from core.player_ui import start_private_caption, start_private_buttons


async def ping_handler(client, message):
    start = time.time()
    response = await message.reply_text("🏓 **Pinging...**")
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
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent

    msg = (
        f"🏓 <b>Pong!</b>\n\n"
        f"📱 <b>Telegram:</b> <code>{tg_ping}ms</code>\n"
        f"🔍 <b>Search API:</b> <code>{api_ping}</code>\n\n"
        f"<b>💻 System</b>\n"
        f"├ Uptime: <code>{uptime}</code>\n"
        f"├ CPU: <code>{cpu}%</code>\n"
        f"└ RAM: <code>{mem}%</code>"
    )
    await response.edit_text(msg, parse_mode=ParseMode.HTML)


async def stats_handler(client, message):
    uptime = get_readable_time(int(time.time() - state.bot_start_time))
    persisted = load_stats()
    songs = max(persisted.get("songs_played", 0), state.stats.get("songs_played", 0))
    groups = len(state.stats.get("groups_served", set()))
    users = len(state.stats.get("users_served", set()))
    active_vc = len(state.vc_active)
    queued = sum(len(q) for q in state.chat_queues.values())
    try:
        save_group_user_counts(groups, users)
    except Exception:
        pass
    text = (
        f"<b>📊 {BOT_NAME} Stats</b>\n\n"
        f"⏱ Uptime: <code>{uptime}</code>\n"
        f"🎵 Songs played: <code>{songs}</code>\n"
        f"👥 Groups: <code>{groups}</code>\n"
        f"👤 Users: <code>{users}</code>\n"
        f"🔊 Active VCs: <code>{active_vc}</code>\n"
        f"📜 Queued tracks: <code>{queued}</code>\n"
        f"🤖 Active bots: <code>{len(state.active_clients)}</code>"
    )
    await message.reply_text(text, parse_mode=ParseMode.HTML)


async def restart_handler(client, message):
    if not await is_owner(message.from_user.id):
        return await message.reply_text("❌ Owner only.")
    await message.reply_text("♻️ Restarting…")
    # Graceful-ish exit; process manager / Replit should restart
    try:
        from clients import call_py, user_app
        from core.assistant import safe_leave_call
        for cid in list(state.vc_active):
            await safe_leave_call(call_py, cid)
        await call_py.stop()
        await user_app.stop()
    except Exception:
        pass
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def start_handler(client, message):
    if message.from_user and await check_abuse(message.from_user.id):
        return

    # Group start
    if message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        bot_uname = client.me.username or "COPYxMUSIC_BOT"
        return await message.reply_text(
            f"🎵 <b>{BOT_NAME}</b> is online!\n\n"
            f"Use <code>/play song name</code> after starting a voice chat.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Add me", url=f"https://t.me/{bot_uname}?startgroup=true"),
            ]]),
        )

    user_name = (message.from_user.first_name if message.from_user else "User") or "User"
    bot_uname = client.me.username or "COPYxMUSIC_BOT"
    owner_url = OWNER_URL or f"tg://user?id={OWNER_ID or MAIN_OWNER}"
    caption = start_private_caption(user_name, bot_uname)
    buttons = start_private_buttons(bot_uname, owner_url, SUPPORT_URL, UPDATES_URL)
    try:
        await message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=buttons)
    except Exception:
        await message.reply_text(caption, parse_mode=ParseMode.HTML)


async def clone_command(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ <b>Usage:</b> <code>/clone BOT_TOKEN</code>",
            parse_mode=ParseMode.HTML,
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
        clone_count = len([c for c in state.active_clients.values() if not getattr(c, "is_main", False)])
        await status.edit_text(
            f"✅ <b>Bot cloned!</b>\n\n"
            f"🤖 @{me.username}\n"
            f"🔢 Total clones: <code>{clone_count}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await status.edit_text(f"❌ <b>Clone failed:</b>\n<code>{e}</code>", parse_mode=ParseMode.HTML)


async def active_bots_command(client, message):
    if message.from_user.id != MAIN_OWNER:
        return await message.reply_text("❌ Restricted to main owner.", parse_mode=ParseMode.HTML)
    if not state.active_clients:
        return await message.reply_text("❌ No active bots.")
    text = f"🌐 <b>Active Bots</b> — {len(state.active_clients)}\n\n"
    for _, c in state.active_clients.items():
        username = c.me.username if c.me else "Unknown"
        owner = getattr(c, "clone_owner", "Main")
        tag = "✅ Main" if getattr(c, "is_main", False) else f"🔗 Clone · {owner}"
        text += f"├ @{username} · {tag}\n"
    await message.reply_text(text, parse_mode=ParseMode.HTML)
