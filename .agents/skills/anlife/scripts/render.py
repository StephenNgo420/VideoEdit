#!/usr/bin/env python3
"""Render video từ EDL JSON.

  python3 render.py edl.json stills 1.5 22 47        # ảnh xem trước -> <workdir>/stills/ + contact sheet
  python3 render.py edl.json render [t0 t1]          # render video không tiếng -> <workdir>/video_only.mp4
  python3 render.py edl.json events                  # chỉ xuất sfx_events.json

Render full mất khoảng (thời lượng x 30 / 4) giây trên 1 CPU -> luôn chạy nền bằng run_bg.sh.
"""
import sys, os, json, math, subprocess, hashlib, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
import numpy as np, cv2
from PIL import Image, ImageDraw
import gfx
from gfx import *
from components import SCENE_BUILDERS, OVERLAY_BUILDERS

GRADES = {
    # Mặc định: giữ nguyên màu gốc (màu da, nhiệt màu, độ bão hoà) — chỉ làm mịn da nhẹ (xem skin_smooth)
    "natural": "null",
    "warm_clean": ("huesaturation=saturation=-0.35:colors=m+b:strength=1,"
                   "colorbalance=rm=-0.02:gm=0.03:bm=-0.03:rh=-0.02:gh=0.03:bh=-0.02,"
                   "curves=all='0/0 0.25/0.27 0.5/0.56 0.8/0.84 1/1',"
                   "eq=contrast=1.05:saturation=0.97,colortemperature=temperature=6000:mix=0.35,vignette=angle=PI/7"),
    "neutral": "curves=all='0/0 0.25/0.26 0.5/0.53 0.8/0.83 1/1',eq=contrast=1.05:saturation=1.03,vignette=angle=PI/8",
    "bright": "curves=all='0/0 0.25/0.29 0.5/0.58 0.8/0.86 1/1',eq=contrast=1.03:saturation=1.02",
    "none": "null",
}
BROLL_GRADE = "eq=contrast=1.04:saturation=1.02"

# =================== EDL ===================
EDL_PATH = os.path.abspath(sys.argv[1])
EDL = json.load(open(EDL_PATH, encoding="utf-8"))
BASE = os.path.dirname(EDL_PATH)
def P(p): return p if os.path.isabs(p) else os.path.join(BASE, p)
WORK = P(EDL.get("workdir", "."))
os.makedirs(WORK, exist_ok=True)
SRC = P(EDL["source"])
FPS = 30

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_tags=rotate:format=duration",
                          "-of", "json", path], capture_output=True, text=True).stdout
    j = json.loads(out); s = j["streams"][0]
    return s["width"], s["height"], float(j["format"]["duration"])

SW, SH, SDUR = probe(SRC)
DUR = float(EDL.get("duration", SDUR))
grade = EDL.get("grade", "natural")
GRADE = GRADES.get(grade, grade)
# Nguồn ngang -> cắt 9:16 quanh tâm (reframe_x = toạ độ x của mặt trong nguồn, mặc định giữa)
if SW / SH > 0.6:
    rx = EDL.get("reframe_x", SW / 2)
    cw = int(SH * 9 / 16) // 2 * 2
    x0 = int(min(max(rx - cw / 2, 0), SW - cw))
    PRE = f"crop={cw}:{SH}:{x0}:0,scale=1080:1920,"
else:
    PRE = "scale=1080:1920,"
VF = PRE + GRADE + ",fps=30,format=rgb24"
FACE = tuple(EDL.get("face", [540, 950]))

# =================== MỊN DA ===================
# Làm mịn nhẹ chỉ trên vùng màu da, KHÔNG đổi màu: bilateral ở nửa độ phân giải, chỉ cộng phần chênh lệch
# (tầng tần số trung — mụn, vết thâm, lỗ chân lông to) vào khung gốc; chi tiết tần số cao (sợi tóc, mép mắt, vân vải)
# giữ nguyên nên da không bị "bết nhựa". skin_smooth: 0 = tắt, 0.35 = nhẹ (mặc định), 0.6 = vừa, >0.7 dễ lộ giả.
SKIN = float(EDL.get("skin_smooth", 0.35))
_K5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

