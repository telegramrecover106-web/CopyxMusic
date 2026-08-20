import random

import state
from config import MAX_QUEUE_SIZE


def get_queue(chat_id):
    return state.chat_queues.get(chat_id, [])


def ensure_queue(chat_id):
    if chat_id not in state.chat_queues:
        state.chat_queues[chat_id] = []
    return state.chat_queues[chat_id]


def add_to_queue(chat_id, song_info) -> int:
    q = ensure_queue(chat_id)
    if len(q) >= MAX_QUEUE_SIZE:
        raise ValueError(f"Queue limit ({MAX_QUEUE_SIZE}) reached.")
    q.append(song_info)
    return len(q) - 1


def current_song(chat_id):
    q = get_queue(chat_id)
    return q[0] if q else None


def pop_current(chat_id):
    q = get_queue(chat_id)
    if not q:
        return None
    return q.pop(0)


def clear_queue(chat_id, keep_current=False):
    q = get_queue(chat_id)
    if not q:
        state.chat_queues.pop(chat_id, None)
        return
    if keep_current and q:
        state.chat_queues[chat_id] = [q[0]]
    else:
        state.chat_queues.pop(chat_id, None)


def shuffle_queue(chat_id):
    q = get_queue(chat_id)
    if len(q) <= 2:
        return False
    current = q[0]
    rest = q[1:]
    random.shuffle(rest)
    state.chat_queues[chat_id] = [current] + rest
    return True


def queue_count(chat_id):
    return len(get_queue(chat_id))
