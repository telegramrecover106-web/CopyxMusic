"""Lightweight JSON persistence suitable for Replit."""
import json
import os
import time
from pathlib import Path

from config import DATA_DIR, MAX_HISTORY

_DATA = Path(DATA_DIR)
_FAV_FILE = _DATA / "favourites.json"
_HIST_FILE = _DATA / "history.json"
_SET_FILE = _DATA / "settings.json"
_STATS_FILE = _DATA / "stats.json"


def _ensure():
    _DATA.mkdir(parents=True, exist_ok=True)


def _load(path, default):
    _ensure()
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, data):
    _ensure()
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None)
    tmp.replace(path)


# ── Favourites ──────────────────────────────────────────

def get_favourites(user_id: int) -> list:
    data = _load(_FAV_FILE, {})
    return data.get(str(user_id), [])


def add_favourite(user_id: int, song: dict) -> bool:
    data = _load(_FAV_FILE, {})
    key = str(user_id)
    favs = data.get(key, [])
    url = song.get("url") or ""
    if any(f.get("url") == url for f in favs):
        return False
    favs.append({
        "title": song.get("title"),
        "url": url,
        "duration": song.get("duration"),
        "thumb": song.get("thumb"),
        "added_at": int(time.time()),
    })
    data[key] = favs[-100:]  # bound
    _save(_FAV_FILE, data)
    return True


def remove_favourite(user_id: int, url: str) -> bool:
    data = _load(_FAV_FILE, {})
    key = str(user_id)
    favs = data.get(key, [])
    new = [f for f in favs if f.get("url") != url]
    if len(new) == len(favs):
        return False
    data[key] = new
    _save(_FAV_FILE, data)
    return True


# ── History ─────────────────────────────────────────────

def add_history(entry: dict):
    hist = _load(_HIST_FILE, [])
    hist.append({
        **entry,
        "ts": int(time.time()),
    })
    hist = hist[-MAX_HISTORY:]
    _save(_HIST_FILE, hist)


def get_history(limit=20):
    hist = _load(_HIST_FILE, [])
    return hist[-limit:]


# ── Settings ────────────────────────────────────────────

def get_setting(chat_id, key, default=None):
    data = _load(_SET_FILE, {})
    return data.get(str(chat_id), {}).get(key, default)


def set_setting(chat_id, key, value):
    data = _load(_SET_FILE, {})
    cid = str(chat_id)
    if cid not in data:
        data[cid] = {}
    data[cid][key] = value
    _save(_SET_FILE, data)


# ── Stats ───────────────────────────────────────────────

def load_stats():
    return _load(_STATS_FILE, {"songs_played": 0, "groups": 0, "users": 0})


def bump_songs_played(n=1):
    s = load_stats()
    s["songs_played"] = int(s.get("songs_played", 0)) + n
    _save(_STATS_FILE, s)


def save_group_user_counts(groups: int, users: int):
    s = load_stats()
    s["groups"] = max(int(s.get("groups", 0)), groups)
    s["users"] = max(int(s.get("users", 0)), users)
    _save(_STATS_FILE, s)
