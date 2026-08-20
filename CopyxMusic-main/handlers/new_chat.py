import os
import time
from html import escape

from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from config import BOT_BRAND, CHANNEL_URL, ADD_GROUP_URL, WELCOME_IMAGE


def _mention(user):
    if not user:
        return "Unknown"
    return f"<a href='tg://user?id={user.id}'>{escape(user.first_name or 'User')}</a>"


def _font(size, bold=False):
    candidates = [
        "assets/DejaVuSans-Bold.ttf" if bold else "assets/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


async def _make_group_card(client, message):
    """Create a small dynamic card from the user's supplied COPYx welcome artwork."""
    out = os.path.join("downloads", f"group_welcome_{message.chat.id}_{int(time.time()*1000)}.png")
    os.makedirs("downloads", exist_ok=True)
    base = Image.open(WELCOME_IMAGE).convert("RGBA").resize((1280, 853))

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    panel = (50, 560, 1230, 825)
    d.rounded_rectangle(panel, radius=30, fill=(4, 8, 25, 220), outline=(80, 190, 255, 230), width=3)

    chat_name = message.chat.title or "Group"
    added = message.from_user
    user_name = added.first_name if added else "Unknown"
    username = f"@{added.username}" if added and added.username else "None"
    lines = [
        f"Welcome • {chat_name[:34]}",
        f"Added by: {user_name[:28]}",
        f"ID: {added.id if added else 'Unknown'}",
        f"Username: {username[:28]}",
        f"Powered by {BOT_BRAND}",
    ]
    d.text((85, 590), lines[0], font=_font(34, True), fill=(245, 250, 255, 255))
    y = 640
    for line in lines[1:]:
        d.text((90, y), line, font=_font(25, False), fill=(220, 235, 255, 255))
        y += 42

    # Add the adder's profile photo when Telegram exposes one.
    avatar_path = None
    try:
        if added and added.photo:
            avatar_path = await client.download_media(
                added.photo.big_file_id,
                file_name=os.path.join("downloads", f"avatar_{added.id}_{int(time.time()*1000)}.jpg"),
            )
    except Exception:
        avatar_path = None

    if avatar_path and os.path.exists(avatar_path):
        try:
            avatar = Image.open(avatar_path).convert("RGB").resize((150, 150))
            mask = Image.new("L", (150, 150), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 150, 150), fill=255)
            overlay.paste(avatar, (1080, 600), mask)
        except Exception:
            pass

    final = Image.alpha_composite(base, overlay).convert("RGB")
    final.save(out, "PNG", optimize=True)
    if avatar_path and os.path.exists(avatar_path):
        try:
            os.remove(avatar_path)
        except OSError:
            pass
    return out


async def new_chat_member(client, message):
    if not message.new_chat_members:
        return
    if not any(m.id == client.me.id for m in message.new_chat_members):
        return

    state.known_groups.add(message.chat.id)
    added_by = message.from_user
    username = f"@{message.chat.username}" if message.chat.username else "Private Group"
    text = (
        f"𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 <b>{escape(message.chat.title or 'Group')}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖\n"
        f"๏ 𝗡𝗔𝗠𝗘 ➠ {_mention(added_by)}\n"
        f"๏ 𝗜𝗗 ➠ <code>{added_by.id if added_by else 'Unknown'}</code>\n"
        f"๏ 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 ➠ @{escape(added_by.username) if added_by and added_by.username else 'None'}\n"
        f"๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ <a href='{CHANNEL_URL}'>{escape(BOT_BRAND)}</a>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👥 <b>GROUP</b> ➠ {escape(message.chat.title or 'Group')}\n"
        f"🔗 <b>TYPE</b> ➠ {username}"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me", url=ADD_GROUP_URL)]])

    card = None
    try:
        card = await _make_group_card(client, message)
        await message.reply_photo(card, caption=text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        try:
            await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass
    finally:
        if card and os.path.exists(card):
            try:
                os.remove(card)
            except OSError:
                pass
