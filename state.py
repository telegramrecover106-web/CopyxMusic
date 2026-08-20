import asyncio
import time
from collections import defaultdict

chat_queues = {}
progress_tasks = {}
active_clients = {}
paused_chats = set()
user_command_history = {}
bot_start_time = time.time()

ASSISTANT_ID = None
ASSISTANT_USERNAME = None

# Per-chat locks to prevent race conditions
chat_locks = defaultdict(asyncio.Lock)

# Playback flags
autoplay_chats = set()
loop_mode = {}  # chat_id -> 0 off, 1 current song
vc_active = set()  # chats where VC is known active
player_messages = {}  # chat_id -> message for cleanup
now_playing_meta = {}  # chat_id -> dict with start_time, duration, etc.

# Stats
stats = {
    "songs_played": 0,
    "groups_served": set(),
    "users_served": set(),
}

# In-memory caches (bounded)
search_cache = {}  # query -> (timestamp, result)
related_cache = {}
