"""Exercise real probe, graphics, captions, render, audio and mux without API/model.

Run after sourcing scripts/activate.sh. Outputs stay in ignored video-work/.
This checks the editing pipeline, not speech recognition accuracy.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / '.agents/skills/anlife/scripts'
base = ROOT / 'video-work'
base.mkdir(exist_ok=True)
work = Path(tempfile.mkdtemp(prefix='smoke-', dir=base))
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')


def run(*args):
    subprocess.run([str(x) for x in args], check=True, cwd=ROOT)


def script(name, *args):
    run(sys.executable, SK / name, *args)


run('ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
    'testsrc2=size=360x640:rate=30:duration=4', '-f', 'lavfi', '-i',
    'sine=frequency=440:sample_rate=48000:duration=4', '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', work / 'source.mp4')
transcript = [{'start': 0.2, 'end': 1.7, 'text': 'Kiểm tra tiếng Việt',
               'words': [{'w': w, 's': 0.2 + i * 0.35, 'e': 0.55 + i * 0.35, 'p': 1.0}
                         for i, w in enumerate(['Kiểm', 'tra', 'tiếng', 'Việt'])]}]
(work / 'transcript.json').write_text(json.dumps(transcript, ensure_ascii=False))
edl = {'source': 'source.mp4', 'workdir': '.', 'output_name': 'smoke',
       'grade': 'natural', 'skin_smooth': 0.35, 'duration': 4,
       'captions': {'enabled': True}, 'shots': [[0, 4, 1.0, 1.05]],
       'scenes': [{'type': 'chapter', 't0': 2, 't1': 3.5,
                   'num': '01', 'name': 'TIẾNG VIỆT', 'tag': 'Kiểm tra font'}],
       'overlays': [], 'music': {'mode': 'synth', 'volume': 0.1}}
edl_path = work / 'edl.json'
edl_path.write_text(json.dumps(edl, ensure_ascii=False))
script('probe.py', work / 'source.mp4', work)
script('render.py', edl_path, 'stills', 0.7, 2.7)
script('render.py', edl_path, 'render')
script('audio.py', edl_path)
script('finalize.py', edl_path, '--out', work / 'outputs')
for suffix in ['_final', '_khong-nhac']:
    output = work / 'outputs' / f'smoke{suffix}.mp4'
    info = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-count_frames', '-show_streams',
        '-show_format', '-of', 'json', str(output)]))
    v = next(s for s in info['streams'] if s['codec_type'] == 'video')
    a = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    assert (v['width'], v['height']) == (1080, 1920), v
    assert v['codec_name'] == 'h264' and a['codec_name'] == 'aac'
    assert int(v['nb_read_frames']) == 120, v
    assert 3.9 <= float(info['format']['duration']) <= 4.2, info['format']
    run('ffmpeg', '-v', 'error', '-xerror', '-i', output, '-f', 'null', '-')
assert (work / 'stills/sheet_0.jpg').is_file()
assert (work / 'final_check.jpg').is_file()
assert json.loads((work / 'sfx_events.json').read_text())
print(f'PASS: 2 decoded H.264/AAC exports, 1080x1920, 120 frames each; {work}')
