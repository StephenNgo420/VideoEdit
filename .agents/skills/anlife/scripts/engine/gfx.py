"""Engine đồ họa: font, text, card, icon, Layer animation, alpha blend. Màu lấy từ assets/config.json."""
import math, functools, json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(SKILL_DIR, "assets")
CONFIG = json.load(open(os.path.join(ASSETS, "config.json"), encoding="utf-8"))
BRAND = CONFIG["brand"]

W, H = 1080, 1920
FD = os.path.join(ASSETS, "fonts") + "/"
FONTS = {
    "disp_black": FD + "InterDisplay-Black.ttf",
    "disp_xbold": FD + "InterDisplay-ExtraBold.ttf",
    "disp_bold": FD + "InterDisplay-Bold.ttf",
    "semibold": FD + "Inter-SemiBold.ttf",
    "medium": FD + "Inter-Medium.ttf",
    "bold": FD + "Inter-Bold.ttf",
    "script": FD + "Pacifico.ttf",
}

def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

RED = hex2rgb(BRAND["primary"])
DRED = hex2rgb(BRAND["primary_dark"])
LRED = hex2rgb(BRAND["primary_light"])
CHAR = hex2rgb(BRAND["text"])
MGRAY = hex2rgb(BRAND["muted"])
LGRAY = (245, 245, 245)
WHITE = (255, 255, 255)
YELLOW = (255, 193, 7)

def asset(path):
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.join(ASSETS, path)

def load_logo(kind="dark", width=None):
    p = asset(BRAND.get("logo_dark" if kind == "dark" else "logo_light"))
    if not p or not os.path.exists(p): return None
    img = Image.open(p).convert("RGBA")
    width = width or BRAND.get("logo_width", 300)
    return img.resize((width, int(img.height * width / img.width)), Image.LANCZOS)

# Sự kiện SFX được ghi lại khi dựng layer (render.py xuất ra sfx_events.json)
EVENTS = []

@functools.lru_cache(maxsize=None)
def F(name, size):
    return ImageFont.truetype(FONTS[name], size)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_cubic(p):
    p = clamp(p); return 1 - (1 - p) ** 3

def ease_out_back(p, s=1.6):
    p = clamp(p) - 1; return p * p * ((s + 1) * p + s) + 1

def ease_in_out(p):
    p = clamp(p); return p * p * (3 - 2 * p)


# ---------- text ----------
def text_size(text, font):
    asc, desc = font.getmetrics()
    return int(math.ceil(font.getlength(text))), asc + desc

