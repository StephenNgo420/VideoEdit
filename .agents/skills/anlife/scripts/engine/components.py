"""Component dựng từ spec JSON (xem references/edl-schema.md).
Scene (full-screen): cards_grid, rows_x, chapter, checklist, versus, summary, statement  -> (bg_np, [Layer])
Overlay (trên cảnh nói): question_card, title_box, meter, x_list, check_list, callout, chips, warning, cta, lower_third, badge -> [Layer]
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import *

ICONS = {
    "check": lambda s: icon_check(s), "check_dark": lambda s: icon_check(s, CHAR), "x": lambda s: icon_x(s),
    "bolt": lambda s: icon_bolt(s), "bookmark": lambda s: icon_bookmark(s), "warn": lambda s: icon_warn(s),
    "chat": lambda s: icon_chat(s), "person": lambda s: icon_person(s), "gear": lambda s: icon_gear(s),
    "mountain": lambda s: icon_mountain(s),
}
def get_icon(name, size):
    return ICONS.get(name or "check", ICONS["check"])(size)

# ---------------- nền cảnh ----------------
_BG = {}
def scene_bg(style="light"):
    if style in _BG: return _BG[style]
    if style == "red":
        img = Image.new("RGBA", (W, H), RED + (255,))
        d = ImageDraw.Draw(img, "RGBA")
        for yy in range(0, H, 56):
            for xx in range(0, W, 56):
                d.ellipse((xx + 26, yy + 26, xx + 30, yy + 30), fill=(255, 255, 255, 28))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((-300, -200, 700, 800), fill=(255, 255, 255, 40))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(160)))
        logo = load_logo("light")
    else:
        g = np.linspace(0, 1, H)[:, None, None]
        arr = (np.array(WHITE, float) * (1 - g) + np.array(LRED, float) * g).repeat(W, axis=1).astype(np.uint8)
        img = Image.fromarray(arr).convert("RGBA")
        blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blobs)
        bd.ellipse((650, 120, 1350, 820), fill=RED + (34,))
        bd.ellipse((-350, 1250, 400, 2000), fill=RED + (26,))
        img = Image.alpha_composite(img, blobs.filter(ImageFilter.GaussianBlur(120)))
        d = ImageDraw.Draw(img, "RGBA")
        for yy in range(0, H, 56):
            for xx in range(0, W, 56):
                d.ellipse((xx + 26, yy + 26, xx + 30, yy + 30), fill=RED + (22,))
        logo = load_logo("dark")
    if logo is not None:
        img.alpha_composite(logo, ((W - logo.width) // 2, 150))
    _BG[style] = np.asarray(img.convert("RGB")).copy()
    return _BG[style]

def title_block(small, big, red=None, y=330, t=0.0):
    L = []
    if small:
        L.append(Layer.centered(text_img(small, F("semibold", 46), MGRAY), W / 2, y, t, anim="up"))
    size = 96
    while F("disp_black", size).getlength(big) > 940 and size > 56: size -= 4
    fb = F("disp_black", size)
    if red and red in big:
        a, b = big.split(red, 1)
        img = rich_line([(a, fb, CHAR), (red, fb, RED), (b, fb, CHAR)])
    else:
        img = text_img(big, fb, CHAR)
    L.append(Layer.centered(img, W / 2, y + 95, t + 0.08, anim="up"))
    return L

def list_item(text, icon, w=900, h=160, sub=None):
    img, m = card(w, h, r=34)
    img.alpha_composite(icon, (m + 34, m + (h - icon.height) // 2))
    fs = 56
    while F("disp_bold", fs).getlength(text) > w - icon.width - 110 and fs > 34: fs -= 2
    f = F("disp_bold", fs)
    d = ImageDraw.Draw(img)
    x = m + 34 + icon.width + 30
    if sub:
        d.text((x, m + h / 2 - 8), text, font=f, fill=CHAR, anchor="ls")
        d.text((x, m + h / 2 + 46), sub, font=F("medium", 38), fill=MGRAY, anchor="ls")
    else:
        d.text((x, m + h / 2), text, font=f, fill=CHAR, anchor="lm")
    return img, m

def _partner_logo(path, height):
    img = Image.open(path).convert("RGBA")
    bb = img.getbbox()
    if bb: img = img.crop(bb)
    return img.resize((int(img.width * height / img.height), height), Image.LANCZOS)

def cobrand_row(partner_path, target_w=300):
    """Không chèn logo mặc định; chỉ hiện logo đối tác khi EDL chủ động cung cấp."""
    pl = _partner_logo(partner_path, 96)
    if pl.width > target_w:
        pl = _partner_logo(partner_path, max(1, int(pl.height * target_w / pl.width)))
    return pl

# ---------------- SCENES ----------------
def sc_brand_reveal(s):
    """Giới thiệu sản phẩm/đối tác: logo đối tác trên thẻ trắng + tên sản phẩm + pill."""
    t0 = s["t0"]; L = []
    if s.get("small"):
        L.append(Layer.centered(text_img(s["small"], F("semibold", 46), MGRAY), W / 2, 520, t0 + 0.1, anim="up", sfx="none"))
    img, m = card(900, 380, r=48)
    lg = _partner_logo(s["logo"], 150)
    if lg.width > 760: lg = _partner_logo(s["logo"], int(150 * 760 / lg.width))
    img.alpha_composite(lg, (m + (900 - lg.width) // 2, m + (380 - lg.height) // 2))
    L.append(Layer.centered(img, W / 2, 800, s.get("logo_t", t0 + 0.3) - 0.05, anim="pop", dur=0.45))
    if s.get("title"):
        size = 100
        while F("disp_black", size).getlength(s["title"]) > 960 and size > 56: size -= 4
        L.append(Layer.centered(text_img(s["title"], F("disp_black", size), CHAR), W / 2, 1080, s.get("title_t", t0 + 0.8), anim="up"))
    if s.get("tag"):
        p = pill(s["tag"], F("bold", 46), WHITE, RED, padx=38, pady=16, icon=get_icon(s["icon"], 50) if s.get("icon") else None)
        L.append(Layer.centered(p, W / 2, 1230, s.get("tag_t", t0 + 1.4), anim="pop"))
    return scene_bg(s.get("bg", "light")), L

def sc_cards_grid(s):
    t0 = s["t0"]
    L = title_block(s.get("small"), s["title"], s.get("highlight"), t=t0 + 0.1)
    cw, chh = 430, 440
    for i, c in enumerate(s["cards"][:4]):
        img, m = card(cw, chh, r=40)
        d = ImageDraw.Draw(img)
        d.text((m + 40, m + 78), c.get("num", f"0{i + 1}"), font=F("disp_black", 48), fill=RED, anchor="ls")
        ns = 92
        while F("disp_black", ns).getlength(c["name"]) > cw - 130 and ns > 50: ns -= 4
        d.text((m + 40, m + 200), c["name"], font=F("disp_black", ns), fill=CHAR, anchor="ls")
        if c.get("ver"):
            nx = m + 40 + F("disp_black", ns).getlength(c["name"]) + 12
            d.text((nx, m + 200), c["ver"], font=F("disp_bold", 44), fill=DRED, anchor="ls")
        if c.get("tag"):
            img.alpha_composite(pill(c["tag"], F("semibold", 38), DRED, LRED, padx=24, pady=12), (m + 40, m + 245))
        if c.get("level"):
            d.text((m + 40, m + 385), s.get("level_label", "Sức mạnh"), font=F("medium", 30), fill=MGRAY, anchor="ls")
            for k in range(4):
                x0 = m + 190 + k * 52
                d.rounded_rectangle((x0, m + 360, x0 + 40, m + 386), 8, fill=RED if k < c["level"] else (230, 230, 230))
        cx, cy = 80 + (i % 2) * 490 - m, 640 + (i // 2) * 490 - m
        ts = c.get("t", t0 + 0.5 + i * 0.3)
        ghost = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(ghost)
        gd.rounded_rectangle((m, m, m + cw, m + chh), 40, fill=(255, 255, 255, 110))
        dashed_rect(gd, (m + 20, m + 20, m + cw - 20, m + chh - 20), RED + (90,), width=3)
        gd.text((m + cw / 2, m + chh / 2), c.get("num", f"0{i + 1}"), font=F("disp_black", 110), fill=RED + (60,), anchor="mm")
        if ts - t0 > 0.8:
            L.append(Layer(ghost, cx, cy, t0 + 0.35 + i * 0.12, ts, anim="fade", dur=0.3, out_dur=0.15))
        L.append(Layer(img, cx, cy, ts - 0.05, anim="pop", dur=0.4))
    return scene_bg("light"), L

def sc_rows_x(s):
    t0 = s["t0"]
    L = title_block(s.get("small"), s["title"], s.get("highlight"), t=t0 + 0.1)
    for i, r in enumerate(s["rows"][:3]):
        w, h = 900, 330
        img, m = card(w, h, r=40)
        d = ImageDraw.Draw(img)
        img.alpha_composite(get_icon(r.get("icon", "x"), 96), (m + 44, m + 50))
        d.text((m + 170, m + 118), r["title"], font=F("disp_black", 68 if len(r["title"]) < 18 else 56), fill=CHAR, anchor="ls")
        if r.get("sub"): d.text((m + 170, m + 190), r["sub"], font=F("semibold", 48 if len(r["sub"]) < 24 else 40), fill=MGRAY, anchor="ls")
        if r.get("tag"): img.alpha_composite(pill(r["tag"], F("bold", 40), WHITE, RED, padx=28, pady=12), (m + 170, m + 225))
        L.append(Layer(img, 90 - m, 640 + i * 400 - m, r.get("t", t0 + 0.4 + i * 0.5) - 0.05, anim="right", dur=0.4))
    return scene_bg("light"), L

def sc_chapter(s):
    t0 = s["t0"]
    L = [Layer.centered(text_img(s.get("num", ""), F("disp_black", 300), (255, 255, 255, 70)), W / 2, 700, t0 + 0.05, anim="left", dur=0.45, sfx="none")]
    ns = 150
    while F("disp_black", ns).getlength(s["name"]) > 960 and ns > 70: ns -= 6
    L.append(Layer.centered(text_img(s["name"], F("disp_black", ns), WHITE), W / 2, 930, t0 + 0.15, anim="pop", dur=0.45, sfx="none"))
    if s.get("tag"):
        p = pill(s["tag"], F("bold", 52), RED, WHITE, padx=40, pady=18, icon=get_icon(s.get("icon", "bolt"), 56))
        L.append(Layer.centered(p, W / 2, 1110, t0 + 0.35, anim="up"))
    return scene_bg("red"), L

def sc_checklist(s):
    t0 = s["t0"]
    L = title_block(s.get("small"), s["title"], s.get("highlight"), t=t0 + 0.1)
    items = s["items"][:5]
    step = 200 if len(items) <= 4 else 175
    for i, it in enumerate(items):
        img, m = list_item(it["text"], get_icon(it.get("icon", s.get("icon", "check")), 84), h=160 if len(items) <= 4 else 145, sub=it.get("sub"))
        L.append(Layer(img, 90 - m, 700 + i * step - m, it.get("t", t0 + 0.4 + i * 0.4) - 0.05, anim="right", dur=0.35))
    return scene_bg("light"), L

def sc_versus(s):
    t0 = s["t0"]
    L = title_block(s.get("small"), s["title"], s.get("highlight", "vs"), t=t0 + 0.1)
    for side, y, anim in (("a", 620, "left"), ("b", 1100, "right")):
        c = s[side]
        w, h = 900, 360
        img, m = card(w, h, r=44)
        d = ImageDraw.Draw(img)
        img.alpha_composite(get_icon(c.get("icon", "person" if side == "a" else "gear"), 170), (m + 50, m + (h - 170) // 2))
        d.text((m + 260, m + 140), c["name"], font=F("disp_black", 84 if len(c["name"]) < 12 else 64), fill=RED, anchor="ls")
        d.text((m + 260, m + 225), c.get("connector", "giống như"), font=F("medium", 40), fill=MGRAY, anchor="ls")
        L.append(Layer(img, 90 - m, y - m, c.get("t", t0 + 0.4), anim=anim))
        rs = 64
        while F("disp_black", rs).getlength(c["role"]) > 600 and rs > 40: rs -= 4
        L.append(Layer(text_img(c["role"], F("disp_black", rs), CHAR), 90 + 256, y + 245, c.get("t_role", c.get("t", t0 + 0.4) + 0.5), anim="up"))
    vs = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vs); dv.ellipse((0, 0, 129, 129), fill=CHAR)
    dv.text((65, 66), "VS", font=F("disp_black", 50), fill=WHITE, anchor="mm")
    L.append(Layer.centered(vs, W / 2, 1040, s.get("vs_t", s["b"].get("t", t0 + 1) - 0.2), anim="pop", sfx="none"))
    return scene_bg("light"), L

def sc_summary(s):
    t0 = s["t0"]
    L = [Layer.centered(get_icon(s.get("icon", "bookmark"), 90), W / 2, 330, t0 + 0.05, anim="pop", sfx="none")]
    fb = F("disp_black", 84)
    title, red = s["title"], s.get("highlight")
    if red and red in title:
        a, b = title.split(red, 1); hdr = rich_line([(a, fb, CHAR), (red, fb, RED), (b, fb, CHAR)])
    else:
        hdr = text_img(title, fb, CHAR)
    L.append(Layer.centered(hdr, W / 2, 460, t0 + 0.1, anim="up"))
    rows = s["rows"][:5]
    tr = s.get("t_rows", t0 + 0.4)
    for i, r in enumerate(rows):
        w, h = 920, 190 if len(rows) <= 4 else 160
        img, m = card(w, h, r=34)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((m, m, m + 300, m + h), 34, fill=RED)
        d.rectangle((m + 260, m, m + 300, m + h), fill=RED)
        ns = 54
        while F("disp_black", ns).getlength(r["name"]) > 270 and ns > 30: ns -= 2
        d.text((m + 150, m + h / 2), r["name"], font=F("disp_black", ns), fill=WHITE, anchor="mm")
        fs = 46
        while F("disp_bold", fs).getlength(r["desc"]) > w - 380 and fs > 28: fs -= 2
        d.text((m + 340, m + h / 2), r["desc"], font=F("disp_bold", fs), fill=CHAR, anchor="lm")
        L.append(Layer(img, 80 - m, 600 + i * (h + 30) - m, tr + i * 0.3, anim="right"))
    if s.get("cta_text"):
        p = pill(s["cta_text"], F("disp_black", 50), WHITE, CHAR, padx=44, pady=20, icon=get_icon("bookmark", 48) if s.get("icon", "bookmark") == "bookmark" else None)
        L.append(Layer.centered(p, W / 2, 1520, s.get("cta_t", tr + 1.5), anim="pop", sfx="ding"))
    return scene_bg("light"), L

def sc_statement(s):
    """Câu chốt lớn giữa màn hình (quote/insight)."""
    t0 = s["t0"]
    L = []
    if s.get("small"): L.append(Layer.centered(pill(s["small"], F("bold", 40), DRED, LRED, padx=30, pady=14), W / 2, 700, t0 + 0.1, anim="pop", sfx="none"))
    fb = F("disp_black", s.get("size", 92))
    para = paragraph(s["text"], fb, CHAR, 900, 1.15, align="center")
    L.append(Layer.centered(para, W / 2, 960, t0 + 0.2, anim="up"))
    if s.get("highlight"):
        L.append(Layer.centered(text_img(s["highlight"], F("script", 80), RED), W / 2, 960 + para.height / 2 + 80, s.get("highlight_t", t0 + 0.8), anim="pop"))
    return scene_bg(s.get("bg", "light")), L

SCENE_BUILDERS = {"brand_reveal": sc_brand_reveal, "cards_grid": sc_cards_grid, "rows_x": sc_rows_x, "chapter": sc_chapter, "checklist": sc_checklist,
                  "versus": sc_versus, "summary": sc_summary, "statement": sc_statement}

# ---------------- OVERLAYS (vùng y≈300-700, phía trên mặt) ----------------
OY = 300  # mép trên overlay

def ov_question_card(o):
    w = 900
    para = paragraph("“" + o["text"] + "”", F("disp_bold", 44), CHAR, w - 80, 1.22)
    h = 150 + para.height
    img, m = card(w, h, r=40)
    d = ImageDraw.Draw(img)
    img.alpha_composite(icon_chat(84, RED, "?"), (m + 36, m + 34))
    d.text((m + 140, m + 70), o.get("label", "Câu hỏi từ khán giả"), font=F("bold", 38), fill=RED, anchor="ls")
    if o.get("sub"): d.text((m + 140, m + 108), o["sub"], font=F("medium", 30), fill=MGRAY, anchor="ls")
    img.alpha_composite(para, (m + 32, m + 132))
    return [Layer(img, 90 - m, o.get("y", 250) - m, o["t0"], o.get("t1"), anim="pop", dur=0.45)]

def ov_title_box(o):
    tw, th = 860, 300 if o.get("script_line") else 200
    box = Image.new("RGBA", (tw + 120, th + 120), (0, 0, 0, 0))
    sh = Image.new("RGBA", box.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((60, 72, 60 + tw, 72 + th), fill=(0, 0, 0, 70))
    box = Image.alpha_composite(box, sh.filter(ImageFilter.GaussianBlur(22)))
    db = ImageDraw.Draw(box)
    db.rectangle((60, 60, 60 + tw, 60 + th), fill=(255, 250, 244, 250))
    dashed_rect(db, (60, 60, 60 + tw, 60 + th), CHAR, width=4)
    line, red = o["line1"], o.get("highlight")
    size = 104
    while F("disp_black", size).getlength(line) > tw - 60 and size > 56: size -= 4
    fb = F("disp_black", size)
    if red and red in line:
        a, b = line.split(red, 1); t1 = rich_line([(a, fb, CHAR), (red, fb, RED), (b, fb, CHAR)])
    else:
        t1 = text_img(line, fb, CHAR)
    box.alpha_composite(t1, (60 + (tw - t1.width) // 2, 80))
    if o.get("script_line"):
        t2 = text_img(o["script_line"], F("script", 70), CHAR)
        box.alpha_composite(t2, (60 + (tw - t2.width) // 2, 205))
    box.alpha_composite(icon_chat(92, CHAR, "?").rotate(12, expand=True, resample=Image.BICUBIC), (0, 0))
    box.alpha_composite(icon_chat(92, RED, o.get("badge", "AI")).rotate(-12, expand=True, resample=Image.BICUBIC), (tw + 10, th - 20))
    return [Layer.centered(box, W / 2, o.get("y", 1440), o["t0"], o.get("t1"), anim="pop", dur=0.5, sfx="none")]

def _head_card(title, h, o, anim="down"):
    img, m = card(880, h, r=36)
    fs = 52
    while F("disp_black", fs).getlength(title) > 800 and fs > 36: fs -= 2
    ImageDraw.Draw(img).text((m + 44, m + 84), title, font=F("disp_black", fs), fill=CHAR, anchor="ls")
    return Layer(img, 100 - m, o.get("y", OY) - m, o["t0"], o.get("t1"), anim=anim)

def ov_meter(o):
    bars = o["bars"]; y0 = o.get("y", OY)
    L = [_head_card(o["title"], 120 + 105 * len(bars), o)]
    for i, (lab, val, col) in enumerate(bars):
        col = RED if col in ("red", None) else MGRAY
        y = y0 + 125 + i * 105
        L.append(Layer(text_img(lab, F("semibold", 40), MGRAY), 136, y - 6, o["t0"] + 0.1, o.get("t1"), anim="fade"))
        for k in range(1, 11):
            bar = Image.new("RGBA", (500, 40), (0, 0, 0, 0))
            bd = ImageDraw.Draw(bar)
            bd.rounded_rectangle((0, 4, 470, 36), 16, fill=(236, 236, 236))
            sw = int(470 * val * k / 10)
            if sw > 20: bd.rounded_rectangle((0, 4, sw, 36), 16, fill=col)
            ti = o["t0"] + 0.2 + (k - 1) * 0.05
            L.append(Layer(bar, 430, y + 4, ti, (ti + 0.05) if k < 10 else o.get("t1"), anim="fade", dur=0.01, out_dur=0.01 if k < 10 else 0.2))
    return L

def _icon_list(o, icon_name):
    items = o["items"]; y0 = o.get("y", OY)
    L = [_head_card(o["title"], 120 + 110 * len(items), o)]
    for i, it in enumerate(items):
        txt, ts = (it["text"], it["t"]) if isinstance(it, dict) else it
        row = text_img(txt, F("disp_bold", 50 if len(txt) < 26 else 42), CHAR)
        r = Image.new("RGBA", (row.width + 90, max(row.height, 70)), (0, 0, 0, 0))
        r.alpha_composite(get_icon(icon_name, 64), (0, (r.height - 64) // 2)); r.alpha_composite(row, (84, (r.height - row.height) // 2))
        L.append(Layer(r, 140, y0 + 118 + i * 108, ts - 0.05, o.get("t1"), anim="left"))
    return L

def ov_x_list(o): return _icon_list(o, "x")
def ov_check_list(o): return _icon_list(o, "check")

def ov_callout(o):
    y0 = o.get("y", OY)
    L = [_head_card(o["title"], 290, o)]
    if o.get("strong"):
        segs = []
        if o.get("prefix"): segs.append((o["prefix"], F("disp_bold", 56), MGRAY))
        segs.append((o["strong"], F("disp_black", 72), RED))
        L.append(Layer(rich_line(segs), 136, y0 + 130, o.get("strong_t", o["t0"] + 0.6), o.get("t1"), anim="left" if o.get("prefix") else "pop"))
    if o.get("stamp"):
        st = o["stamp"]
        stamp = Image.new("RGBA", (330, 110), (0, 0, 0, 0))
        ds = ImageDraw.Draw(stamp)
        ds.rounded_rectangle((4, 4, 325, 105), 18, outline=RED, width=7)
        fs = 42
        while F("disp_black", fs).getlength(st["text"]) > 290: fs -= 2
        ds.text((165, 57), st["text"], font=F("disp_black", fs), fill=RED, anchor="mm")
        stamp = stamp.resize((264, 88), Image.LANCZOS).rotate(-10, expand=True, resample=Image.BICUBIC)
        L.append(Layer.centered(stamp, 850, y0 + 72, st["t"], o.get("t1"), anim="stamp", dur=0.25, sfx="ding"))
    return L

def ov_chips(o):
    y0 = o.get("y", OY)
    L = [_head_card(o["title"], 330 if o.get("note") else 250, o)]
    x = 140
    for txt, ts in o["chips"]:
        p = pill(txt, F("disp_bold", 46), WHITE, RED, padx=32, pady=14)
        if x + p.width > 960: break
        L.append(Layer(p, x, y0 + 120, ts - 0.04, o.get("t1"), anim="pop"))
        x += p.width + 20
    if o.get("note"):
        n = o["note"]
        segs = [(n.get("text", ""), F("semibold", 40), MGRAY)]
        if n.get("strong"): segs.append((n["strong"], F("disp_bold", 40), CHAR))
        L.append(Layer(rich_line(segs), 136, y0 + 225, n.get("t", o["t0"] + 1.5), o.get("t1"), anim="up"))
    return L

def ov_warning(o):
    img, m = card(880, 230, r=36)
    d = ImageDraw.Draw(img)
    img.alpha_composite(icon_warn(110), (m + 40, m + 60))
    d.text((m + 180, m + 95), o.get("label", "Lưu ý"), font=F("bold", 40), fill=MGRAY, anchor="ls")
    fs = 58
    while F("disp_black", fs).getlength(o["text"]) > 660 and fs > 36: fs -= 2
    d.text((m + 180, m + 165), o["text"], font=F("disp_black", fs), fill=CHAR, anchor="ls")
    return [Layer(img, 100 - m, o.get("y", OY) - m, o["t0"], o.get("t1"), anim="pop")]

def ov_cta(o):
    checks = o.get("checks", [])
    h = 250 + 72 * len(checks) + 90
    img, m = card(900, h, r=36)
    d = ImageDraw.Draw(img)
    logo = cobrand_row(o["partner_logo"], 260) if o.get("partner_logo") else load_logo("dark", 300)
    if logo is not None: img.alpha_composite(logo, (m + 44, m + 40 + (78 - logo.height) // 2))
    fs = 64
    while F("disp_black", fs).getlength(o["headline"]) > 810: fs -= 2
    d.text((m + 44, m + 185), o["headline"], font=F("disp_black", fs), fill=CHAR, anchor="ls")
    for i, t_ in enumerate(checks):
        img.alpha_composite(icon_check(52), (m + 44, m + 222 + i * 72))
        d.text((m + 116, m + 262 + i * 72), t_, font=F("disp_bold", 44), fill=CHAR, anchor="ls")
    yl = m + 250 + 72 * len(checks)
    d.line((m + 44, yl - 10, m + 856, yl - 10), fill=(230, 230, 230), width=2)
    d.text((m + 44, yl + 50), o.get("contact", BRAND.get("contact_line", "")), font=F("disp_black", 46), fill=RED, anchor="ls")
    y0 = o.get("y", 260)
    L = [Layer(img, 90 - m, y0 - m, o["t0"], o.get("t1"), anim="down", dur=0.45)]
    if o.get("pill"):
        p = o["pill"]
        cm = pill(p["text"], F("disp_bold", 46), WHITE, RED, padx=36, pady=18, icon=icon_chat(52, WHITE, "…"))
        L.append(Layer.centered(cm, W / 2, y0 + h + 80, p["t"], o.get("t1"), anim="pop"))
    return L

def ov_lower_third(o):
    """Thẻ tên người nói (hiện 3-4s đầu video)."""
    nm = text_img(o.get("name", BRAND.get("presenter", "Mạnh Thành")), F("disp_black", 56), CHAR)
    rl = text_img(o.get("role", ""), F("semibold", 36), MGRAY)
    w = max(nm.width, rl.width) + 80
    img, m = card(w, 170, r=28)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((m, m, m + 14, m + 170), 7, fill=RED)
    img.alpha_composite(nm, (m + 40, m + 18)); img.alpha_composite(rl, (m + 40, m + 98))
    return [Layer(img, 70 - m, o.get("y", 1180) - m, o["t0"], o.get("t1"), anim="left")]

def ov_badge(o):
    """Pill nổi đơn lẻ, ví dụ con số / từ khoá."""
    p = pill(o["text"], F("disp_black", o.get("size", 56)), WHITE, RED if o.get("color", "red") == "red" else CHAR, padx=40, pady=18,
             icon=get_icon(o["icon"], 56) if o.get("icon") else None)
    return [Layer.centered(p, o.get("x", W / 2), o.get("y", 420), o["t0"], o.get("t1"), anim="pop")]

OVERLAY_BUILDERS = {"question_card": ov_question_card, "title_box": ov_title_box, "meter": ov_meter, "x_list": ov_x_list,
                    "check_list": ov_check_list, "callout": ov_callout, "chips": ov_chips, "warning": ov_warning,
                    "cta": ov_cta, "lower_third": ov_lower_third, "badge": ov_badge}
