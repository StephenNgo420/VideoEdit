# EDL schema

EDL = 1 file JSON mô tả toàn bộ bản dựng. Đường dẫn tương đối tính từ thư mục chứa file EDL. Thời gian tính bằng giây theo
video nguồn (không cắt/nối). Toạ độ theo khung đầu ra 1080×1920.

## Mục lục
1. Trường gốc
2. captions
3. shots / punches / chapters
4. scenes (graphic: brand_reveal, cards_grid, rows_x, chapter, checklist, versus, summary, statement — video: broll, image)
5. overlays (question_card, title_box, meter, x_list, check_list, callout, chips, warning, cta, lower_third, badge)
6. music / sfx
7. Icon

## 1. Trường gốc

| Trường | Kiểu | Mặc định | Ghi chú |
|---|---|---|---|
| `source` | path | — | video gốc (đã cắt lặng / ờ à nếu người dùng làm sẵn) |
| `workdir` | path | `.` | nơi ghi transcript, broll, stills, video_only.mp4 |
| `transcript` | path | `<workdir>/transcript.json` | |
| `output_name` | str | `video` | tên file đầu ra (không dấu, gạch nối) |
| `grade` | str | `natural` | `natural` (giữ nguyên màu gốc — mặc định) / `neutral` / `bright` / `warm_clean` (da ấm/vàng, chỉ khi được yêu cầu) / `none` / chuỗi filter ffmpeg |
| `skin_smooth` | float | 0.35 | mức làm mịn da (chỉ vùng da, không đổi màu). 0 = tắt, 0.35 nhẹ, 0.5–0.6 vừa, tối đa 0.7 |
| `face` | [x,y] | [540,950] | tâm zoom & tâm cắt người nói (từ probe.json) |
| `reframe_x` | int | giữa | chỉ khi nguồn ngang: x của mặt trong nguồn để cắt 9:16 |
| `progress_bar` | bool | true | thanh tiến trình đỏ trên cùng |
| `duration` | float | độ dài nguồn | cắt bớt đuôi nếu cần |
| `voice_chain` | str | lọc ồn+EQ+nén | chuỗi filter ffmpeg cho giọng |

## 2. captions

```json
"captions": {
  "enabled": true, "y": 1475, "size": 70, "max_words": 3, "max_chars": 17,
  "exclude": [[0, 6.4]],
  "fixes": {"Cloth": "Claude", "Haku": "Haiku"},
  "merges": [["code", "bay", "codebase"]],
  "word_overrides": [{"t": 105.80, "w": "tác"}],
  "keywords": ["Claude", "Sonnet"]
}
```
- `fixes`: thay theo token (giữ dấu câu đi kèm). Không phân biệt vị trí → chỉ dùng cho lỗi lặp lại toàn video.
- `word_overrides`: thay 1 từ tại đúng thời điểm (±0.06s) — dùng cho lỗi đơn lẻ.
- `merges`: gộp 2 token liền nhau. Số kiểu "4" + ".5" tự gộp thành "4.5".
- `keywords`: luôn tô màu brand đậm trong phụ đề. Từ đang nói luôn có nền màu brand.
- Phụ đề tự ẩn trong scene graphic; hiện trong B-roll (tắt bằng `"captions": false` trong scene).

## 3. shots / punches / chapters

```json
"shots":   [[t0, t1, scale_start, scale_end], ...],   // zoom quanh `face`, scale ≥ 1.0; ngoài shot = 1.0
"punches": [[t, factor], ...],                          // nhân thêm factor (1.08–1.13) từ t tới hết shot chứa nó, ease 0.18s
"chapters":[[t0, t1, "01 · TÊN PHẦN"], ...]             // pill đỏ góc trên trái, hiện khi thấy người nói
```

## 4. scenes

Mọi scene có `type`, `t0`, `t1`. Scene graphic phủ full màn hình (nền brand, logo ở trên). Whoosh tự thêm tại `t0-0.15`.
Phần tử bên trong có `t` riêng — thời điểm bật ra (nên = lúc nói từ đó).

