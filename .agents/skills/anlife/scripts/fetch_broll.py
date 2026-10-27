#!/usr/bin/env python3
"""Tìm & tải cảnh trám (B-roll) cho các scene type "broll"/"image" có "query" mà chưa có "clip"/"src".

  python3 fetch_broll.py edl.json --preview     # tải thumbnail ứng viên -> <workdir>/broll/candidates_<t0>.jpg (xem rồi đặt "pick")
  python3 fetch_broll.py edl.json               # tải clip đã chọn (pick, mặc định 0), ghi đường dẫn vào EDL (có backup .bak)

API key (miễn phí): --pexels KEY / --pixabay KEY, hoặc env PEXELS_API_KEY / PIXABAY_API_KEY, hoặc assets/config.json.
Query nên bằng tiếng Anh, cụ thể, mô tả hình ảnh (vd "person typing laptop office close up").
"""
import sys, os, json, argparse, urllib.request, urllib.parse, shutil, io
from PIL import Image, ImageDraw

SKILL = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CFG = json.load(open(os.path.join(SKILL, "assets", "config.json"), encoding="utf-8"))
ap = argparse.ArgumentParser()
ap.add_argument("edl"); ap.add_argument("--preview", action="store_true")
ap.add_argument("--pexels", default=os.environ.get("PEXELS_API_KEY") or CFG.get("pexels_api_key"))
ap.add_argument("--pixabay", default=os.environ.get("PIXABAY_API_KEY") or CFG.get("pixabay_api_key"))
a = ap.parse_args()
if not a.pexels and not a.pixabay:
    sys.exit("THIẾU API KEY: cần Pexels (pexels.com/api) hoặc Pixabay (pixabay.com/api/docs). "
             "Hoặc dùng clip/ảnh người dùng upload: đặt 'clip'/'src' trực tiếp trong EDL.")

EDL_PATH = os.path.abspath(a.edl); BASE = os.path.dirname(EDL_PATH)
EDL = json.load(open(EDL_PATH, encoding="utf-8"))
WORK = os.path.join(BASE, EDL.get("workdir", ".")) if not os.path.isabs(EDL.get("workdir", ".")) else EDL["workdir"]
BD = os.path.join(WORK, "broll"); os.makedirs(BD, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 video-editor-skill"}

def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

def download(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f: shutil.copyfileobj(r, f)
    return path

def search_videos(q, orient, need_dur):
    cands = []
    if a.pexels:
        try:
            j = get_json("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
                {"query": q, "orientation": orient, "size": "medium", "per_page": 15}), {"Authorization": a.pexels})
            for v in j.get("videos", []):
                files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("height")]
                if not files: continue
                tgt = 1920 if orient == "portrait" else 1080          # chiều cao mong muốn
                ok = [f for f in files if f["height"] <= 2200] or files  # tránh tải 4K
                f = min(ok, key=lambda f: abs(f["height"] - tgt))
                cands.append(dict(src="pexels", id=v["id"], dur=v["duration"], w=f["width"], h=f["height"], url=f["link"],
                                  thumb=v.get("image"), page=v.get("url"), author=v.get("user", {}).get("name")))
        except Exception as e: print("Pexels lỗi:", e)
    if a.pixabay and len(cands) < 6:
        try:
            j = get_json("https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": a.pixabay, "q": q, "per_page": 20, "safesearch": "true"}))
            for v in j.get("hits", []):
                vs = v["videos"]; f = vs.get("large") if vs.get("large", {}).get("url") else vs.get("medium")
                if not f or not f.get("url"): continue
                is_port = f["height"] > f["width"]
                if orient == "portrait" and not is_port: continue
                cands.append(dict(src="pixabay", id=v["id"], dur=v["duration"], w=f["width"], h=f["height"], url=f["url"],
                                  thumb=f.get("thumbnail") or vs.get("tiny", {}).get("thumbnail"), page=v.get("pageURL"), author=v.get("user")))
        except Exception as e: print("Pixabay lỗi:", e)
    # ưu tiên clip đủ dài
    cands.sort(key=lambda c: (c["dur"] < need_dur, 0))
    return cands

