from pyrogram import filters
from CopyxMusic import app, config, db, queue
from CopyxMusic.helpers import thumb, buttons


@app.on_message(filters.command("nowplaying") & filters.group)
async def nowplaying(_, m):
    media=queue.get_current(m.chat.id)
    if not media: return await m.reply_text("🎵 Nothing is playing.")
    played=getattr(media,"time",0); dur=getattr(media,"duration_sec",0)
    bar_len=12; filled=int(bar_len*played/dur) if dur else 0
    bar="▰"*filled+"▱"*(bar_len-filled)
    text=(f"🎧 <b>COPY ✘ MUSIC · ᴍᴜsɪᴄ sᴛʀᴇᴀᴍɪɴɢ</b>\n\n"
          f"🎵 <b>Now Playing</b>\n\n"
          f"🎧 <a href=\"{media.url}\"><b>{media.title}</b></a>\n\n"
          f"⏱ Duration: {media.duration}\n"
          f"⏱ {bar}\n"
          f"ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ: {media.user or 'Unknown'}\n"
          f"👁 Views: {getattr(media,'view_count',None) or 'N/A'}\n"
          f"📺 Source: YouTube")
    try:
        image=await thumb.generate(media)
        await m.reply_photo(image,caption=text,reply_markup=buttons.controls(m.chat.id,timer=f"{played//60:02d}:{played%60:02d} / {media.duration}"))
    except Exception:
        await m.reply_text(text,reply_markup=buttons.controls(m.chat.id))