**brand_reveal** — giới thiệu sản phẩm/đối tác: logo đối tác trên thẻ trắng + tên sản phẩm + pill.
```json
{"type":"brand_reveal","t0":36.75,"t1":39.8,"small":"Giải pháp","logo":"/abs/path/partner-logo.png","logo_t":37.56,
 "title":"Cyber Protect Cloud","title_t":38.14,"tag":"Tích hợp trên 1 nền tảng","tag_t":39.0,"icon":"check","bg":"light"}
```
Logo đối tác: PNG nền trong suốt (tự cắt viền trống), dùng đường dẫn tuyệt đối và chỉ thêm khi người dùng yêu cầu. Không có logo thương hiệu mặc định ở đầu khung.

**cards_grid** — tối đa 4 thẻ 2×2, thẻ mờ nét đứt hiện trước rồi "bật" đúng lúc gọi tên.
```json
{"type":"cards_grid","t0":20,"t1":25.9,"small":"Claude hiện có","title":"4 model nổi bật","highlight":"4",
 "level_label":"Sức mạnh",
 "cards":[{"num":"01","name":"Haiku","ver":"4.5","tag":"Nhanh nhất","level":1,"t":23.24}, ...]}
```
`level` 1–4 vẽ thang 4 ô (bỏ nếu không cần). Tên ≤ 8 ký tự đẹp nhất.

**rows_x** — 2–3 hàng lớn (sai lầm, vấn đề, trường hợp).
```json
{"type":"rows_x","t0":..,"t1":..,"small":"..","title":"2 kiểu chọn sai","highlight":"2",
 "rows":[{"title":"Model quá mạnh","sub":"cho việc đơn giản","tag":"Lãng phí","icon":"x","t":31.76}]}
```

**chapter** — nền đỏ full, số lớn mờ + tên + pill.
```json
{"type":"chapter","t0":37.05,"t1":39.9,"num":"01","name":"HAIKU 4.5","tag":"Nhanh nhất","icon":"bolt"}
```

**checklist** — tối đa 5 mục có icon (mặc định check).
```json
{"type":"checklist","t0":..,"t1":..,"small":"Haiku 4.5 phù hợp với","title":"Việc lặp lại","highlight":"lặp lại","icon":"check",
 "items":[{"text":"Viết email","t":46.8,"sub":"(tuỳ chọn dòng phụ)","icon":"x"}]}
```

**versus** — 2 thẻ lớn trên/dưới + vòng VS.
```json
{"type":"versus","t0":..,"t1":..,"small":"So sánh nhanh","title":"Sonnet vs Opus 5","highlight":"vs",
 "a":{"name":"SONNET","role":"Nhân sự đa năng","icon":"person","t":83.1,"t_role":84.06,"connector":"giống như"},
 "b":{"name":"OPUS 5","role":"Kỹ sư giải pháp","icon":"gear","t":84.9,"t_role":86.58},"vs_t":84.7}
```

**summary** — bảng tóm tắt (tên | mô tả) + pill CTA (có ding).
```json
{"type":"summary","t0":..,"t1":..,"title":"Lưu lại để chọn đúng","highlight":"chọn đúng","icon":"bookmark","t_rows":117.05,
 "rows":[{"name":"Haiku 4.5","desc":"Việc nhanh, lặp lại"}],"cta_text":"LƯU VIDEO NGAY","cta_t":118.5}
```

**statement** — câu chốt lớn giữa màn hình.
```json
{"type":"statement","t0":..,"t1":..,"small":"Bài học","text":"Chọn model theo bài toán, không theo độ mạnh","size":84,
 "highlight":"đừng quên!","highlight_t":..,"bg":"light|red"}
```

