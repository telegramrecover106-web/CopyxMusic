from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler


def _video_chat_started_filter(_, __, message):
    return getattr(message, "video_chat_started", None) is not None


def _video_chat_ended_filter(_, __, message):
    return getattr(message, "video_chat_ended", None) is not None


VIDEO_CHAT_STARTED = filters.create(_video_chat_started_filter, name="video_chat_started")
VIDEO_CHAT_ENDED = filters.create(_video_chat_ended_filter, name="video_chat_ended")
VIDEO_CHAT_EVENT = VIDEO_CHAT_STARTED | VIDEO_CHAT_ENDED

from handlers.admin import ban_user, kick_user, mute_user, unban_user, unmute_user
from handlers.callbacks import callback_handler
from handlers.music import clear_command, pause_command, play_command, resume_command, skip_command, stop_command, queue_command
from handlers.system import help_command, ping_handler, start_handler, video_chat_event_handler, welcome_new_members


def register_handlers(client):
    client.add_handler(MessageHandler(ping_handler, filters.command(["ping", "alive"])))
    client.add_handler(MessageHandler(start_handler, filters.command("start")))
    # IMPORTANT: keep these lifecycle handlers separate from the generic
    # `filters.service` handler. Pyrogram/Kurigram dispatches the first
    # matching handler in a handler group, so a broad service filter would
    # otherwise swallow the video-chat start/end update.
    client.add_handler(MessageHandler(video_chat_event_handler, VIDEO_CHAT_EVENT))
    client.add_handler(MessageHandler(welcome_new_members, filters.service))
    client.add_handler(MessageHandler(queue_command, filters.command(["queue", "q"]) & filters.group))
    client.add_handler(MessageHandler(help_command, filters.command(["help", "commands"])))
    # Playback is open to normal users; Telegram's own group permissions still apply to VC access.
    client.add_handler(MessageHandler(play_command, filters.command(["play", "p"])))
    client.add_handler(MessageHandler(stop_command, filters.command(["stop", "end"]) & filters.group))
    client.add_handler(MessageHandler(skip_command, filters.command("skip") & filters.group))
    client.add_handler(MessageHandler(clear_command, filters.command(["clear", "clean"]) & filters.group))
    client.add_handler(MessageHandler(pause_command, filters.command("pause") & filters.group))
    client.add_handler(MessageHandler(resume_command, filters.command("resume") & filters.group))
    client.add_handler(MessageHandler(kick_user, filters.command("kick") & filters.group))
    client.add_handler(MessageHandler(ban_user, filters.command("ban") & filters.group))
    client.add_handler(MessageHandler(unban_user, filters.command("unban") & filters.group))
    client.add_handler(MessageHandler(mute_user, filters.command("mute") & filters.group))
    client.add_handler(MessageHandler(unmute_user, filters.command("unmute") & filters.group))
    client.add_handler(CallbackQueryHandler(callback_handler))
