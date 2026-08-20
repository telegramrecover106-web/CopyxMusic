import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.API_ID = int(os.getenv("API_ID", "0"))
        self.API_HASH = os.getenv("API_HASH", "")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.LOGGER_ID = int(os.getenv("LOGGER_ID", "0"))
        self.OWNER_ID = int(os.getenv("OWNER_ID", "0"))
        self.MONGO_URL = os.getenv("MONGO_DB_URI", "")

        self.DURATION_LIMIT = int(os.getenv("DURATION_LIMIT", "300")) * 60
        self.QUEUE_LIMIT = int(os.getenv("QUEUE_LIMIT", "30"))
        self.PLAYLIST_LIMIT = int(os.getenv("PLAYLIST_LIMIT", "20"))

        # Preferred name requested by COPYxMUSIC. Legacy names remain supported.
        self.SESSION1 = os.getenv("SESSION_SECRET") or os.getenv("STRING_SESSION") or os.getenv("ASSISTANT_SESSION", "")
        self.SESSION2 = os.getenv("SESSION_SECRET2") or os.getenv("STRING_SESSION2", "")
        self.SESSION3 = os.getenv("SESSION_SECRET3") or os.getenv("STRING_SESSION3", "")

        self.SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/CopymusicOfficial")
        self.SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/CopymusicOfficial")
        self.UPDATES_URL = os.getenv("UPDATES_URL", "https://t.me/CopymusicOfficial")
        self.OWNER_URL = os.getenv("OWNER_URL", "https://t.me/CopymusicOfficial")
        self.BOT_USERNAME = os.getenv("BOT_USERNAME", "COPYxMUSIC_BOT")

        self.EXCLUDED_CHATS: List[int] = self._parse_int_list(os.getenv("EXCLUDED_CHATS", ""))
        self.AUTO_END = self._bool(os.getenv("AUTO_END", "False"))
        self.AUTO_LEAVE = self._bool(os.getenv("AUTO_LEAVE", "False"))
        self.THUMB_GEN = self._bool(os.getenv("THUMB_GEN", "True"))
        self.VIDEO_PLAY = self._bool(os.getenv("VIDEO_PLAY", "True"))
        self.VIDEO_MAX_HEIGHT = self._video_height(os.getenv("VIDEO_MAX_HEIGHT", "1080"))

        # YouTube/yt-dlp is the primary streaming path. External API is optional.
        self.ARTISTBOTS_API_URL = os.getenv("YOUTUBE_API_URL", "")
        self.ARTISTBOTS_KEY = os.getenv("YOUTUBE_API_KEY", "")
        self.ENABLE_API = self._bool(os.getenv("ENABLE_YOUTUBE_API", "False"))
        self.ENABLE_COOKIES_FALLBACK = self._bool(os.getenv("ENABLE_COOKIES_FALLBACK", "True"))
        self.API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
        self.API_STREAM_TIMEOUT = int(os.getenv("API_STREAM_TIMEOUT", "300"))
        self.COOKIES_URL = [u.strip() for u in os.getenv("COOKIE_URL", "").split() if u.strip()]
        self.YOUTUBE_COOKIES = os.getenv("YOUTUBE_COOKIES", "")

        self.DEFAULT_THUMB = os.getenv("DEFAULT_THUMB", "assets/start.png")
        self.PING_IMG = os.getenv("PING_IMG", "assets/start.png")
        self.START_IMG = os.getenv("START_IMG", "assets/start.png")
        self.RADIO_IMG = os.getenv("RADIO_IMG", "assets/start.png")
        self.WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "assets/start.png")
        self.EXCLUDED_USERNAMES = os.getenv("EXCLUDED_USERNAMES", "").split()

    @staticmethod
    def _bool(v):
        return str(v).lower() in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _parse_int_list(v):
        out=[]
        for x in str(v).split(','):
            x=x.strip()
            if x.lstrip('-').isdigit(): out.append(int(x))
        return out

    @staticmethod
    def _video_height(v):
        try: h=int(v)
        except: return 1080
        return 0 if h<=0 else max(480,min(h,2160))

    def check(self):
        required={
            "API_ID":self.API_ID, "API_HASH":self.API_HASH, "BOT_TOKEN":self.BOT_TOKEN,
            "MONGO_DB_URI":self.MONGO_URL, "OWNER_ID":self.OWNER_ID, "SESSION_SECRET":self.SESSION1,
        }
        missing=[k for k,v in required.items() if not v or (isinstance(v,int) and v==0)]
        if missing: raise SystemExit("Missing required env vars: " + ", ".join(missing))


config = Config()
