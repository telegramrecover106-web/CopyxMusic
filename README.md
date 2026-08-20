# COPYxMUSIC

High-quality Telegram voice-chat music bot powered by Pyrogram, PyTgCalls and yt-dlp.

## Features

- `/play` song name or YouTube URL in groups
- Automatic assistant invite when missing
- Voice chat start/end detection
- Smart queue, skip, pause, resume, stop
- AutoPlay, loop, shuffle
- Favourites, lyrics, suggestions
- Now playing progress
- Group welcome message
- Clone multi-bot support
- Replit / Docker / Railway / Render ready

## Required Replit Secrets / Environment

| Key | Description |
|-----|-------------|
| `API_ID` | from https://my.telegram.org |
| `API_HASH` | from https://my.telegram.org |
| `BOT_TOKEN` | from @BotFather |
| `ASSISTANT_SESSION` | Pyrogram string session of a user account |
| `OWNER_ID` | Your Telegram user ID |

Optional: `SEARCH_API_URL`, `DOWNLOAD_API_BASE`, `YOUTUBE_COOKIES`, `SUPPORT_URL`, `UPDATES_URL`

## Telegram setup

1. Create a bot with @BotFather.
2. Create a user account session string for the assistant (Pyrogram).
3. Add the **bot** to your group as **admin** with:
   - Invite users via link
   - Delete messages (optional)
   - Manage video chats (recommended)
4. Start a **voice chat** in the group, then `/play song`.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Docker:

```bash
docker build -t copyxmusic .
docker run --env-file .env copyxmusic
```

## Commands

| Command | Description |
|---------|-------------|
| `/play <song>` | Play song / URL |
| `/skip` | Skip |
| `/stop` | Stop & clear |
| `/pause` `/resume` | Pause / resume |
| `/queue` | Show queue |
| `/nowplaying` | Current track |
| `/seek <sec>` | Seek |
| `/loop` | Loop current |
| `/shuffle` | Shuffle queue |
| `/autoplay` | Toggle autoplay |
| `/lyrics` | Lyrics |
| `/fav` `/unfav` | Favourites |
| `/ping` | Latency |
| `/stats` | Stats |
| `/restart` | Owner restart |

## Branding

Official: https://t.me/CopymusicOfficial

Made with ❤️ as COPYxMUSIC
