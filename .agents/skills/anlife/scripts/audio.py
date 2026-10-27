#!/usr/bin/env python3
"""Âm thanh: SFX tự đồng bộ theo sfx_events.json + nhạc nền + xử lý giọng + chuẩn loudness.
  python3 audio.py edl.json
Xuất <workdir>/mix_music.m4a (nếu music.mode != none) và <workdir>/mix_nomusic.m4a. Mất 1-3 phút -> chạy nền.
EDL "music": {"mode": "synth" | "file" | "none", "file": "nhac.mp3", "volume": 0.14}
"""
import sys, os, json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt
from scipy.io import wavfile

EDL_PATH = os.path.abspath(sys.argv[1]); BASE = os.path.dirname(EDL_PATH)
EDL = json.load(open(EDL_PATH, encoding="utf-8"))
P = lambda p: p if os.path.isabs(p) else os.path.join(BASE, p)
WORK = P(EDL.get("workdir", ".")); SRC = P(EDL["source"])
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC],
                           capture_output=True, text=True).stdout) + 0.3
SR = 44100
rng = np.random.default_rng(7)

def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-np.maximum(t - a, 0) / d)

def whoosh(dur=0.5):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # băng thông quét 300 -> 3500 Hz theo từng khúc nhỏ
    blocks = 40
    for b in range(blocks):
        s, e = b * n // blocks, (b + 1) * n // blocks
        f = 300 * (3500 / 300) ** (b / blocks)
        sos = butter(2, [f * 0.6, min(f * 1.6, 18000)], "bandpass", fs=SR, output="sos")
        seg = sosfilt(sos, noise[max(0, s - 2000):e])[-(e - s):]
        out[s:e] = seg
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t ** 0.7) ** 2
    out *= env
    return out / (np.abs(out).max() + 1e-9)

def pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 950 * np.exp(-t * 30) + 380
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env_ad(n, 0.002, 0.025)

def ding():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1318.5 * t) + 0.6 * np.sin(2 * np.pi * 1975.5 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t))
    return s * env_ad(n, 0.003, 0.35) / 1.8

def place(track, clip, t, gain):
    i = int(t * SR)
    j = min(len(track), i + len(clip))
    if i < len(track): track[i:j] += clip[:j - i] * gain


def place(track, clip, t, gain):
    i = int(t * SR); j = min(len(track), i + len(clip))
    if 0 <= i < len(track): track[i:j] += clip[:j - i] * gain

def wav(name, x):
    wavfile.write(name, SR, (np.clip(x, -1, 1) * 32767 * 0.9).astype(np.int16))

# ---------- SFX ----------
ev = json.load(open(os.path.join(WORK, "sfx_events.json")))
sfx = np.zeros(int(DUR * SR))
CLIPS = {"whoosh": (whoosh(), 0.30), "pop": (pop(), 0.22), "ding": (ding(), 0.16)}
lvl = EDL.get("sfx_level", 1.0)
for e in ev:
    c, g = CLIPS.get(e["type"], CLIPS["pop"]); place(sfx, c, e["t"], g * lvl)
wav(os.path.join(WORK, "sfx.wav"), sfx / max(1, np.abs(sfx).max()))
print(f"sfx: {len(ev)} events", flush=True)

MUS = EDL.get("music", {"mode": "synth"})
mode = MUS.get("mode", "synth")
music_path = os.path.join(WORK, "music.wav")
if mode == "synth":
    # ---------- Nhạc nền pad (ấm, chậm, không giai điệu nổi) ----------
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    chords = [[53, 57, 60, 64], [55, 59, 62, 67], [52, 55, 59, 62], [57, 60, 64, 67]]  # Fmaj7 G Em7 Am7
    bars = 4.0
    n = int(DUR * SR)
    t = np.arange(n) / SR
    pad = np.zeros(n)
    for k in range(int(DUR / bars) + 1):
        ch = chords[k % 4]
        s0, s1 = int(k * bars * SR), int(min((k + 1) * bars + 1.2, DUR) * SR)
        if s0 >= n: break
        tt = t[s0:s1] - k * bars
        env = np.minimum(tt / 1.0, 1) * np.clip((bars + 1.2 - tt) / 1.2, 0, 1)
        for m in ch:
            f = note(m)
            for det in (1.0, 1.004, 0.996):
                pad[s0:s1] += env * (np.sin(2 * np.pi * f * det * tt) + 0.25 * np.sin(4 * np.pi * f * det * tt)) / 12
        # bass nhẹ
        pad[s0:s1] += env * 0.35 * np.sin(2 * np.pi * note(ch[0] - 12) * tt)
    # arp mềm (nốt 8, nhỏ)
    step = 0.375
    for i in range(int(DUR / step)):
        ch = chords[int(i * step / bars) % 4]
        m = ch[[0, 2, 1, 3, 2, 1][i % 6]] + 12
        s0 = int(i * step * SR); nn = int(0.6 * SR)
        if s0 + nn > n: break
        tt = np.arange(nn) / SR
        pad[s0:s0 + nn] += 0.12 * np.sin(2 * np.pi * note(m) * tt) * env_ad(nn, 0.005, 0.18)
    pad = sosfiltfilt(butter(2, 2200, "low", fs=SR, output="sos"), pad)
    # nhịp "thở" nhẹ
    pad *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 8)
    fade = np.minimum(t / 1.5, 1) * np.clip((DUR - t) / 2.5, 0, 1)
    pad = pad * fade
    pad /= np.abs(pad).max()

    wav(music_path, pad)
elif mode == "file":
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", P(MUS["file"]), "-t", f"{DUR:.2f}",
                    "-af", f"afade=t=in:d=1.5,afade=t=out:st={DUR - 3:.2f}:d=3", "-ar", str(SR), "-ac", "1", music_path], check=True)

VO = EDL.get("voice_chain", "highpass=f=80,afftdn=nf=-30,equalizer=f=3000:t=q:w=1:g=2,equalizer=f=250:t=q:w=1:g=-1.5,"
                            "acompressor=threshold=-20dB:ratio=3:attack=5:release=100:makeup=2")
LN = "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000"
if mode != "none":
    vol = MUS.get("volume", 0.14)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", music_path, "-i", os.path.join(WORK, "sfx.wav"), "-filter_complex",
        f"[0:a]{VO},asplit=2[v][vsc];[1:a]volume={vol}[m];[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
        f"[2:a]volume=0.9[s];[v][md][s]amix=inputs=3:normalize=0:duration=first,{LN}[out]",
        "-map", "[out]", "-c:a", "aac", "-b:a", "192k", os.path.join(WORK, "mix_music.m4a")], check=True)
    print("mix_music.m4a ok", flush=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", os.path.join(WORK, "sfx.wav"), "-filter_complex",
    f"[0:a]{VO}[v];[1:a]volume=0.9[s];[v][s]amix=inputs=2:normalize=0:duration=first,{LN}[out]",
    "-map", "[out]", "-c:a", "aac", "-b:a", "192k", os.path.join(WORK, "mix_nomusic.m4a")], check=True)
print("DONE audio", flush=True)