def rich_line(segs, pad=8):
    """segs: list of (text, font, color). Trả về RGBA PIL image của 1 dòng, baseline chung."""
    asc = max(f.getmetrics()[0] for _, f, _ in segs)
    desc = max(f.getmetrics()[1] for _, f, _ in segs)
    w = int(sum(f.getlength(t) for t, f, _ in segs)) + pad * 2
    img = Image.new("RGBA", (w, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    for t, f, c in segs:
        d.text((x, pad + asc), t, font=f, fill=c, anchor="ls")
        x += f.getlength(t)
    return img

def text_img(text, font, color, pad=8):
    return rich_line([(text, font, color)], pad)

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def paragraph(text, font, color, maxw, line_gap=1.25, align="left"):
    lines = wrap(text, font, maxw)
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * line_gap)
    w = int(max(font.getlength(l) for l in lines)) + 16
    img = Image.new("RGBA", (w, lh * len(lines) + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        x = 8 if align == "left" else 8 + (w - 16 - font.getlength(l)) / 2
        d.text((x, 8 + i * lh + asc), l, font=font, fill=color, anchor="ls")
    return img


# ---------- shapes ----------
def card(w, h, r=36, fill=(255, 255, 255, 250), shadow=60, blur=26, off=12, border=None, bw=3):
    """Card bo góc có bóng mềm. Trả về (img, m) với m là lề bóng; nội dung vẽ tại (m, m)."""
    m = blur * 2 + off
    img = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((m, m + off, m + w, m + h + off), r, fill=(40, 20, 20, shadow))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(blur)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((m, m, m + w, m + h), r, fill=fill, outline=border, width=bw if border else 0)
    return img, m

def dashed_rect(d, box, color, dash=22, gap=14, width=4):
    x0, y0, x1, y1 = box
    def seg(ax, ay, bx, by):
        L = math.hypot(bx - ax, by - ay); n = 0.0
        while n < L:
            e = min(n + dash, L)
            d.line((ax + (bx - ax) * n / L, ay + (by - ay) * n / L, ax + (bx - ax) * e / L, ay + (by - ay) * e / L), fill=color, width=width)
            n += dash + gap
    seg(x0, y0, x1, y0); seg(x1, y0, x1, y1); seg(x1, y1, x0, y1); seg(x0, y1, x0, y0)

def pill(text, font, fg, bg, padx=28, pady=12, r=None, icon=None):
    tw, th = text_size(text, font)
    iw = icon.width + 14 if icon is not None else 0
    w, h = tw + 2 * padx + iw, th + 2 * pady
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r if r is not None else h // 2, fill=bg)
    x = padx
    if icon is not None:
        img.alpha_composite(icon, (x, (h - icon.height) // 2)); x += iw
    d.text((x, pady + font.getmetrics()[0]), text, font=font, fill=fg, anchor="ls")
    return img


# ---------- icons (vẽ 4x rồi thu nhỏ để khử răng cưa) ----------
def _icon(size, drawfn):
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    drawfn(ImageDraw.Draw(img), S)
    return img.resize((size, size), Image.LANCZOS)

def icon_check(size, bg=RED):
    def f(d, S):
        d.ellipse((0, 0, S - 1, S - 1), fill=bg)
        d.line([(S * .27, S * .52), (S * .44, S * .68), (S * .74, S * .35)], fill=WHITE, width=int(S * .11), joint="curve")
    return _icon(size, f)

def icon_x(size, bg=CHAR):
    def f(d, S):
        d.ellipse((0, 0, S - 1, S - 1), fill=bg)
        w = int(S * .11)
        d.line([(S * .32, S * .32), (S * .68, S * .68)], fill=WHITE, width=w)
        d.line([(S * .68, S * .32), (S * .32, S * .68)], fill=WHITE, width=w)
    return _icon(size, f)

def icon_bolt(size, color=RED):
    def f(d, S):
        d.polygon([(S * .58, 0), (S * .12, S * .58), (S * .45, S * .58), (S * .36, S), (S * .88, S * .38), (S * .54, S * .38)], fill=color)
    return _icon(size, f)

def icon_bookmark(size, color=RED):
    def f(d, S):
        d.rounded_rectangle((S * .18, 0, S * .82, S * .9), int(S * .08), fill=color)
        d.polygon([(S * .18, S * .6), (S * .5, S * .72), (S * .82, S * .6), (S * .82, S), (S * .5, S * .78), (S * .18, S)], fill=color)
        d.polygon([(S * .18, S * .86), (S * .5, S * .66), (S * .82, S * .86), (S * .82, S * 1.0), (S * .18, S * 1.0)], fill=(0, 0, 0, 0))
    return _icon(size, f)

def icon_warn(size):
    def f(d, S):
        d.rounded_rectangle((S * .02, S * .02, S * .98, S * .98), int(S * .2), fill=YELLOW)
        d.rectangle((S * .44, S * .2, S * .56, S * .6), fill=CHAR)
        d.ellipse((S * .43, S * .68, S * .57, S * .82), fill=CHAR)
    return _icon(size, f)

def icon_chat(size, color=RED, glyph="?"):
    def f(d, S):
        d.rounded_rectangle((S * .04, S * .06, S * .96, S * .76), int(S * .2), fill=color)
        d.polygon([(S * .26, S * .7), (S * .5, S * .7), (S * .24, S * .95)], fill=color)
        fnt = ImageFont.truetype(FONTS["disp_black"], int(S * .5))
        d.text((S * .5, S * .42), glyph, font=fnt, fill=WHITE, anchor="mm")
    return _icon(size, f)

def icon_person(size, color=RED):
    def f(d, S):
        d.ellipse((0, 0, S - 1, S - 1), fill=LRED)
        d.ellipse((S * .34, S * .18, S * .66, S * .5), fill=color)
        d.pieslice((S * .2, S * .54, S * .8, S * 1.1), 180, 360, fill=color)
    return _icon(size, f)

def icon_gear(size, color=CHAR):
    def f(d, S):
        d.ellipse((0, 0, S - 1, S - 1), fill=LRED)
        c = S / 2
        for k in range(8):
            a = k * math.pi / 4
            d.line([(c + math.cos(a) * S * .18, c + math.sin(a) * S * .18), (c + math.cos(a) * S * .36, c + math.sin(a) * S * .36)], fill=color, width=int(S * .12))
        d.ellipse((c - S * .24, c - S * .24, c + S * .24, c + S * .24), fill=color)
        d.ellipse((c - S * .1, c - S * .1, c + S * .1, c + S * .1), fill=LRED)
    return _icon(size, f)


# ---------- numpy compositing ----------
def to_np(img):
    return np.asarray(img.convert("RGBA"), dtype=np.uint8)

def blend(dst, rgba, x, y, op=1.0):
    """Alpha-blend rgba (h,w,4 uint8) lên dst (H,W,3 uint8) tại (x,y) top-left, có clip."""
    if op <= 0.003: return
    h, w = rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0: return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4].astype(np.float32) * (op / 255.0)
    reg = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (reg + (src[..., :3].astype(np.float32) - reg) * a).astype(np.uint8)


class Layer:
    """Một phần tử đồ họa có animation vào/ra.
    x,y = toạ độ top-left đích. anim: pop | up | down | left | right | fade | stamp."""
    def __init__(self, img, x, y, t_in, t_out=None, anim="up", dur=0.35, out_dur=0.2, sfx=None):
        self.a = to_np(img) if isinstance(img, Image.Image) else img
        if sfx is None and anim in ("pop", "left", "right", "stamp", "down") and t_in >= 0:
            sfx = "pop"
        if sfx and sfx != "none":
            EVENTS.append((round(t_in, 3), sfx))
        self.x, self.y = x, y
        self.t_in, self.t_out, self.anim, self.dur, self.out_dur = t_in, t_out, anim, dur, out_dur

    @staticmethod
    def centered(img, cx, cy, *a, **k):
        return Layer(img, cx - img.width / 2, cy - img.height / 2, *a, **k)

    def draw(self, dst, t):
        if t < self.t_in: return
        if self.t_out is not None and t >= self.t_out + self.out_dur: return
        p = (t - self.t_in) / self.dur
        op = clamp(p * 2.2)
        dx = dy = 0.0; sc = 1.0
        if p < 1:
            if self.anim == "up": dy = (1 - ease_out_cubic(p)) * 70
            elif self.anim == "down": dy = -(1 - ease_out_cubic(p)) * 70
            elif self.anim == "left": dx = -(1 - ease_out_cubic(p)) * 140
            elif self.anim == "right": dx = (1 - ease_out_cubic(p)) * 140
            elif self.anim == "pop": sc = 0.55 + 0.45 * ease_out_back(p)
            elif self.anim == "stamp": sc = 1.6 - 0.6 * ease_out_cubic(p)
            elif self.anim == "fade": op = clamp(p)
        if self.t_out is not None and t > self.t_out:
            op *= 1 - clamp((t - self.t_out) / self.out_dur)
        a = self.a
        if abs(sc - 1) > 0.01:
            h, w = a.shape[:2]
            nw, nh = max(2, int(w * sc)), max(2, int(h * sc))
            a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_LINEAR)
            dx += (w - nw) / 2; dy += (h - nh) / 2
        blend(dst, a, self.x + dx, self.y + dy, op)

def icon_mountain(size, color=RED):
    def f(d, S):
        d.polygon([(0, S * .92), (S * .38, S * .22), (S * .7, S * .92)], fill=color)
        d.polygon([(S * .42, S * .92), (S * .7, S * .45), (S, S * .92)], fill=DRED)
        d.polygon([(S * .38, S * .22), (S * .3, S * .37), (S * .46, S * .37)], fill=WHITE)
    return _icon(size, f)
