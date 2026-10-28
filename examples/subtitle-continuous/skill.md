---
name: vietnamese-caption-graphics
description: >-
  Tạo phụ đề tiếng Việt từ video/âm thanh hoặc transcript có thời gian, rà lời,
  chia cụm 5–6 từ, vẽ chữ trắng viền đen không nền; chỉ cụm đầu tiên của video
  pop-up nhẹ. Dùng khi người dùng yêu cầu thêm hoặc chỉnh đồ hoạ phụ đề.
---

# Phụ đề tiếng Việt — chữ trắng viền đen

Tách từ quy trình transcribe và render captions của Anlife. Tệp này chứa hướng
 dẫn và mã Python đủ để tạo phụ đề, không phụ thuộc engine đồ hoạ của Anlife.
Chỉ chuẩn bị, nhận dạng, rà lời, chia cụm, vẽ và ghép phụ đề vào video.
Giữ nguyên nội dung, khung hình và âm thanh nguồn khi chỉ được yêu cầu thêm sub.

## Thiết kế mặc định

- Chữ trắng `#FFFFFF`, viền đen `#000000`, font đậm có đủ dấu tiếng Việt.
- Không hộp nền, nền highlight, màu từ đang nói, bóng đổ hoặc hiệu ứng nền.
- Mỗi cụm 5–6 từ cách nhau bằng khoảng trắng; cả cụm hiện đồng thời. Không karaoke.
  Với tiếng Việt, đây là đơn vị hiển thị theo khoảng trắng, không phải tách từ ngôn ngữ học.
- Chỉ cụm phụ đề đầu tiên theo thời gian có pop-up: 94% → 102% → 100% trong
  180 ms. Nếu lời nói bắt đầu ở giây 5, pop bắt đầu ở giây 5, không phải giây 0.
- Tất cả cụm sau thay trực tiếp cụm trước, không pop, zoom, fade hay chuyển động.
- Khoảng cách giữa mọi hai cụm liên tiếp bằng **0 giây**: giữ cụm trước cho đến
  đúng thời điểm cụm kế tiếp bắt đầu; không có frame trống, không chồng chữ.
- Khung 1080×1920: cỡ chữ mục tiêu 68 px, viền 4 px, căn giữa ngang, đáy chữ cách
  đáy video 20% chiều cao. Scale các thông số theo chiều cao video thực tế.
  Co chữ khi dài; nếu cần xuống 2 dòng trong cùng một cụm, không tách thành cụm ngắn.
- Chừa lề ngang 7,5% và đủ chỗ cho scale 102%. Kiểm tra preview trên video thật
  để tránh che mặt, nội dung quan trọng và giao diện mạng xã hội.

## 1. Chuẩn bị môi trường

Dùng checkout hiện tại; không tạo Git worktree nếu người dùng chưa yêu cầu.
Kiểm tra tool/dependency đã có, cài phần thiếu. Chạy job dài và theo dõi đến khi hoàn tất.
Không yêu cầu người dùng tự gõ lệnh setup thông thường khi có môi trường thực thi.

Cần Python 3.12, FFmpeg/ffprobe với filter `ass` (libass), encoder libx264 và
Pillow để đo chữ. Faster-whisper/PyAV chỉ cần khi phải nhận dạng lời nói.
Dùng font TTF/OTF hỗ trợ tiếng Việt; giữ giấy phép nếu phân phối font.
Font không nhúng trong file Markdown này. Có thể dùng InterDisplay-ExtraBold.ttf
của Anlife hoặc font đậm hỗ trợ tiếng Việt có sẵn trên máy.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pillow==13.0.0
# Chỉ cài khi cần nhận dạng lời nói:
python -m pip install faster-whisper==1.2.1 av==16.0.1
ffmpeg -hide_banner -filters 2>/dev/null | rg ' ass '
```

Trong repo VideoEdit đã setup: dùng `source scripts/activate.sh` để tái sử dụng venv.
Mỗi shell mới cần activate lại. Không commit venv, model/cache, media hoặc API key.
Model Whisper mặc định `large-v3-turbo`, CPU int8; tải lần đầu khoảng 1,6 GB.
Nếu proxy báo `403 CONNECT`, cần cho phép `huggingface.co`, `*.huggingface.co`,
`*.hf.co` trong cấu hình mạng, áp dụng rồi thử lại. Không tắt TLS/checksum.
Không cần API key cho model công khai hoặc cho đồ hoạ phụ đề.

## 2. Nhận dạng và rà lời

Nếu đã có transcript đáng tin cậy kèm thời gian, dùng lại; không nghe lại chỉ vì đổi style.
Nếu chưa có, lưu đoạn sau thành `transcribe.py`, rồi chạy:
`python transcribe.py source.mp4 work --prompt "Tên riêng, thuật ngữ"`.
Có thể truyền `--model /path/to/local/model` để dùng model CTranslate2 sẵn có.

```python
import argparse, json, os, subprocess
from pathlib import Path
from faster_whisper import WhisperModel
p = argparse.ArgumentParser()
p.add_argument('source'); p.add_argument('work')
p.add_argument('--model', default='large-v3-turbo')
p.add_argument('--prompt', default='')
a = p.parse_args()
w = Path(a.work); w.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.source, '-vn',
                '-ac', '1', '-ar', '16000', str(w/'audio16k.wav')], check=True)
