import asyncio
import logging
import os
import time
import urllib.parse

import aiohttp
import yt_dlp

from config import COOKIES_FILE, DOWNLOAD_API_BASE, SEARCH_API_URL, DOWNLOAD_DIR, SEARCH_CACHE_TTL
import state

logger = logging.getLogger(__name__)

_YDL_BASE = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "extract_flat": False,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}


def _cookies_opts():
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        return {"cookiefile": COOKIES_FILE}
    return {}


def _extract_meta(info):
    if not info:
        return None
    # Handle playlist/search result wrappers
    if "entries" in info and info["entries"]:
        info = info["entries"][0]
    vid = info.get("id") or info.get("url")
    url = info.get("webpage_url") or info.get("original_url")
    if not url and vid and not str(vid).startswith("http"):
        url = f"https://www.youtube.com/watch?v={vid}"
    if not url:
        url = info.get("url")
    duration = info.get("duration") or 0
    try:
        duration = int(duration)
    except Exception:
        duration = 0
    thumb = None
    thumbs = info.get("thumbnails") or []
    if thumbs:
        thumb = thumbs[-1].get("url")
    thumb = thumb or info.get("thumbnail")
    return {
        "title": info.get("title") or "Unknown",
        "link": url,
        "url": url,
        "duration": duration,
        "thumbnail": thumb,
        "thumb": thumb,
        "views": info.get("view_count"),
        "channel": info.get("channel") or info.get("uploader"),
        "id": vid,
    }


async def fetch_youtube_link(query: str):
    """Search YouTube. Prefer external API, fall back to yt-dlp."""
    q = (query or "").strip()
    if not q:
        return None

    # Cache
    now = time.time()
    cached = state.search_cache.get(q.lower())
    if cached and now - cached[0] < SEARCH_CACHE_TTL:
        return cached[1]

    # Direct URL
    if "youtube.com" in q or "youtu.be" in q:
        result = await _ytdlp_extract(q)
        if result:
            state.search_cache[q.lower()] = (now, result)
            return result

    # External search API
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SEARCH_API_URL}/search?q={urllib.parse.quote(q)}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status == 200:
                    data = await response.json()
                    item = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else None
                    if item and (item.get("link") or item.get("url")):
                        result = {
                            "title": item.get("title") or "Unknown",
                            "link": item.get("link") or item.get("url"),
                            "url": item.get("link") or item.get("url"),
                            "duration": item.get("duration") or 0,
                            "thumbnail": item.get("thumbnail") or item.get("thumb"),
                            "thumb": item.get("thumbnail") or item.get("thumb"),
                            "views": item.get("views"),
                            "channel": item.get("channel"),
                        }
                        state.search_cache[q.lower()] = (now, result)
                        # Bound cache size
                        if len(state.search_cache) > 200:
                            oldest = sorted(state.search_cache.items(), key=lambda x: x[1][0])[:50]
                            for k, _ in oldest:
                                state.search_cache.pop(k, None)
                        return result
    except Exception as e:
        logger.warning(f"Search API failed: {e}")

    # yt-dlp search fallback
    result = await _ytdlp_search(q)
    if result:
        state.search_cache[q.lower()] = (now, result)
    return result


async def _ytdlp_search(query: str):
    def _run():
        opts = {
            **_YDL_BASE,
            **_cookies_opts(),
            "format": "bestaudio/best",
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            return _extract_meta(info)

    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)
    except Exception as e:
        logger.warning(f"yt-dlp search failed: {e}")
        return None


async def _ytdlp_extract(url: str):
    def _run():
        opts = {
            **_YDL_BASE,
            **_cookies_opts(),
            "format": "bestaudio/best",
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return _extract_meta(info)

    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)
    except Exception as e:
        logger.warning(f"yt-dlp extract failed: {e}")
        return None


async def fetch_related(video_id_or_url: str, limit=5):
    """Best-effort related songs via ytsearch of title."""
    try:
        meta = await _ytdlp_extract(video_id_or_url) if "http" in str(video_id_or_url) else None
        title = (meta or {}).get("title") or video_id_or_url
        # Search similar
        def _run():
            opts = {
                **_YDL_BASE,
                **_cookies_opts(),
                "format": "bestaudio/best",
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{title}", download=False)
                entries = (info or {}).get("entries") or []
                results = []
                for e in entries:
                    m = _extract_meta(e)
                    if m and m.get("url"):
                        results.append(m)
                return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)
    except Exception as e:
        logger.warning(f"related failed: {e}")
        return []


async def _download_via_api(youtube_url):
    try:
        unique = str(time.time()).replace(".", "")
        final_path = os.path.join(DOWNLOAD_DIR, f"{unique}.mp3")
        endpoint = f"{DOWNLOAD_API_BASE}/download?url={urllib.parse.quote(youtube_url)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    return None
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = await resp.json()
                    direct_url = data.get("url") or data.get("link") or data.get("download_url")
                    if not direct_url:
                        return None
                    async with session.get(direct_url, timeout=aiohttp.ClientTimeout(total=120)) as audio_resp:
                        if audio_resp.status != 200:
                            return None
                        with open(final_path, "wb") as f:
                            async for chunk in audio_resp.content.iter_chunked(65536):
                                f.write(chunk)
                else:
                    with open(final_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(65536):
                            f.write(chunk)
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            return final_path
        return None
    except Exception as e:
        logger.warning(f"Download API failed: {e}")
        return None


def _yt_download(youtube_url, output_template):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
        **_cookies_opts(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])


async def _download_via_ytdlp(youtube_url):
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        unique = str(time.time()).replace(".", "")
        output_template = os.path.join(DOWNLOAD_DIR, f"{unique}.%(ext)s")
        final_path = os.path.join(DOWNLOAD_DIR, f"{unique}.mp3")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _yt_download, youtube_url, output_template)
        if os.path.exists(final_path):
            return final_path
        for ext in ("m4a", "webm", "opus", "ogg", "mp3"):
            alt = os.path.join(DOWNLOAD_DIR, f"{unique}.{ext}")
            if os.path.exists(alt):
                return alt
        return None
    except Exception as e:
        logger.warning(f"yt-dlp failed: {e}")
        return None


async def download_song(youtube_url):
    if DOWNLOAD_API_BASE:
        result = await _download_via_api(youtube_url)
        if result:
            return result
        logger.info("Download API failed, falling back to yt-dlp")
    return await _download_via_ytdlp(youtube_url)


async def get_lyrics(title: str):
    """Best-effort lyrics via public lyrics.ovh API (no key required)."""
    try:
        # Split artist - title if possible
        parts = title.split(" - ", 1)
        if len(parts) == 2:
            artist, song = parts[0].strip(), parts[1].strip()
        else:
            artist, song = " ", title.strip()
        url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(song)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = (data.get("lyrics") or "").strip()
                    if lyrics:
                        # Bound size
                        if len(lyrics) > 3500:
                            lyrics = lyrics[:3500] + "\n…"
                        return lyrics
    except Exception as e:
        logger.warning(f"lyrics failed: {e}")
    return None
