import time

chat_queues = {}
progress_tasks = {}
active_clients = {}
paused_chats = set()
auto_mode_chats = set()
active_voice_chats = set()
favourite_tracks = {}
user_command_history = {}
bot_start_time = time.time()
ASSISTANT_ID = None
ASSISTANT_USERNAME = None
