import os

# Required secrets — set via environment / Replit Secrets. No hardcoded tokens.
API_ID = int(os.getenv("API_ID", "0") or "0")
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("ASSISTANT_SESSION") or os.getenv("STRING_SESSION") or ""
OWNER_ID = int(os.getenv("OWNER_ID", "0") or "0")
MAIN_OWNER = OWNER_ID
DEPLOYED_OWNER_ID = OWNER_ID

# Optional search / download helpers
SEARCH_API_URL = os.getenv("SEARCH_API_URL", "https://search-api.kustbotsweb.workers.dev")
DOWNLOAD_API_BASE = (os.getenv("DOWNLOAD_API_BASE", "") or "").rstrip("/")
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.txt")
YOUTUBE_COOKIES = os.getenv("YOUTUBE_COOKIES", "")

# Branding & links
BOT_NAME = "COPYxMUSIC"
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/CopymusicOfficial")
UPDATES_URL = os.getenv("UPDATES_URL", "https://t.me/CopymusicOfficial")
OWNER_URL = os.getenv("OWNER_URL", "")  # falls back to tg://user?id=OWNER_ID
ADD_TO_GROUP_URL = os.getenv("ADD_TO_GROUP_URL", "")  # auto-built from bot username if empty

# Behaviour
RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW = 8
MAX_TITLE_LEN = 48
PORT = int(os.getenv("PORT", "8080") or "8080")
EVERYONE_CAN_CONTROL = os.getenv("EVERYONE_CAN_CONTROL", "1") == "1"
MAX_QUEUE_SIZE = 50
MAX_HISTORY = 200
SEARCH_CACHE_TTL = 300
DOWNLOAD_DIR = "downloads"
DATA_DIR = "data"