def search_photos(q, orient):
    cands = []
    if a.pexels:
        try:
            j = get_json("https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": q, "orientation": orient, "per_page": 12}),
                         {"Authorization": a.pexels})
            for p in j.get("photos", []):
                cands.append(dict(src="pexels", id=p["id"], url=p["src"]["large2x"], thumb=p["src"]["medium"], page=p["url"], author=p["photographer"]))
        except Exception as e: print("Pexels lỗi:", e)
    if a.pixabay and len(cands) < 6:
        try:
            j = get_json("https://pixabay.com/api/?" + urllib.parse.urlencode({"key": a.pixabay, "q": q, "per_page": 20, "image_type": "photo",
                                                                              "orientation": "vertical" if orient == "portrait" else "horizontal"}))
            for p in j.get("hits", []):
                cands.append(dict(src="pixabay", id=p["id"], url=p["largeImageURL"], thumb=p["webformatURL"], page=p["pageURL"], author=p["user"]))
        except Exception as e: print("Pixabay lỗi:", e)
    return cands

def contact(cands, path, title):
    ims = []
    for c in cands[:8]:
        try:
            req = urllib.request.Request(c["thumb"], headers=UA)
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
            im.thumbnail((300, 300)); ims.append((c, im))
        except Exception: pass
    if not ims: return
    sheet = Image.new("RGB", (310 * len(ims), 360), "black"); d = ImageDraw.Draw(sheet)
    for i, (c, im) in enumerate(ims):
        sheet.paste(im, (i * 310, 30))
        info = f"#{i} {c.get('dur', '')}s {c.get('w', '')}x{c.get('h', '')}" if "dur" in c else f"#{i}"
        d.text((i * 310 + 6, 334), info, fill="white")
    d.text((6, 6), title[:150], fill="yellow")
    sheet.save(path, quality=85)

credits_path = os.path.join(BD, "credits.json")
credits = json.load(open(credits_path)) if os.path.exists(credits_path) else []
used, changed = set(), False
for s in EDL.get("scenes", []):
    if s["type"] not in ("broll", "image") or not s.get("query"): continue
    if (s["type"] == "broll" and s.get("clip")) or (s["type"] == "image" and s.get("src")):
        continue
    dur = s["t1"] - s["t0"]
    orient = "portrait" if s.get("layout", "full") == "full" else "landscape"
    queries = s["query"] if isinstance(s["query"], list) else [s["query"]]
    cands = []
    for q in queries:
        cands += search_videos(q, orient, dur) if s["type"] == "broll" else search_photos(q, orient)
        if len(cands) >= 6: break
    cands = [c for c in cands if (c["src"], c["id"]) not in used]
    tag = f"{s['t0']:07.2f}"
    if not cands:
        print(f"[{tag}] KHÔNG tìm thấy cho {queries} — đổi query hoặc chuyển scene thành graphic"); continue
    if a.preview:
        p = os.path.join(BD, f"candidates_{tag}.jpg"); contact(cands, p, f"t={s['t0']} {queries}")
        json.dump(cands[:8], open(os.path.join(BD, f"candidates_{tag}.json"), "w"), indent=1)
        print(f"[{tag}] {len(cands)} ứng viên -> {p}"); continue
    c = cands[min(s.get("pick", 0), len(cands) - 1)]
    ext = ".mp4" if s["type"] == "broll" else ".jpg"
    path = os.path.join(BD, f"{c['src']}_{c['id']}{ext}")
    if not os.path.exists(path): download(c["url"], path)
    used.add((c["src"], c["id"]))
    s["clip" if s["type"] == "broll" else "src"] = os.path.relpath(path, BASE)
    credits.append({k: c.get(k) for k in ("src", "id", "page", "author")} | {"scene_t0": s["t0"]})
    changed = True
    print(f"[{tag}] OK {c['src']} #{c['id']} {c.get('dur', '')}s -> {path}")
if changed:
    shutil.copy(EDL_PATH, EDL_PATH + ".bak")
    json.dump(EDL, open(EDL_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(credits, open(credits_path, "w"), indent=1, ensure_ascii=False)
    print("EDL đã cập nhật đường dẫn clip. Credits:", credits_path)
print("DONE")
