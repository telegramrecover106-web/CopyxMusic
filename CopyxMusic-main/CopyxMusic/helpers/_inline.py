from pyrogram import types
from pyrogram.enums import ButtonStyle
from CopyxMusic import app, config, lang


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text):
        return self.ikm([[self.ikb(text=f"✖ {text}", callback_data="cancel_dl", style=ButtonStyle.DANGER)]])

    def controls(self, chat_id: int, status: str = None, timer: str = None, remove: bool = False):
        label = status or timer or "🎵 COPYx MUSIC · LIVE"
        rows = [
            [self.ikb(label, callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY)],
            [self.ikb("⏪ 10s", callback_data=f"controls seek_back_10 {chat_id}"),
             self.ikb("⏸ / ▶️", callback_data=f"controls pause {chat_id}")],
            [self.ikb("⏮ Replay", callback_data=f"controls replay {chat_id}"),
             self.ikb("⏭ Skip", callback_data=f"controls skip {chat_id}")],
            [self.ikb("⏩ 10s", callback_data=f"controls seek_forward_10 {chat_id}"),
             self.ikb("🔂 Loop", callback_data=f"controls loop {chat_id}")],
            [self.ikb("🔀 Shuffle", callback_data=f"controls shuffle {chat_id}"),
             self.ikb("⏹ Stop", callback_data=f"controls stop {chat_id}", style=ButtonStyle.DANGER),
             self.ikb("✖ Close", callback_data=f"controls close {chat_id}", style=ButtonStyle.DANGER)],
        ]
        return self.ikm(rows)

    def help_markup(self, _lang, back=False):
        if back:
            return self.ikm([[self.ikb("🔙 Back", callback_data="help")]])
        return self.ikm([
            [self.ikb("🎵 Music", callback_data="help_play"), self.ikb("📋 Queue", callback_data="help_queue")],
            [self.ikb("🛠 Controls", callback_data="help_loop"), self.ikb("ℹ️ Commands", callback_data="help_stats")],
            [self.ikb("🌐 Language", callback_data="help_langs")],
        ])

    def langs_markup(self):
        langs=[("🇬🇧 English","en"),("🇮🇳 Hindi","hi"),("🇮🇳 Telugu","te"),("🇮🇩 Indonesian","id"),("🇧🇩 Bengali","bn"),("🇵🇰 Urdu","ur")]
        rows=[]
        for i in range(0,len(langs),2):
            rows.append([self.ikb(a,callback_data=f"setlang_{b}"), self.ikb(langs[i+1][0],callback_data=f"setlang_{langs[i+1][1]}")])
        rows.append([self.ikb("🔙 Back",callback_data="help")])
        return self.ikm(rows)

    def ping_markup(self,text):
        return self.ikm([
            [self.ikb(text,callback_data="ping_refresh")],
            [self.ikb("💬 Support",url=config.SUPPORT_CHAT),self.ikb("📢 Updates",url=config.UPDATES_URL)],
            [self.ikb("➕ Add COPYxMUSIC",url=f"https://t.me/{config.BOT_USERNAME}?startgroup=true",style=ButtonStyle.SUCCESS)],
        ])

    def play_queued(self, chat_id:int, item_id:str, _text:str):
        return self.ikm([[self.ikb("▶️ Play",callback_data=f"controls force {chat_id} {item_id}",style=ButtonStyle.SUCCESS),
                          self.ikb("✖ Close",callback_data=f"controls close {chat_id}",style=ButtonStyle.DANGER)]])

    def queue_markup(self, chat_id:int, _text:str, playing:bool):
        action="pause" if playing else "resume"
        label="⏸ Pause" if playing else "▶️ Resume"
        return self.ikm([[self.ikb(label,callback_data=f"controls {action} {chat_id}",style=ButtonStyle.SUCCESS),
                          self.ikb("⏭ Skip",callback_data=f"controls skip {chat_id}"),
                          self.ikb("⏹ Stop",callback_data=f"controls stop {chat_id}",style=ButtonStyle.DANGER)]])

    def settings_markup(self, lang, admin_only, force_admin, language, chat_id):
        return self.ikm([[self.ikb("⚙️ Settings",callback_data=f"controls status {chat_id}")],[self.ikb("🏠 Start",callback_data="start",style=ButtonStyle.SUCCESS)]])

    def start_key(self, lang, private=False):
        rows=[
            [self.ikb("💬 CHAT WITH ME",url=f"https://t.me/{config.BOT_USERNAME}",style=ButtonStyle.SUCCESS)],
            [self.ikb("⌜ HELP & CMDS ⌟",callback_data="help"), self.ikb("⌜ SUPPORT ⌟",url=config.SUPPORT_CHAT)],
            [self.ikb("⌜ UPDATES ⌟",url=config.UPDATES_URL), self.ikb("⌜ OWNER ⌟",url=config.OWNER_URL,style=ButtonStyle.DANGER)],
            [self.ikb("➕ ADD ME TO GROUP ➕",url=f"https://t.me/{config.BOT_USERNAME}?startgroup=true",style=ButtonStyle.SUCCESS)],
        ]
        return self.ikm(rows)

    def yt_key(self, link):
        return self.ikm([[self.ikb("▶️ Open on YouTube",url=link),self.ikb("✖ Close",callback_data="controls close 0",style=ButtonStyle.DANGER)]])

buttons = Inline()
