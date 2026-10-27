#!/usr/bin/env python3
"""Ghép video_only.mp4 + audio -> /mnt/user-data/outputs, kèm sheet kiểm tra.
  python3 finalize.py edl.json [--out /mnt/user-data/outputs]
Tạo <name>_final.mp4 (có nhạc, nếu có) và <name>_khong-nhac.mp4."""
import sys, os, json, subprocess, argparse
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument("edl"); ap.add_argument("--out", default="/mnt/user-data/outputs")
a = ap.parse_args()
EDL_PATH = os.path.abspath(a.edl); BASE = os.path.dirname(EDL_PATH)
EDL = json.load(open(EDL_PATH, encoding="utf-8"))
P = lambda p: p if os.path.isabs(p) else os.path.join(BASE, p)
WORK = P(EDL.get("workdir", ".")); name = EDL.get("output_name", "video")
os.makedirs(a.out, exist_ok=True)
vid = os.path.join(WORK, "video_only.mp4")
outs = []
for mix, suffix in (("mix_music.m4a", "_final"), ("mix_nomusic.m4a", "_khong-nhac" if os.path.exists(os.path.join(WORK, "mix_music.m4a")) else "_final")):
    mp = os.path.join(WORK, mix)
    if not os.path.exists(mp): continue
    o = os.path.join(a.out, name + suffix + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", mp, "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest",
                    "-movflags", "+faststart", o], check=True)
    outs.append(o)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", outs[0]], capture_output=True, text=True).stdout)
ims = []
for k in range(8):
    t = dur * (k + 0.5) / 8
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", outs[0], "-frames:v", "1", "-vf", "scale=216:384", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    ims.append((t, Image.frombytes("RGB", (216, 384), raw)))
sheet = Image.new("RGB", (216 * 8, 408), "black"); d = ImageDraw.Draw(sheet)
for i, (t, im) in enumerate(ims): sheet.paste(im, (i * 216, 0)); d.text((i * 216 + 6, 388), f"{t:.1f}s", fill="white")
sheet.save(os.path.join(WORK, "final_check.jpg"))
for o in outs: print(o, f"{os.path.getsize(o) / 1e6:.1f}MB")
print("check sheet:", os.path.join(WORK, "final_check.jpg")); print("DONE")
