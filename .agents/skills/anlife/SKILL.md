---
name: anlife
description: >-
  Dựng video nói chuyện quay sẵn (talking-head, chia sẻ kiến thức, review, bán hàng) thành video chuyên nghiệp dạng dọc 9:16
  cho Reels/TikTok/Shorts: phụ đề tiếng Việt chạy theo từng từ, zoom/jump-cut, cảnh minh hoạ bằng chữ và đồ hoạ khớp lời nói,
  cảnh trám bằng video/ảnh stock (Pexels/Pixabay) hoặc clip người dùng gửi, chỉnh màu, SFX, nhạc nền, chuẩn loudness, CTA cuối
  theo brand. BẮT BUỘC dùng khi người dùng upload video .mp4/.mov và muốn "dựng", "edit", "làm cho hấp dẫn/chuyên nghiệp",
  "thêm phụ đề/sub", "thêm hiệu ứng", "zoom", "chèn text minh hoạ", "cảnh trám", "b-roll", "chỉnh màu", "làm reels/tiktok/shorts",
  kể cả khi họ không nói chữ "dựng video". Cũng dùng khi sửa lại video đã dựng bằng skill này (đổi chữ, thay nhạc, thêm B-roll).
---

# Dựng video talking-head chuyên nghiệp

Skill biến 1 video người nói thành video ngắn có nhịp nhanh, dễ xem không cần bật tiếng, đúng brand. Toàn bộ dựng bằng code
(ffmpeg + Python) theo một file kịch bản dựng **EDL JSON** do trợ lý viết từ transcript. Trợ lý đóng vai **đạo diễn**: quyết
định câu nào thành hook, chỗ nào zoom, chỗ nào thay cảnh ngồi nói bằng minh hoạ, chỗ nào chèn video trám.

```
video ─► probe ─► transcribe (nền) ─► rà lỗi chữ ─► lập EDL ─► tải B-roll ─► ảnh xem trước ─► render (nền) ─► audio (nền) ─► finalize
```

`SK=<thư mục skill này>` (trong repo: `.agents/skills/anlife`; chạy `source scripts/activate.sh` từ gốc repo). Mọi script nằm trong `$SK/scripts/`.
Thư mục làm việc: `video-work/<slug>/ trong repo` (được Git bỏ qua; không lưu dữ liệu dự án vào thư mục skill).

## Giới hạn môi trường — đọc trước

- Mỗi lệnh bash bị cắt sau ~300 giây. Transcribe, render, audio đều lâu hơn → **luôn chạy nền**:
  `bash $SK/scripts/run_bg.sh <log> <lệnh…>` rồi theo dõi bằng `tail -3 <log>` (poll theo khoảng ngắn để tiếp tục báo tiến độ) (dòng `DONE` = xong).
- Đo CPU/RAM trước khi chạy; tham khảo trên máy 1 CPU: render ~3–4 fps → video 2 phút mất ~15–18 phút; transcribe mất 1–2 phút nạp model + ~1× thời lượng. Không chạy 2 job nặng
  song song (chậm cả hai). Báo người dùng thời gian chờ ước tính.
- Theo dõi job đến khi hoàn tất hoặc gặp blocker cụ thể; báo tiến độ trung thực, không nói đã xong khi job còn chạy.
- File upload lớn (>100MB) vẫn xử lý được; video HEVC/iPhone ổn.

## Quy trình

### 1. Chuẩn bị & khảo sát
```bash
bash $SK/scripts/setup.sh
python3 $SK/scripts/probe.py <video> <workdir>
```
Xem `contact_sheet.jpg` (tool xem ảnh có sẵn): bố cục khung, nền, vị trí mặt, ánh sáng lệch màu. **Màu da: giữ nguyên như video gốc** (`grade: "natural"`, mặc định) và chỉ làm mịn da nhẹ (`skin_smooth: 0.35`) — không
tự ý chỉnh ấm/vàng. `probe.json` gợi ý `face`
(tâm zoom) và `reframe_x` nếu nguồn ngang (renderer tự cắt 9:16 quanh mặt).

### 2. Transcribe (nền)
```bash
bash $SK/scripts/run_bg.sh <workdir>/tr.log python3 $SK/scripts/transcribe.py <video> <workdir> --lang vi \
  --prompt "Mạnh Thành, <tên riêng/thuật ngữ trong video>"
```
`--prompt` chứa thuật ngữ giúp Whisper viết đúng tên riêng. Kết quả: `transcript.json`, `transcript.txt`, `words.txt`
(từ@giây — dùng để canh thời gian), `low_confidence.txt`.

### 3. Rà lỗi chữ
Đọc `transcript.txt` + `low_confidence.txt`. Whisper tiếng Việt hay sai tên riêng, thuật ngữ tiếng Anh ("Cloth"→Claude,
"code bay"→codebase). Sửa bằng `captions.fixes` / `merges` / `word_overrides` trong EDL. Từ nào **đoán** (không chắc) thì
ghi lại để báo người dùng ở cuối — đừng lặng lẽ đoán.

