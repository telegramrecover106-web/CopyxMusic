from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler, ChatMemberUpdatedHandler

from handlers.admin import ban_user, kick_user, mute_user, unban_user, unmute_user
from handlers.callbacks import callback_handler
from handlers.music import (
    play_command, vplay_command, stop_command, skip_command, clear_command,
    pause_command, resume_command, queue_command, nowplaying_command,
    seek_command, loop_command, shuffle_command, autoplay_command,
    fav_command, unfav_command, lyrics_command,
)
from handlers.system import ping_handler, start_handler, stats_handler, restart_handler
from handlers.welcome import on_bot_added
from handlers.voicechat import on_voice_chat_started, on_voice_chat_ended


def register_handlers(client):
    # System
    client.add_handler(MessageHandler(ping_handler, filters.command(["ping", "alive"])))
    client.add_handler(MessageHandler(start_handler, filters.command("start")))
    client.add_handler(MessageHandler(stats_handler, filters.command("stats")))
    client.add_handler(MessageHandler(restart_handler, filters.command("restart") & filters.private))

    # Music (group)
    client.add_handler(MessageHandler(play_command, filters.command(["play", "p"])))
    client.add_handler(MessageHandler(vplay_command, filters.command(["vplay", "vp"])))
    client.add_handler(MessageHandler(stop_command, filters.command(["stop", "end"]) & filters.group))
    client.add_handler(MessageHandler(skip_command, filters.command("skip") & filters.group))
    client.add_handler(MessageHandler(clear_command, filters.command(["clear", "clean"]) & filters.group))
    client.add_handler(MessageHandler(pause_command, filters.command("pause") & filters.group))
    client.add_handler(MessageHandler(resume_command, filters.command("resume") & filters.group))
    client.add_handler(MessageHandler(queue_command, filters.command(["queue", "q"]) & filters.group))
    client.add_handler(MessageHandler(nowplaying_command, filters.command(["nowplaying", "np"]) & filters.group))
    client.add_handler(MessageHandler(seek_command, filters.command("seek") & filters.group))
    client.add_handler(MessageHandler(loop_command, filters.command("loop") & filters.group))
    client.add_handler(MessageHandler(shuffle_command, filters.command("shuffle") & filters.group))
    client.add_handler(MessageHandler(autoplay_command, filters.command("autoplay") & filters.group))
    client.add_handler(MessageHandler(fav_command, filters.command(["fav", "favourite"])))
    client.add_handler(MessageHandler(unfav_command, filters.command(["unfav", "unfavourite"])))
    client.add_handler(MessageHandler(lyrics_command, filters.command("lyrics")))

    # Admin
    client.add_handler(MessageHandler(kick_user, filters.command("kick") & filters.group))
    client.add_handler(MessageHandler(ban_user, filters.command("ban") & filters.group))
    client.add_handler(MessageHandler(unban_user, filters.command("unban") & filters.group))
    client.add_handler(MessageHandler(mute_user, filters.command("mute") & filters.group))
    client.add_handler(MessageHandler(unmute_user, filters.command("unmute") & filters.group))

    # Callbacks
    client.add_handler(CallbackQueryHandler(callback_handler))

    # Welcome
    client.add_handler(ChatMemberUpdatedHandler(on_bot_added))

    # Voice chat service messages
    client.add_handler(MessageHandler(
        on_voice_chat_started,
        filters.service & filters.video_chat_started,
    ))
    client.add_handler(MessageHandler(
        on_voice_chat_ended,
        filters.service & filters.video_chat_ended,
    ))
