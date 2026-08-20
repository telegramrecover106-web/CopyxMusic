from pyrogram import filters, types
from CopyxMusic import app, db, queue, yt


@app.on_message(filters.command("fav") & filters.group)
async def fav(_, m: types.Message):
    media=queue.get_current(m.chat.id)
    if not media: return await m.reply_text("⚠️ Nothing is playing right now.")
    await db.add_favourite(m.from_user.id, media)
    await m.reply_text(f"❤️ Added {media.title} to your favourites.")


@app.on_message(filters.command("unfav") & filters.group)
async def unfav(_, m: types.Message):
    media=queue.get_current(m.chat.id)
    if not media: return await m.reply_text("⚠️ Nothing is playing right now.")
    ok=await db.remove_favourite(m.from_user.id, media.title)
    await m.reply_text("💔 Removed from favourites." if ok else "⚠️ That song is not in your favourites.")


@app.on_message(filters.command(["favorites","favourites"]))
async def favourites(_, m: types.Message):
    items=await db.get_favourites(m.from_user.id)
    if not items: return await m.reply_text("❤️ Your favourites are empty. Use /fav while a song is playing.")
    lines=["<b>❤️ Your Favourites</b>",""]
    for i,x in enumerate(items,1):
        lines.append(f"{i}. <a href=\"{x.get('url','')}\">{x.get('title','Unknown')}</a> — {x.get('duration','')}" )
    await m.reply_text("\n".join(lines),disable_web_page_preview=True)


@app.on_message(filters.command("history"))
async def history(_, m: types.Message):
    doc=await db.db.history.find_one({"_id":m.from_user.id}) or {}
    items=(doc.get("items") or [])[-20:][::-1]
    if not items: return await m.reply_text("🕘 No playback history yet.")
    lines=["<b>🕘 Playback History</b>",""]
    for i,x in enumerate(items,1):
        lines.append(f"{i}. <a href=\"{x.get('url','')}\">{x.get('title','Unknown')}</a> — {x.get('duration','')}" )
    await m.reply_text("\n".join(lines),disable_web_page_preview=True)
