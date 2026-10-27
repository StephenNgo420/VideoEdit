#!/usr/bin/env python3
"""Transcribe có timestamp từng từ bằng faster-whisper (CPU).
  python3 transcribe.py <video> <workdir> [--lang vi] [--model large-v3-turbo] [--prompt "Mạnh Thành, ..."]
Ghi <workdir>/transcript.json và transcript.txt (mỗi dòng: start-end text). ~1x thời lượng video trên 1 CPU -> chạy nền."""
import sys, os, json, time, argparse, subprocess
ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("workdir")
ap.add_argument("--lang", default="vi"); ap.add_argument("--model", default="large-v3-turbo")
ap.add_argument("--prompt", default="")
a = ap.parse_args()
os.makedirs(a.workdir, exist_ok=True)
wav = os.path.join(a.workdir, "audio16k.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
from faster_whisper import WhisperModel
t = time.time()
m = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 1)
segs, info = m.transcribe(wav, language=a.lang, word_timestamps=True, beam_size=1, vad_filter=False,
                          initial_prompt=a.prompt or None)
out, lines = [], []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 2)} for w in s.words]})
    lines.append(f"{s.start:7.2f}-{s.end:7.2f} {s.text.strip()}")
    print(lines[-1], flush=True)
json.dump(out, open(os.path.join(a.workdir, "transcript.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(a.workdir, "transcript.txt"), "w").write("\n".join(lines))
# danh sách từ kèm timestamp + từ độ tin cậy thấp để rà lỗi
wl = [" ".join(f"{w['w'].strip()}@{w['s']:.2f}" for w in s["words"]) for s in out]
open(os.path.join(a.workdir, "words.txt"), "w").write("\n".join(wl))
low = [f"{w['s']:.2f} {w['w'].strip()} (p={w['p']})" for s in out for w in s["words"] if w["p"] < 0.5]
open(os.path.join(a.workdir, "low_confidence.txt"), "w").write("\n".join(low))
print(f"DONE {len(out)} segments, {sum(len(s['words']) for s in out)} words in {time.time() - t:.0f}s; low-confidence: {len(low)}", flush=True)
