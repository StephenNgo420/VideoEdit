#!/usr/bin/env python3
"""Khảo sát video nguồn: thông số, contact sheet 6 khung, ước lượng vị trí mặt.
  python3 probe.py <video> <workdir>
In ra JSON gợi ý: duration, orientation, face (toạ độ trong khung 1080x1920 đầu ra), reframe_x (nếu nguồn ngang)."""
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw

src, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
    "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size", "-of", "json", src],
    capture_output=True, text=True).stdout)
v = [s for s in j["streams"] if s["codec_type"] == "video"][0]
has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
w, h, dur = v["width"], v["height"], float(j["format"]["duration"])
times = [dur * k / 7 for k in range(1, 7)]
det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
faces, thumbs = [], []
for t in times:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY)
    fs = det.detectMultiScale(g, 1.1, 6, minSize=(int(min(w, h) * 0.08),) * 2)
    if len(fs):
        x, y, fw, fh = max(fs, key=lambda r: r[2] * r[3]); faces.append((x + fw / 2, y + fh / 2, fw))
    im = Image.fromarray(fr); im.thumbnail((360, 640)); thumbs.append(im)
sheet = Image.new("RGB", (sum(t.width for t in thumbs), max(t.height for t in thumbs) + 24), "black")
d = ImageDraw.Draw(sheet); x = 0
for t, im in zip(times, thumbs):
    sheet.paste(im, (x, 0)); d.text((x + 6, im.height + 4), f"t={t:.1f}s", fill="white"); x += im.width
sheet.save(os.path.join(work, "contact_sheet.jpg"), quality=85)

res = dict(duration=round(dur, 2), width=w, height=h, codec=v["codec_name"], fps=v["r_frame_rate"], has_audio=has_audio,
           size_mb=round(int(j["format"]["size"]) / 1e6, 1), orientation="portrait" if h > w else "landscape")
if faces:
    fx, fy, fw = np.median(np.array(faces), axis=0)
    if h > w:
        s = 1080 / w; res["face"] = [int(fx * s), int(fy * s)]
    else:
        cw = h * 9 / 16; x0 = min(max(fx - cw / 2, 0), w - cw); s = 1920 / h
        res["reframe_x"] = int(fx); res["face"] = [int((fx - x0) * s), int(fy * s)]
    res["face_detected_in"] = f"{len(faces)}/6 frames"
else:
    res["face"] = [540, 900]; res["face_detected_in"] = "0/6 — dùng mặc định, kiểm tra contact sheet"
res["contact_sheet"] = os.path.join(work, "contact_sheet.jpg")
json.dump(res, open(os.path.join(work, "probe.json"), "w"), indent=1)
print(json.dumps(res, indent=1, ensure_ascii=False))
