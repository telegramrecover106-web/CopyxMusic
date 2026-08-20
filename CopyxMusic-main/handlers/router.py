from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

from handlers.admin import ban_user, kick_user, mute_user, unban_user, unmute_user
from handlers.callbacks import callback_handler
from handlers.music import (
    clear_command, pause_command, play_command, resume_command,
    skip_command, stop_command, queue_command, shuffle_command, loop_command
)
from handlers.system import ping_handler, start_handler
from handlers.new_chat import new_chat_member


async def private_play_warning(client, message):
    await message.reply_text("⚠️ <b>This command can only be used in a group.</b>", parse_mode="html")


def register_handlers(client):
    client.add_handler(MessageHandler(ping_handler, filters.command(["ping", "alive"])))
    client.add_handler(MessageHandler(start_handler, filters.command("start")))
    client.add_handler(MessageHandler(play_command, filters.command(["play", "p"]) & filters.group))
    client.add_handler(MessageHandler(
        private_play_warning,
        filters.command(["play", "p"]) & filters.private,
    ))
    client.add_handler(MessageHandler(stop_command, filters.command(["stop", "end"]) & filters.group))
    client.add_handler(MessageHandler(skip_command, filters.command("skip") & filters.group))
    client.add_handler(MessageHandler(clear_command, filters.command(["clear", "clean"]) & filters.group))
    client.add_handler(MessageHandler(pause_command, filters.command("pause") & filters.group))
    client.add_handler(MessageHandler(resume_command, filters.command("resume") & filters.group))
    client.add_handler(MessageHandler(queue_command, filters.command(["queue", "q"]) & filters.group))
    client.add_handler(MessageHandler(shuffle_command, filters.command("shuffle") & filters.group))
    client.add_handler(MessageHandler(loop_command, filters.command("loop") & filters.group))

    # Moderation commands remain admin protected.
    client.add_handler(MessageHandler(kick_user, filters.command("kick") & filters.group))
    client.add_handler(MessageHandler(ban_user, filters.command("ban") & filters.group))
    client.add_handler(MessageHandler(unban_user, filters.command("unban") & filters.group))
    client.add_handler(MessageHandler(mute_user, filters.command("mute") & filters.group))
    client.add_handler(MessageHandler(unmute_user, filters.command("unmute") & filters.group))

    client.add_handler(MessageHandler(new_chat_member, filters.new_chat_members & filters.group))
    client.add_handler(CallbackQueryHandler(callback_handler))
