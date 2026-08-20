import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSET_DIR = os.path.dirname(os.path.dirname(__file__)) + "/assets"
BASE_IMAGE = os.path.join(ASSET_DIR, "welcome_base.jpg")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _fit(text, max_len):
    text = str(text or "").replace("\n", " ").strip()
    return text if len(text) <= max_len else text[:max_len-1] + "…"


def make_welcome_image(member, group_name, out_path, avatar_path=None):
    if os.path.exists(BASE_IMAGE):
        img = Image.open(BASE_IMAGE).convert("RGB").resize((1200, 700))
        # Give the reference design a sky-blue treatment.
        overlay = Image.new("RGBA", img.size, (48, 181, 214, 135))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
    else:
        img = Image.new("RGBA", (1200, 700), (55, 190, 225, 255))

    draw = ImageDraw.Draw(img, "RGBA")
    # Dark translucent information card for readability.
    draw.rounded_rectangle((55, 330, 1145, 650), radius=28, fill=(4, 20, 38, 215), outline=(90, 225, 255, 220), width=3)
    draw.text((75, 45), "WELCOME", font=_font(BOLD, 86), fill=(245, 250, 255, 255), stroke_width=2, stroke_fill=(0, 140, 220, 255))
    draw.text((75, 140), "COPYx MUSIC", font=_font(BOLD, 44), fill=(115, 240, 255, 255))
    draw.text((75, 205), "WELCOME TO", font=_font(BOLD, 30), fill=(255, 255, 255, 255))
    draw.text((75, 245), _fit(group_name, 38), font=_font(BOLD, 38), fill=(255, 255, 255, 255))

    # Avatar circle on the right.
    if avatar_path and os.path.exists(avatar_path):
        try:
            avatar = Image.open(avatar_path).convert("RGB").resize((220, 220))
            mask = Image.new("L", (220, 220), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 219, 219), fill=255)
            img.paste(avatar, (900, 70), mask)
            draw.ellipse((895, 65, 1125, 295), outline=(80, 240, 255, 255), width=8)
        except Exception:
            pass

    name = getattr(member, "first_name", "Unknown") or "Unknown"
    username = getattr(member, "username", None)
    uid = getattr(member, "id", "N/A")
    username_text = f"@{username}" if username else "@N/A"
    draw.text((90, 365), "NAME", font=_font(BOLD, 34), fill=(255,255,255,255))
    draw.text((315, 365), _fit(name, 28), font=_font(FONT, 34), fill=(135,235,255,255))
    draw.text((90, 435), "ID", font=_font(BOLD, 34), fill=(255,255,255,255))
    draw.text((315, 435), str(uid), font=_font(FONT, 34), fill=(255,255,255,255))
    draw.text((90, 505), "USERNAME", font=_font(BOLD, 30), fill=(255,255,255,255))
    draw.text((315, 505), _fit(username_text, 28), font=_font(FONT, 30), fill=(135,235,255,255))
    draw.text((90, 585), "MADE BY", font=_font(BOLD, 28), fill=(255,255,255,255))
    draw.text((315, 585), "COPYx MUSIC", font=_font(BOLD, 30), fill=(255,255,255,255))
    img.convert("RGB").save(out_path, quality=92)
    return out_path
