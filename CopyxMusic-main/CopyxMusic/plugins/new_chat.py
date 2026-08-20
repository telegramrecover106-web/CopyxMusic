import asyncio
from pyrogram import filters, types
from pyrogram.errors import ChatAdminRequired, FloodWait
from CopyxMusic import app, config, db, logger
from CopyxMusic.helpers._welcome import make_group_welcome

WELCOME_TEXT = """<blockquote><b>𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 {group}</b>

➖➖➖➖➖➖➖➖➖➖➖
๏ 𝗡𝗔𝗠𝗘 ➠ {name}
๏ 𝗜𝗗 ➠ <code>{user_id}</code>
๏ 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 ➠ {username}
๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ <a href="https://t.me/CopymusicOfficial">COPYxMUSIC</a>
➖➖➖➖➖➖➖➖➖➖➖</blockquote>"""


async def _group_link(chat):
    try:
        if chat.username: return f"https://t.me/{chat.username}"
        member=await app.get_chat_member(chat.id,app.id)
        if member.privileges and member.privileges.can_invite_users:
            return await app.export_chat_invite_link(chat.id)
    except Exception: pass
    return "Unavailable"


@app.on_message(filters.new_chat_members & filters.group, group=5)
async def bot_added(_, message: types.Message):
    if not message.new_chat_members: return
    for member in message.new_chat_members:
        if member.id != app.id: continue
        chat=message.chat; added_by=message.from_user
        await db.add_chat(chat.id)
        try:
            image=await make_group_welcome(chat,added_by)
            username=f"@{added_by.username}" if added_by and added_by.username else "—"
            caption=WELCOME_TEXT.format(group=chat.title or "Group",name=added_by.first_name if added_by else "Unknown",user_id=added_by.id if added_by else "—",username=username)
            await app.send_photo(chat.id,image,caption=caption)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.warning(f"Welcome send failed in {chat.id}: {e}")
        # Logger gets full chat metadata when configured.
        if config.LOGGER_ID:
            try:
                link=await _group_link(chat)
                count=await app.get_chat_members_count(chat.id)
                text=(f"🟢 <b>COPYxMUSIC added to a group</b>\n\n"
                      f"🔖 <b>Name:</b> {chat.title}\n🆔 <b>ID:</b> <code>{chat.id}</code>\n"
                      f"👤 <b>Username:</b> @{chat.username if chat.username else 'private'}\n"
                      f"🔗 <b>Link:</b> {link}\n👥 <b>Members:</b> {count}")
                await app.send_message(config.LOGGER_ID,text)
            except Exception: pass
        break


@app.on_message(filters.left_chat_member & filters.group, group=5)
async def bot_removed(_, message: types.Message):
    if not message.left_chat_member or message.left_chat_member.id != app.id: return
    await db.rm_chat(message.chat.id)
    if config.LOGGER_ID:
        try: await app.send_message(config.LOGGER_ID,f"🔴 <b>COPYxMUSIC removed</b>\n\n<b>{message.chat.title}</b>\n<code>{message.chat.id}</code>")
        except Exception: pass