### 4. Lập EDL (phần quan trọng nhất)
Đọc **`references/director-guide.md`** (nguyên tắc dựng: hook, nhịp, khi nào dùng scene/overlay/B-roll, vùng an toàn) và
**`references/edl-schema.md`** (toàn bộ trường, component, toạ độ). Bắt đầu bằng cách copy `examples/claude-models.edl.json`
rồi thay nội dung — đây là video thật đã được duyệt, dùng làm chuẩn chất lượng.

Mọi mốc thời gian lấy từ `words.txt`: phần tử hiện ra **đúng lúc người nói nói từ đó** (t của từ, trừ ~0.05s).

### 5. Cảnh trám video (B-roll)
Scene `broll`/`image` có `query` (tiếng Anh, mô tả hình ảnh cụ thể) → tải bằng:
```bash
python3 $SK/scripts/fetch_broll.py <edl> --preview    # thumbnail ứng viên -> broll/candidates_*.jpg, xem và đặt "pick"
python3 $SK/scripts/fetch_broll.py <edl>              # tải clip đã chọn, ghi đường dẫn vào EDL
```
API key Pexels/Pixabay là tuỳ chọn: chỉ cấu hình bằng biến môi trường `PEXELS_API_KEY` / `PIXABAY_API_KEY`, không ghi key vào file hoặc chat. Không có key: dùng clip/ảnh người dùng upload (`"clip"`/`"src"`), hoặc bỏ scene đó — renderer tự bỏ qua scene thiếu clip.
Chi tiết chọn cảnh, bản quyền: `references/broll-guide.md`.

### 6. Ảnh xem trước — bắt buộc trước khi render
```bash
python3 $SK/scripts/render.py <edl> stills 2 9 23 36 48 55 ...   # chọn 1 mốc giữa MỖI scene/overlay
```
Xem `stills/sheet_*.jpg`. Kiểm: chữ tràn khung, overlay đè mặt, phần tử chồng nhau, lỗi dấu tiếng Việt, B-roll lạc đề. Sửa EDL
và chạy lại đến khi sạch. Render lỗi mất 15 phút, còn stills chỉ mất vài giây.

### 7. Render + audio (nền, tuần tự)
```bash
cat > <workdir>/job.sh <<EOF
python3 $SK/scripts/render.py <edl> render
python3 $SK/scripts/audio.py <edl>
EOF
bash $SK/scripts/run_bg.sh <workdir>/job.log bash <workdir>/job.sh
```
`render` ghi `sfx_events.json` (whoosh mỗi lần vào scene, pop khi thẻ bật ra, ding cho stamp/CTA) → audio tự khớp. Audio:
lọc ồn, EQ, nén giọng, nhạc nền tự giảm khi nói (sidechain), loudness −14 LUFS. Thử 1 đoạn ngắn: `render <edl> render 18 26`.

### 8. Finalize & giao
```bash
python3 $SK/scripts/finalize.py <edl> --out outputs
```
Tạo `<output_name>_final.mp4` (có nhạc) + `_khong-nhac.mp4` trong `outputs/` trong repo, và `final_check.jpg` — xem
nó, rồi đưa liên kết tải đến cả hai video bằng công cụ hiện có.

Báo người dùng ngắn gọn: những gì đã làm (phụ đề, số cảnh minh hoạ, B-roll, màu giữ gốc + mịn da nhẹ, âm thanh), **các từ đã đoán cần xác nhận**,
nhạc synth chỉ là tạm (gửi nhạc bản quyền để thay), và muốn sửa gì thì nói — sửa EDL rồi render lại.

## Sửa sau phản hồi
Chỉ sửa EDL (đổi chữ, mốc thời gian, thêm/bớt scene, `music.file`…) → stills các chỗ đổi → render lại → `audio.py` (chỉ cần
nếu scene/overlay/nhạc đổi) → finalize. Transcript không cần chạy lại.

## Nhận diện Anlife
Màu và dòng liên hệ đọc từ `assets/config.json`. Mặc định dùng xanh lam `#2563EB` (đậm `#1D4ED8`, nhạt `#DBEAFE`),
chữ `#333333`, font Inter và **không chèn logo thương hiệu**. Dòng liên hệ mặc định là `[SĐT : 0377.526.213]`.
Tên người nói mặc định cho overlay `lower_third` là `Mạnh Thành`; chỉ đổi khi người dùng yêu cầu rõ. Logo sản phẩm/đối tác chỉ được
dùng khi người dùng chủ động cung cấp hoặc yêu cầu, không tự thêm logo thương hiệu vào video.

## Tham khảo
- `references/director-guide.md` — tư duy đạo diễn, công thức nhịp, checklist chất lượng. **Đọc mỗi lần lập EDL.**
- `references/edl-schema.md` — schema đầy đủ, mọi component và tham số.
- `references/broll-guide.md` — viết query, chọn clip, layout full/split, bản quyền.
- `references/troubleshooting.md` — lỗi thường gặp (font, timeout, lệch tiếng, clip lỗi).
- `examples/claude-models.edl.json` — EDL mẫu hoàn chỉnh (129s, 12 scene, 10 overlay, 2 B-roll).

## Cài đặt trên Codex

Đọc `docs/SETUP.vi.md` ở gốc repo để biết dependency, giới hạn mạng và những bước cần làm ở session mới. Chạy `source scripts/activate.sh` trong mỗi shell mới. Không cần tạo Git worktree.
