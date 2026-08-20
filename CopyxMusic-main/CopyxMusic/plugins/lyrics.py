import aiohttp
from urllib.parse import quote
from pyrogram import filters
from CopyxMusic import app, queue


@app.on_message(filters.command("lyrics") & filters.group)
async def lyrics(_, m):
    media=queue.get_current(m.chat.id)
    query=" ".join(m.command[1:]) if len(m.command)>1 else (media.title if media else "")
    if not query: return await m.reply_text("🎵 Usage: /lyrics <song name>")
    # LRCLIB is a public lyrics metadata service; failures are handled cleanly.
    parts=query.split(" - ",1)
    artist,title=(parts[0],parts[1]) if len(parts)==2 else ("",query)
    url=f"https://lrclib.net/api/get?artist_name={quote(artist)}&track_name={quote(title)}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url,timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status!=200: raise RuntimeError("not found")
                data=await r.json()
        text=data.get("plainLyrics") or data.get("syncedLyrics")
        if not text: raise RuntimeError("empty")
        await m.reply_text(f"<b>🎵 Lyrics — {query}</b>\n\n{text[:3800]}")
    except Exception:
        await m.reply_text("❌ Lyrics not found for this song.")