model = WhisperModel(a.model, device='cpu', compute_type='int8',
                     cpu_threads=min(4, os.cpu_count() or 1))
segments, _ = model.transcribe(str(w/'audio16k.wav'), language='vi',
    word_timestamps=True, beam_size=1, vad_filter=True,
    initial_prompt=a.prompt or None)
result = [{'start': s.start, 'end': s.end, 'text': s.text.strip(),
           'words': [{'w': v.word.strip(), 's': round(v.start, 3),
                      'e': round(v.end, 3), 'p': round(v.probability, 2)}
                     for v in (s.words or [])]} for s in segments]
(w/'transcript.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
(w/'transcript.txt').write_text('\n'.join(s['text'] for s in result), encoding='utf-8')
(w/'low_confidence.txt').write_text('\n'.join(
    f"{v['s']:.2f} {v['w']} (p={v['p']})" for s in result for v in s['words']
    if v['p'] < 0.5), encoding='utf-8')
print('DONE', len(result), 'segments')
```

Đọc transcript, kiểm tra các từ thiếu chắc chắn, tên riêng và dấu tiếng Việt bằng
âm thanh gốc. Không tự đoán rồi báo là chính xác. Whisper có thể sinh chữ trên
đầu vào không có lời nói; phải bỏ nội dung đó sau khi nghe kiểm tra.

## 3. Chia thành cụm có thời gian

Tạo `chunks.json`: danh sách `{start, end, text}` theo thời gian video nguồn.
Đọc timestamp của từng từ từ transcript để đặt start/end, không chia thời gian
đều cho lời nói thật. Mỗi từ xuất hiện đúng một lần, đúng thứ tự, không bỏ hoặc
thêm từ chỉ để đủ số lượng.

Ưu tiên cụm 6 từ; chọn 5 từ để giữ ý hoặc tránh đuôi quá ngắn. Không tự cắt cụm
ngay khi gặp dấu phẩy hay hết segment Whisper nếu vẫn có thể ghép lời liên tục.
Chọn lại các điểm chia lân cận để tránh cụm cuối 1–4 từ. Không ghép nội dung
không liên quan chỉ để đủ số từ. Khi có khoảng nghỉ giữa hai cụm, giữ nguyên
cụm trước đến lúc cụm mới bắt đầu theo chế độ không khoảng trống bên dưới.
Nếu một đoạn lời tự nhiên không thể chia toàn bộ thành 5–6 từ, giữ đúng lời và
thời gian, ghi `short_reason` cho ngoại lệ 1–4 từ; báo rõ ngoại lệ khi giao file.
Tối đa 6 từ/cụm. Không thêm chữ đệm. Chấm câu giữ nguyên khi đúng với lời nói.

Thời gian không âm, end > start, không chồng nhau. Giữ start theo timestamp từ
đầu của từng cụm; **end của cụm i = start của cụm i+1**. Cụm trước còn trên màn
hình đến đúng lúc cụm sau thay thế, kể cả khi lời nói có khoảng nghỉ. Không đẩy
cụm sau lên sớm, không sửa tốc độ hoặc cắt âm thanh để lấp khoảng trống.
Cụm cuối giữ end đã rà theo lời nói. Khoảng trước cụm đầu và sau cụm cuối không
phải khoảng cách giữa các cụm; không tự đưa chữ lên trước khi bắt đầu lời nói.
Nếu muốn ẩn sub trong đoạn nghỉ dài hoặc chuyển cảnh, người dùng cần yêu cầu
ngoại lệ; mặc định của skill này là liên tục từ cụm đầu đến cụm cuối.

Mã xuất bên dưới tự chuẩn hoá end theo start kế tiếp, kể cả khi chunks.json đầu
vào còn gap. ASS và SRT dùng chung ranh giới đã chuẩn hoá để khoảng cách bằng 0
sau khi làm tròn timestamp. Kiểm tra từng frame quanh điểm chuyển, không chỉ đọc
thời gian trong JSON.

Ví dụ minh hoạ có timing chủ động (không phải kết quả Whisper):

```json
[
  {"start": 0.6, "end": 3.2, "text": "Hôm nay mình thử phụ đề"},
  {"start": 3.2, "end": 5.8, "text": "Chữ trắng viền đen rõ nét"},
  {"start": 5.8, "end": 8.4, "text": "Cụm đầu bật lên thật nhẹ"},
  {"start": 8.4, "end": 10.8, "text": "Các cụm sau giữ yên"}
]
```

## 4. Tạo đồ hoạ ASS và SRT

Lưu mã dưới đây thành `make_captions.py`. Đặt `FONT` là đường dẫn tuyệt đối tới
file font thật. Đọc width/height của video bằng ffprobe; truyền đúng kích thước
vào script, không tự crop hay kéo giãn video chỉ để thêm phụ đề.

```bash
FONT=/path/to/InterDisplay-ExtraBold.ttf
python make_captions.py chunks.json --font "$FONT" --width 1080 --height 1920 --out captions
```

ASS giữ đầy đủ thiết kế và animation; SRT chỉ giữ chữ và thời gian, không giữ style.
Mã dùng BorderStyle=1, Shadow=0 và chỉ vẽ viền chữ; không có khối nền phụ đề.
Chỉ event đầu tiên có tag transform. Cả cụm được scale cùng lúc, không scale riêng từng từ.

```python
"""Build ASS/SRT from explicitly reviewed, timed 5–6-word caption groups."""
import argparse
import json
import math
from pathlib import Path
from PIL import ImageFont


def stamp(seconds, ass=False):
    factor = 100 if ass else 1000
    n = round(seconds * factor)
    h, n = divmod(n, 3600 * factor)
    m, n = divmod(n, 60 * factor)
    s, fraction = divmod(n, factor)
    return (f'{h}:{m:02}:{s:02}.{fraction:02}' if ass else
            f'{h:02}:{m:02}:{s:02},{fraction:03}')


def ass_text(text):
    # Fullwidth substitutes prevent input text from injecting ASS override tags.
    return text.replace('\\', '＼').replace('{', '｛').replace('}', '｝')


def build(source, font_path, width, height, output):
    chunks = json.loads(Path(source).read_text(encoding='utf-8'))
    if not isinstance(chunks, list) or not chunks:
        raise ValueError('Expected a nonempty list of caption groups')
    previous_end = 0.0
    for i, c in enumerate(chunks):
        start, end = float(c['start']), float(c['end'])
        text = ' '.join(c['text'].split())
        count = len(text.split())
        if not (math.isfinite(start) and math.isfinite(end)
                and 0 <= start < end and start >= previous_end):
            raise ValueError(f'Invalid/overlapping timing in group {i + 1}')
        if count not in (5, 6) and not c.get('short_reason'):
            raise ValueError(f'Group {i + 1}: expected 5–6 space-separated words; '
                             'document an unavoidable exception using short_reason')
        if not 1 <= count <= 6:
            raise ValueError(f'Group {i + 1}: empty or exceeds 6 words')
        c.update(start=start, end=end, text=text)
        previous_end = end

    # Hold the current group until the next one starts: no blank interval.
    # Preserve starts (speech sync) and the reviewed end of the final group.
    for i in range(len(chunks) - 1):
        chunks[i]['end'] = chunks[i + 1]['start']

    font_path = Path(font_path).resolve()
    family, face = ImageFont.truetype(str(font_path), 64).getname()
    if face.lower() != 'regular' and not family.lower().endswith(face.lower()):
        family = f'{family} {face}'
    if any(x in family for x in ',\n\r'):
        raise ValueError('Unsupported font family name')
    base_size = max(1, round(68 * height / 1920))
    minimum_size = max(1, round(48 * height / 1920))
    outline = max(1, round(4 * height / 1920))
    margin_x = round(width * 0.075)
    margin_v = round(height * 0.20)
    max_width = width * 0.85 / 1.02  # leave room for first pop's 102% scale
    header = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{family},{base_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,{outline},0,2,{margin_x},{margin_x},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events, srt = [], []
    for i, c in enumerate(chunks):
        words = c['text'].split()
        lines = [c['text']]
        size = base_size
        while size > minimum_size:
            font = ImageFont.truetype(str(font_path), size)
            if font.getlength(lines[0]) + outline * 2 <= max_width:
                break
            size -= 1
        font = ImageFont.truetype(str(font_path), size)
        if font.getlength(lines[0]) + outline * 2 > max_width:
            split = min(range(1, len(words)), key=lambda k:
                        max(font.getlength(' '.join(words[:k])),
                            font.getlength(' '.join(words[k:])))) if len(words) > 1 else 1
            lines = [' '.join(words[:split]), ' '.join(words[split:])]
            lines = [line for line in lines if line]
        if any(font.getlength(line) + outline * 2 > max_width for line in lines):
            raise ValueError(f'Group {i + 1} too wide: review font/layout manually')
        tags = f'\\fs{size}'
        if i == 0:
            # Only the first chronological caption group animates. No fade/shadow/box.
            ms = min(180, round((c['end'] - c['start']) * 1000))
            mid = max(1, round(ms * 0.56))
            tags += (f'\\fscx94\\fscy94\\t(0,{mid},\\fscx102\\fscy102)'
                     f'\\t({mid},{ms},\\fscx100\\fscy100)')
        text = r'\N'.join(ass_text(line) for line in lines)
        events.append(f'Dialogue: 0,{stamp(c["start"], True)},{stamp(c["end"], True)},'
                      f'Default,,0,0,0,,{{{tags}}}{text}')
        srt.append(f'{i + 1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n'
                   + '\n'.join(lines))
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.with_suffix('.ass').write_text(header + '\n'.join(events) + '\n', encoding='utf-8')
    target.with_suffix('.srt').write_text('\n\n'.join(srt) + '\n', encoding='utf-8')
    print(f'Wrote {len(chunks)} caption groups: {target.with_suffix(".ass")} / .srt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('chunks', help='Reviewed JSON groups with start/end/text')
    parser.add_argument('--font', required=True, help='Path to Vietnamese-capable TTF/OTF')
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--height', type=int, default=1920)
    parser.add_argument('--out', default='captions')
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0:
        parser.error('Frame dimensions must be positive')
    build(args.chunks, args.font, args.width, args.height, args.out)

```

## 5. Preview, render và kiểm tra

Trong các lệnh dưới, chạy tại thư mục chứa `captions.ass`. Cho libass biết thư
mục font thực tế bằng `fontsdir`. Với path chứa dấu nháy, dấu hai chấm hoặc ký tự
filter đặc biệt, dùng thư mục làm việc/path đơn giản hoặc escape theo cú pháp FFmpeg.
Kiểm tra log fontselect để bảo đảm font mong muốn được nạp.

```bash
# Thay /path/to/fonts bằng thư mục chứa font được chọn.
ffmpeg -y -i source.mp4 -vf "ass=filename=captions.ass:fontsdir=/path/to/fonts" \
  -map 0:v:0 -map '0:a?' -c:v libx264 -preset medium -crf 18 \
  -c:a copy -movflags +faststart captioned.mp4
```

Nếu codec audio nguồn không phù hợp MP4, dùng `-c:a aac -b:a 192k` thay cho copy.
Không thêm nhạc, SFX, logo, màu brand, zoom, làm mịn da hoặc cảnh minh hoạ trong
workflow chỉ thêm phụ đề này. Không thêm pop/fade cho các cụm sau.

Trước bản đầy đủ, xuất clip hoặc ảnh preview trong cùng pipeline ASS. Kiểm tra:
- Cụm đầu: frame đầu, giữa pop (~0,10s), sau pop (~0,20s).
- Cụm thứ 2 trở đi: ngay frame đầu và sau 0,20s; chữ phải đứng yên, không fade.
- Mọi cặp liên tiếp: end trước = start sau trong ASS lẫn SRT; xem frame ngay
  trước, đúng lúc và ngay sau điểm chuyển để xác nhận không có frame trống.
  Quét toàn đoạn từ cụm đầu đến cuối; không chồng hai cụm tại điểm chuyển.
- Chữ trắng viền đen, đủ dấu, không nền/box/highlight/shadow, không tràn khung.
- Mỗi cụm 5–6 từ hoặc có ngoại lệ được giải thích. Toàn cụm hiện đồng thời.
- Đồng bộ lời nói thật khi có nguồn giọng nói; video giả không chứng minh độ chính xác ASR.

Kiểm tra thời lượng, kích thước và codec bằng ffprobe, rồi giải mã đầy đủ:

```bash
ffprobe -v error -show_streams -show_format -of json captioned.mp4
ffmpeg -v error -xerror -i captioned.mp4 -f null -
```

Giao video đã burn-in phụ đề, ASS giữ style và SRT nếu người dùng cần chỉnh tiếp.
Báo rõ phần đã kiểm chứng, từ còn nghi ngờ và ngoại lệ số từ. File demo dùng nền
video minh hoạ và timing giả phải được ghi rõ, không gọi là bài thử nhận dạng giọng nói.
Đổi thiết kế chỉ cần tạo lại ASS và render, không cần transcribe lại.