def skin_smooth(frame):
    if SKIN <= 0: return frame
    h, w = frame.shape[:2]
    sm = cv2.resize(frame, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    m = cv2.inRange(cv2.cvtColor(sm, cv2.COLOR_RGB2YCrCb), (40, 135, 85), (250, 178, 132))   # dải màu da
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, _K5)
    ys, xs = np.nonzero(m)
    if len(ys) < 200: return frame                     # không thấy da (B-roll, khung trống) -> bỏ qua
    # chỉ xử lý khung bao vùng da (thường ~25% khung) -> ~20–30 ms/khung trên 1 CPU
    y0, y1 = max(ys.min() - 12, 0), min(ys.max() + 13, h // 2)
    x0, x1 = max(xs.min() - 12, 0), min(xs.max() + 13, w // 2)
    roi = sm[y0:y1, x0:x1]
    mk = cv2.GaussianBlur(m[y0:y1, x0:x1], (0, 0), 5).astype(np.float32) * (min(SKIN, 1.0) / 255.0)
    d = (cv2.bilateralFilter(roi, 7, 28, 5).astype(np.float32) - roi) * mk[..., None]
    d = cv2.resize(d, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_LINEAR)
    out = frame.copy()
    Y0, X0 = y0 * 2, x0 * 2
    sub = out[Y0:Y0 + d.shape[0], X0:X0 + d.shape[1]]
    d = d[:sub.shape[0], :sub.shape[1]]
    out[Y0:Y0 + d.shape[0], X0:X0 + d.shape[1]] = np.clip(sub + d, 0, 255).astype(np.uint8)
    return out

# =================== TRANSCRIPT ===================
CAP = EDL.get("captions", {})
FIX = CAP.get("fixes", {})
MERGES = [tuple(m) for m in CAP.get("merges", [])]
KEYWORDS = set(k.lower() for k in CAP.get("keywords", []))

def load_words():
    tp = P(EDL.get("transcript", os.path.join(WORK, "transcript.json")))
    if not os.path.exists(tp): return []
    segs = json.load(open(tp, encoding="utf-8"))
    out = []
    for s in segs:
        ws = []
        for w in s["words"]:
            tok = w["w"].strip()
            core = tok.rstrip(",.?!"); punct = tok[len(core):]
            if tok in FIX: tok = FIX[tok]
            elif core in FIX: tok = FIX[core] + punct
            ws.append(dict(w=tok, s=w["s"], e=w["e"]))
        merged = []
        for w in ws:
            if merged and w["w"].startswith(".") and merged[-1]["w"][-1:].isdigit():
                merged[-1]["w"] += w["w"]; merged[-1]["e"] = w["e"]; continue
            hit = False
            for a, b, r in MERGES:
                if merged and merged[-1]["w"].rstrip(",.") == a and w["w"].rstrip(",.?!") == b:
                    merged[-1]["w"] = r + w["w"][len(b):]; merged[-1]["e"] = w["e"]; hit = True; break
            if not hit: merged.append(w)
        if merged: merged[-1]["eos"] = True
        out += merged
    for ov in CAP.get("word_overrides", []):   # {"t": 105.8, "w": "tác"}
        for w in out:
            if abs(w["s"] - ov["t"]) < 0.06: w["w"] = ov["w"]
    return [w for w in out if w["w"]]

WORDS = load_words()

def chunk_words(words, maxw, maxc):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        if len(cur) >= maxw or len(txt) >= maxc or w["w"][-1] in ",.?!" or w.get("eos"):
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    res = []
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else c[-1]["e"] + 0.5
        res.append(dict(words=c, t0=c[0]["s"], t1=min(nxt, c[-1]["e"] + 0.45)))
    return res

CHUNKS = chunk_words(WORDS, CAP.get("max_words", 3), CAP.get("max_chars", 17))
CAP_Y = CAP.get("y", 1475)
CAP_EXCLUDE = CAP.get("exclude", [])
_cap_cache = {}

def clean(w): return w if w.endswith("?") else w.rstrip(",.!")

def cap_img(ci, active):
    key = (ci, active)
    if key in _cap_cache: return _cap_cache[key]
    words = [clean(w["w"]) for w in CHUNKS[ci]["words"]]
    size = CAP.get("size", 70)
    while True:
        f = F("disp_xbold", size); sp = f.getlength(" ")
        widths = [f.getlength(w) for w in words]
        tw = sum(widths) + sp * (len(words) - 1) + 24 * len(words)
        if tw < 880 or size < 46: break
        size -= 4
    asc, desc = f.getmetrics()
    padx, pady = 30, 20
    cw, chh = int(tw + padx * 2), asc + desc + pady * 2
    img, m = card(cw, chh, r=30, fill=(255, 255, 255, 246), shadow=80, blur=18, off=8)
    d = ImageDraw.Draw(img)
    x = m + padx
    for i, (w, ww) in enumerate(zip(words, widths)):
        if i == active:
            d.rounded_rectangle((x - 2, m + 10, x + ww + 22, m + chh - 10), 16, fill=RED); col = WHITE
        else:
            col = DRED if w.lower().strip("?") in KEYWORDS else CHAR
        d.text((x + 10, m + pady + asc), w, font=f, fill=col, anchor="ls")
        x += ww + sp + 24
    _cap_cache[key] = to_np(img)
    return _cap_cache[key]

def draw_captions(dst, t, y=None):
    if not CAP.get("enabled", True): return
    for a, b in CAP_EXCLUDE:
        if a <= t < b: return
    for ci, ch in enumerate(CHUNKS):
        if ch["t0"] <= t < ch["t1"]:
            act = max([i for i, w in enumerate(ch["words"]) if w["s"] <= t], default=-1)
            a = cap_img(ci, act)
            p = (t - ch["t0"]) / 0.12
            if p < 1:
                sc = 0.9 + 0.1 * ease_out_back(p); h, w = a.shape[:2]
                a = cv2.resize(a, (int(w * sc), int(h * sc)))
            blend(dst, a, W / 2 - a.shape[1] / 2, (y or CAP_Y) - a.shape[0] / 2, clamp(p * 1.5))
            return

# =================== ZOOM ===================
SHOTS = EDL.get("shots", [])
PUNCH = EDL.get("punches", [])

def zoom_at(t):
    for t0, t1, a, b in SHOTS:
        if t0 <= t < t1:
            s = a + (b - a) * ease_in_out((t - t0) / (t1 - t0))
            for tp, k in PUNCH:
                if t0 <= tp <= t: s *= 1 + (k - 1) * ease_out_cubic((t - tp) / 0.18)
            return s
    return 1.0

def apply_zoom(frame, s, center=FACE):
    if s <= 1.001: return frame
    cx, cy = center
    M = np.float32([[s, 0, cx - s * cx], [0, s, cy - s * cy]])
    return cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# =================== B-ROLL ===================
def prep_clip(src, dur, w, h, start=0.0):
    src = P(src)
    key = hashlib.md5(f"{src}|{dur:.2f}|{w}x{h}|{start}".encode()).hexdigest()[:10]
    out = os.path.join(WORK, "broll", f"prep_{key}.mp4")
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-ss", str(start), "-i", src, "-t", f"{dur + 0.5:.2f}", "-an",
                        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30,{BROLL_GRADE}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", out], check=True)
    return out

class ClipReader:
    def __init__(self, path):
        self.path, self.cap, self.idx, self.last = path, None, -1, None
    def frame(self, i):
        if self.cap is None or i < self.idx:
            if self.cap: self.cap.release()
            self.cap = cv2.VideoCapture(self.path); self.idx = -1
        while self.idx < i:
            ok, fr = self.cap.read()
            if not ok: break
            self.idx += 1; self.last = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        return self.last

def cover_image(path, w, h):
    img = Image.open(P(path)).convert("RGB")
    s = max(w * 1.12 / img.width, h * 1.12 / img.height)
    img = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    return np.asarray(img)

def headline_layers(s, y=380):
    L = []
    if not s.get("headline"): return L
    size = s.get("headline_size", 88)
    while F("disp_black", size).getlength(s["headline"]) > 940 and size > 64: size -= 4
    fb = F("disp_black", size)
    lines = wrap(s["headline"], fb, 940)
    red = s.get("headline_highlight")
    for i, line in enumerate(lines):
        if red and red in line:
            a, b = line.split(red, 1); img = rich_line([(a, fb, WHITE), (red, fb, RED), (b, fb, WHITE)])
        else:
            img = text_img(line, fb, WHITE)
        L.append(Layer.centered(img, W / 2, y + i * int(fb.size * 1.15), s["t0"] + 0.25 + i * 0.08, anim="up", sfx="none"))
    return L

TOP_SHADE = None
def top_shade():
    global TOP_SHADE
    if TOP_SHADE is None:
        a = np.zeros((900, W, 4), np.uint8)
        a[..., 3] = (np.linspace(1, 0, 900) ** 1.6 * 190).astype(np.uint8)[:, None]
        TOP_SHADE = a
    return TOP_SHADE

# =================== SCENES & OVERLAYS ===================
SCENES = []    # dict: t0,t1,kind('graphic'|'broll'), full(bool), ...
OVERLAYS = []
PILLS = EDL.get("chapters", [])

def setup():
    for s in EDL.get("scenes", []):
        t0, t1 = s["t0"], s["t1"]
        gfx.EVENTS.append((round(t0 - 0.15, 3), "whoosh"))
        if s["type"] in ("broll", "image"):
            layout = s.get("layout", "full")
            w, h = (W, H) if layout == "full" else (W, H // 2)
            sc = dict(t0=t0, t1=t1, kind=s["type"], layout=layout, full=layout == "full", spec=s,
                      layers=headline_layers(s, s.get("headline_y", 380 if layout == "full" else 240)))
            if s["type"] == "broll":
                src = s.get("clip")
                if not src or not os.path.exists(P(src)):
                    print(f"CẢNH BÁO: scene broll {t0}-{t1} chưa có clip hợp lệ -> bỏ qua (chạy fetch_broll.py hoặc đặt 'clip')")
                    gfx.EVENTS.pop(); continue
                sc["reader"] = ClipReader(prep_clip(src, t1 - t0, w, h, s.get("start", 0.0)))
            else:
                if not s.get("src") or not os.path.exists(P(s["src"])):
                    print(f"CẢNH BÁO: scene image {t0}-{t1} chưa có ảnh -> bỏ qua"); gfx.EVENTS.pop(); continue
                sc["img"] = cover_image(s["src"], w, h)
            SCENES.append(sc)
        else:
            bg, layers = SCENE_BUILDERS[s["type"]](s)
            SCENES.append(dict(t0=t0, t1=t1, kind="graphic", full=True, bg=bg, layers=layers))
    for o in EDL.get("overlays", []):
        OVERLAYS.extend(OVERLAY_BUILDERS[o["type"]](o))
    ev = sorted(set(gfx.EVENTS))
    for e in EDL.get("sfx_extra", []): ev.append((e["t"], e.get("type", "pop")))
    ev = [e for e in sorted(ev) if 0 <= e[0] < DUR]
    ded = []
    for t, k in ev:   # bỏ pop quá sát nhau
        if ded and k == "pop" and ded[-1][1] in ("pop", "whoosh") and t - ded[-1][0] < 0.14: continue
        ded.append((t, k))
    json.dump([{"t": t, "type": k} for t, k in ded], open(os.path.join(WORK, "sfx_events.json"), "w"), indent=0)

_pill_cache = {}
def draw_pill(dst, t):
    for t0, t1, txt in PILLS:
        if t0 <= t < t1:
            if txt not in _pill_cache: _pill_cache[txt] = to_np(pill(txt, F("disp_bold", 36), WHITE, RED, padx=26, pady=12))
            blend(dst, _pill_cache[txt], 70, 175, clamp((t - t0) / 0.25) * (1 - clamp((t - (t1 - 0.2)) / 0.2)))

def scene_at(t):
    for sc in SCENES:
        if sc["t0"] - 0.001 <= t < sc["t1"]: return sc
    return None

def broll_frame(sc, t, w, h):
    lt = t - sc["t0"]; s = sc["spec"]
    if sc["kind"] == "broll":
        fr = sc["reader"].frame(int(lt * FPS))
        if fr is None: fr = np.zeros((h, w, 3), np.uint8)
        if s.get("kenburns", True):
            fr = apply_zoom(fr, 1.0 + 0.06 * lt / max(0.1, sc["t1"] - sc["t0"]), (w / 2, h / 2))
        return np.ascontiguousarray(fr)
    img = sc["img"]; ih, iw = img.shape[:2]
    p = lt / max(0.1, sc["t1"] - sc["t0"])
    z = 1.0 + 0.1 * p if s.get("zoom", "in") == "in" else 1.1 - 0.1 * p
    base_w = min(iw, ih * w / h); base_h = base_w * h / w          # khung lớn nhất đúng tỉ lệ đích
    cw, ch = int(base_w / z), int(base_h / z)
    pan = 1 if s.get("pan", "right") == "right" else -1
    cx, cy = iw / 2 + (iw - cw) * 0.35 * (p - 0.5) * pan, ih / 2
    x0 = int(min(max(cx - cw / 2, 0), iw - cw)); y0 = int(min(max(cy - ch / 2, 0), ih - ch))
    crop = img[y0:y0 + ch, x0:x0 + cw]
    return cv2.resize(crop, (w, h), interpolation=cv2.INTER_LINEAR)

def transition_alpha(sc, t):
    pin = ease_out_cubic((t - sc["t0"]) / 0.25)
    pout = 1 - clamp((t - (sc["t1"] - 0.2)) / 0.2)
    return pin, pin * pout

def compose(frame, t):
    speaker = apply_zoom(skin_smooth(frame), zoom_at(t)).copy()
    sc = scene_at(t)
    out = speaker
    talking_ui = sc is None or not sc["full"] or (t - sc["t0"] < 0.25) or (sc["t1"] - t < 0.2)
    if talking_ui and not (sc is not None and not sc["full"]):
        for L in OVERLAYS: L.draw(out, t)
        draw_pill(out, t)
        draw_captions(out, t)
    if sc is not None:
        pin, a = transition_alpha(sc, t)
        if sc["kind"] == "graphic":
            layer = sc["bg"].copy()
            for L in sc["layers"]: L.draw(layer, t)
        elif sc["full"]:
            layer = broll_frame(sc, t, W, H).copy()
            if sc["spec"].get("headline"): blend(layer, top_shade(), 0, 0)
            for L in sc["layers"]: L.draw(layer, t)
            if sc["spec"].get("captions", True): draw_captions(layer, t)
        else:   # split: B-roll trên, người nói dưới
            layer = np.empty_like(out)
            layer[:H // 2] = broll_frame(sc, t, W, H // 2)
            y0 = int(min(max(FACE[1] - sc["spec"].get("speaker_face_y", 330), 0), H - H // 2))
            layer[H // 2:] = speaker[y0:y0 + H // 2]
            layer[H // 2 - 3:H // 2 + 3] = RED
            if sc["spec"].get("headline"): blend(layer, top_shade()[:560], 0, 0)
            for L in sc["layers"]: L.draw(layer, t)
            if sc["spec"].get("captions", True): draw_captions(layer, t, y=H // 2 + 20)
        if pin < 1:
            s = 1.06 - 0.06 * pin
            M = np.float32([[s, 0, W / 2 - s * W / 2], [0, s, H / 2 - s * H / 2]])
            layer = cv2.warpAffine(layer, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
        out = layer if a >= 0.999 else cv2.addWeighted(layer, a, out, 1 - a, 0)
    if EDL.get("progress_bar", True):
        pw = int(W * t / DUR)
        out[0:8, :] = (out[0:8, :].astype(np.uint16) * 60 // 100 + 100).astype(np.uint8)
        out[0:8, :pw] = RED
    if t > DUR - 0.35:
        out = (out.astype(np.float32) * clamp((DUR - t) / 0.35)).astype(np.uint8)
    return out

# =================== IO ===================
def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", SRC, "-frames:v", "1", "-vf", VF, "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()

def stills(times):
    d = os.path.join(WORK, "stills"); os.makedirs(d, exist_ok=True)
    ims = []
    for t in times:
        im = Image.fromarray(compose(grab(t), t))
        im.save(os.path.join(d, f"still_{t:07.2f}.jpg"), quality=88)
        ims.append(im.resize((270, 480)))
    for k in range(0, len(ims), 5):
        sheet = Image.new("RGB", (270 * 5, 510), "black")
        dd = ImageDraw.Draw(sheet)
        for i, im in enumerate(ims[k:k + 5]):
            sheet.paste(im, (i * 270, 0)); dd.text((i * 270 + 8, 486), f"t={times[k + i]}", fill="white")
        sheet.save(os.path.join(d, f"sheet_{k // 5}.jpg"), quality=85)
    print("stills ->", d)

def render(t0, t1, out_path):
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", SRC, "-an", "-vf", VF, "-f", "rawvideo", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high", out_path],
                           stdin=subprocess.PIPE)
    n, st, fs = 0, time.time(), W * H * 3
    total = int((t1 - t0) * FPS)
    while True:
        buf = dec.stdout.read(fs)
        if len(buf) < fs: break
        t = t0 + n / FPS
        enc.stdin.write(compose(np.frombuffer(buf, np.uint8).reshape(H, W, 3), t).tobytes())
        n += 1
        if n % 150 == 0:
            sp = n / (time.time() - st)
            print(f"frame {n}/{total} t={t:.1f}s {sp:.1f}fps ETA {(total - n) / sp / 60:.1f} phút", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f"DONE {n} frames in {time.time() - st:.0f}s -> {out_path}", flush=True)

if __name__ == "__main__":
    mode = sys.argv[2]
    setup()
    if mode == "stills":
        stills([float(x) for x in sys.argv[3:]])
    elif mode == "render":
        if len(sys.argv) >= 5: render(float(sys.argv[3]), float(sys.argv[4]), os.path.join(WORK, "test_segment.mp4"))
        else: render(0, DUR, os.path.join(WORK, "video_only.mp4"))
    elif mode == "events":
        print("events ->", os.path.join(WORK, "sfx_events.json"))