**broll** — video trám.
```json
{"type":"broll","t0":26.0,"t1":30.7,"layout":"full|split",
 "query":["confused man looking at laptop","thinking person computer screen"],  // fetch_broll.py dùng
 "clip":"broll/pexels_123.mp4",       // fetch_broll.py tự điền; hoặc đặt clip người dùng upload
 "pick":0, "start":0.0,                // chọn ứng viên thứ mấy; giây bắt đầu trong clip
 "headline":"Chưa hiểu sự khác nhau?","headline_highlight":"khác nhau","headline_y":380,
 "kenburns":true, "captions":true, "speaker_face_y":330}
```
- `full`: clip phủ toàn màn, lớp tối phía trên nếu có headline, phụ đề giữ nguyên vị trí.
- `split`: clip ở nửa trên (1080×960), người nói ở nửa dưới (mặt đặt ở `speaker_face_y` trong nửa dưới), phụ đề nằm ngay
  đường chia. Hợp cho đoạn nói dài vẫn muốn giữ mặt. Overlay/pill ẩn trong split.
- Clip ngắn hơn scene tự lặp. Clip được chuẩn hoá (cắt khung, 30fps) và cache trong `workdir/broll/prep_*.mp4`.

**image** — ảnh tĩnh có Ken Burns (zoom/pan chậm), cùng các trường `layout`, `headline*`, `captions` như broll:
```json
{"type":"image","t0":..,"t1":..,"src":"broll/photo.jpg","query":"...","zoom":"in|out","pan":"right|left"}
```

## 5. overlays

Hiện trên cảnh người nói (ẩn khi đang ở scene full/split). Chung: `t0`, `t1` (bỏ `t1` = giữ tới hết video), `y` (mép trên,
mặc định 300). `t0: -1` = hiện sẵn từ khung đầu (không animation).

| type | trường | dùng khi |
|---|---|---|
| `question_card` | `label`, `sub`, `text`, `y`=250 | hook dạng câu hỏi khán giả / bình luận |
| `title_box` | `line1`, `highlight`, `script_line`, `badge`, `y`=1440 (tâm) | tiêu đề hook khung nét đứt |
| `meter` | `title`, `bars: [[nhãn, 0-1, "red"|"gray"], ...]` | đánh đổi, so mức độ |
| `x_list` / `check_list` | `title`, `items: [[text, t], ...]` | nên/không nên |
| `callout` | `title`, `prefix`, `strong`, `strong_t`, `stamp: {text, t}` | lời khuyên, câu chốt, "khuyên dùng" |
| `chips` | `title`, `chips: [[text, t], ...]`, `note: {text, strong, t}` | đặc điểm ngắn |
| `warning` | `label`, `text` | lưu ý, rủi ro (icon vàng) |
| `cta` | `headline`, `checks: [...]`, `contact` (mặc định `[SĐT : 0377.526.213]` từ config), `pill: {text, t}`, `partner_logo` (tuỳ chọn, chỉ khi được yêu cầu), `y`=260 | kêu gọi cuối video; mỗi check ≤ 26 ký tự |
| `lower_third` | `name` (mặc định `Mạnh Thành`), `role`, `y`=1180 | giới thiệu người nói 3–4s đầu |
| `badge` | `text`, `icon`, `x`, `y`, `size`, `color` | con số/từ khoá nổi đơn lẻ |

## 6. music / sfx

```json
"music": {"mode": "synth" | "file" | "none", "file": "nhac.mp3", "volume": 0.14},
"sfx_level": 1.0,
"sfx_extra": [{"t": 12.3, "type": "ding" | "pop" | "whoosh"}]
```
SFX tự sinh: whoosh khi vào scene; pop khi phần tử có animation pop/left/right/down/stamp bật ra; ding cho stamp và
pill CTA của summary. Pop cách nhau < 0.14s tự gộp.

## 7. Icon
`check`, `check_dark`, `x`, `bolt`, `bookmark`, `warn`, `chat`, `person`, `gear`, `mountain`.
Thêm icon mới: viết hàm trong `scripts/engine/gfx.py` (vẽ 4× rồi thu nhỏ) và đăng ký trong `ICONS` ở `components.py`.
Thêm component mới: hàm trả về `(bg, [Layer])` (scene) hoặc `[Layer]` (overlay), đăng ký vào `SCENE_BUILDERS`/`OVERLAY_BUILDERS`.
