import asyncio
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from CopyxMusic import config

W, H = 1536, 1024


def _font(size, bold=False):
    names = [
        "CopyxMusic/helpers/DejaVuSans-Bold.ttf" if bold else "CopyxMusic/helpers/Inter-Light.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for n in names:
        if os.path.exists(n):
            return ImageFont.truetype(n, size)
    return ImageFont.load_default()


def _fit_text(draw, text, max_w, size=44, bold=True):
    f=_font(size,bold)
    while draw.textbbox((0,0),text,font=f)[2] > max_w and size > 20:
        size-=2; f=_font(size,bold)
    return f


def _circle_avatar(img, box):
    avatar=ImageOps.fit(img.convert("RGB"), (box[2]-box[0],box[3]-box[1]), Image.Resampling.LANCZOS)
    mask=Image.new("L", avatar.size, 0)
    ImageDraw.Draw(mask).ellipse((0,0,*avatar.size), fill=255)
    out=Image.new("RGBA", avatar.size, (0,0,0,0)); out.paste(avatar,(0,0),mask)
    return out

async def make_group_welcome(chat, added_by):
    base_path=Path(config.WELCOME_IMAGE)
    if not base_path.exists(): base_path=Path(config.START_IMG)
    bg=Image.open(base_path).convert("RGB").resize((W,H))
    # Sky-blue glass overlay to make the welcome card distinct from the start art.
    overlay=Image.new("RGBA",(W,H),(40,190,235,65)); bg=Image.alpha_composite(bg.convert("RGBA"),overlay)
    dark=Image.new("RGBA",(W,H),(0,0,0,75)); bg=Image.alpha_composite(bg,dark)
    draw=ImageDraw.Draw(bg)

    # Glass card
    card=(70,250,1466,930)
    draw.rounded_rectangle(card, radius=48, fill=(4,14,32,210), outline=(80,220,255,220), width=4)
    title=f"WELCOME TO {chat.title or 'THIS GROUP'}"
    ftitle=_fit_text(draw,title,1250,54,True)
    draw.text((120,285),title,font=ftitle,fill=(230,250,255))
    draw.text((120,360),"╾⃝⃤ COPY ✘ MUSIC  •  MUSIC STREAMING",font=_font(32,True),fill=(95,215,255))
    draw.text((120,425),"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",font=_font(28,True),fill=(120,220,255))

    # Avatar
    avatar=None
    if added_by:
        try:
            photos = [photo async for photo in added_by._client.get_chat_photos(added_by.id, limit=1)]
            if photos:
                avatar_path = await added_by._client.download_media(photos[0].file_id, file_name="cache/welcome_avatar")
                if avatar_path and os.path.exists(avatar_path): avatar=Image.open(avatar_path)
        except Exception: pass
    if avatar:
        av=_circle_avatar(avatar,(1120,400,1360,640)); bg.alpha_composite(av,(1120,400))
    else:
        draw.ellipse((1120,400,1360,640),fill=(30,160,220,200),outline=(120,240,255),width=6)
        initial=(added_by.first_name[:1] if added_by and added_by.first_name else "C")
        draw.text((1200,485),initial,font=_font(100,True),fill=(255,255,255))

    name=(added_by.first_name or "Unknown") if added_by else "Unknown"
    uname=f"@{added_by.username}" if added_by and added_by.username else "—"
    uid=str(added_by.id) if added_by else "—"
    lines=[("๏ NAME ➠",name),("๏ ID ➠",uid),("๏ USERNAME ➠",uname)]
    y=500
    for label,val in lines:
        draw.text((145,y),label,font=_font(34,True),fill=(255,255,255)); draw.text((430,y),val,font=_font(34,False),fill=(190,235,255)); y+=72
    draw.text((145,730),"๏ MADE BY ➠",font=_font(34,True),fill=(255,255,255))
    draw.text((430,730),"COPYxMUSIC",font=_font(34,True),fill=(75,220,255))
    draw.text((145,815),"Fast voice-chat playback  •  Smart queue  •  HD thumbnails",font=_font(28,False),fill=(205,230,245))
    draw.text((145,865),"🎧 Welcome — enjoy the music!",font=_font(30,True),fill=(255,255,255))

    os.makedirs("cache",exist_ok=True)
    safe_id=str(chat.id).replace('-','_')
    out=f"cache/welcome_{safe_id}.jpg"
    bg.convert("RGB").save(out,quality=92,optimize=True)
    return out
