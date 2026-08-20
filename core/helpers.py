import isodate
from config import MAX_TITLE_LEN


def to_bold_unicode(text: str) -> str:
    maps = {
        "A": "𝗔", "B": "𝗕", "C": "𝗖", "D": "𝗗", "E": "𝗘", "F": "𝗙", "G": "𝗚", "H": "𝗛",
        "I": "𝗜", "J": "𝗝", "K": "𝗞", "L": "𝗟", "M": "𝗠", "N": "𝗡", "O": "𝗢", "P": "𝗣",
        "Q": "𝗤", "R": "𝗥", "S": "𝗦", "T": "𝗧", "U": "𝗨", "V": "𝗩", "W": "𝗪", "X": "𝗫",
        "Y": "𝗬", "Z": "𝗭",
        "a": "𝗮", "b": "𝗯", "c": "𝗰", "d": "𝗱", "e": "𝗲", "f": "𝗳", "g": "𝗴", "h": "𝗵",
        "i": "𝗶", "j": "𝗷", "k": "𝗸", "l": "𝗹", "m": "𝗺", "n": "𝗻", "o": "𝗼", "p": "𝗽",
        "q": "𝗾", "r": "𝗿", "s": "𝘀", "t": "𝘁", "u": "𝘂", "v": "𝘃", "w": "𝘄", "x": "𝘅",
        "y": "𝘆", "z": "𝘇",
        "0": "𝟬", "1": "𝟭", "2": "𝟮", "3": "𝟯", "4": "𝟰",
        "5": "𝟱", "6": "𝟲", "7": "𝟳", "8": "𝟴", "9": "𝟵",
    }
    return "".join(maps.get(c, c) for c in text)


def one_line_title(full_title, max_len=None):
    max_len = max_len or MAX_TITLE_LEN
    if not full_title:
        return "Unknown"
    full_title = str(full_title).strip()
    if len(full_title) <= max_len:
        return full_title
    return full_title[: max_len - 1] + "…"


def parse_duration_str(duration_str):
    try:
        return int(isodate.parse_duration(str(duration_str)).total_seconds())
    except Exception:
        pass
    s = str(duration_str or "0")
    if ":" in s:
        try:
            parts = [int(x) for x in s.split(":")]
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
        except Exception:
            pass
    try:
        return int(float(s))
    except Exception:
        return 0


def format_time(seconds):
    secs = max(0, int(seconds))
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def get_progress_bar(elapsed, total, bar_length=12):
    if total <= 0:
        return "LIVE 🔴"
    fraction = min(max(elapsed / total, 0), 1)
    marker_index = min(int(fraction * bar_length), bar_length - 1)
    left = "━" * marker_index
    right = "─" * (bar_length - marker_index - 1)
    return f"{format_time(elapsed)} {left}●{right} {format_time(total)}"


def get_readable_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s and not d:
        parts.append(f"{s}s")
    return " ".join(parts) or "0s"


def mention_html(user_id, name):
    name = (name or "User").replace("<", "").replace(">", "")
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def yt_link_html(title, url):
    title = one_line_title(title or "Song", 60)
    if url and "youtube" in str(url).lower() or "youtu.be" in str(url).lower():
        return f'<a href="{url}">{title}</a>'
    return title
