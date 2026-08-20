import time

chat_queues = {}
progress_tasks = {}
active_clients = {}
paused_chats = set()
loop_chats = set()
known_groups = set()
voice_states = {}
user_command_history = {}
bot_start_time = time.time()
ASSISTANT_ID = None
ASSISTANT_USERNAME = None
