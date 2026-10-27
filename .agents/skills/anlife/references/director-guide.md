# Director guide — cách nghĩ khi lập EDL

Mục tiêu của video ngắn: người xem **không lướt qua trong 3 giây đầu**, hiểu được **khi tắt tiếng**, và **luôn có thứ gì đó
thay đổi trên màn hình mỗi 2–4 giây**. Hiệu ứng chỉ phục vụ ý; một ý rõ ràng đặt đúng lúc giá trị hơn mười hiệu ứng.

## 1. Đọc transcript như biên tập viên

Trước khi viết EDL, chia transcript thành các "nhịp" và đánh dấu:
- **Hook**: câu gây tò mò nhất / câu hỏi / con số mạnh. Nếu nó không nằm ở đầu, đặt tiêu đề hook (overlay `title_box`)
  tóm ý đó ngay từ khung hình đầu tiên (`t0: -1` để hiện sẵn — khung đầu chính là thumbnail trên feed).
- **Liệt kê** ("có 4 loại…", "thứ nhất… thứ hai…", "phù hợp với A, B, C") → scene `cards_grid` / `checklist`.
- **So sánh / đối lập** ("A giống như…, còn B…", "quá mạnh… hoặc quá nhẹ…") → `versus` / `rows_x` / `meter`.
- **Chuyển phần** ("Đầu tiên là…", "Tiếp theo…", "Cuối cùng…") → scene `chapter` (nền đỏ, 1.8–2.8s) + `chapters` pill.
- **Lời khuyên / cảnh báo / câu chốt** → overlay `callout` (+stamp), `warning`, `chips`, hoặc scene `statement`.
- **Câu mô tả tình huống đời thường** (người dùng bối rối, làm việc với laptop, họp nhóm, nhận tin nhắn) → **B-roll video**.
- **Kêu gọi lưu/chia sẻ** → scene `summary` (bảng tóm tắt — thứ người ta muốn lưu lại).
- **Nhắc tên sản phẩm/giải pháp lần đầu** ("…với Acronis Cyber Protect Cloud") → scene `brand_reveal` với logo đối tác.
- **CTA bán hàng/liên hệ** → overlay `cta` ở cuối, giữ đến hết video. Chỉ thêm `partner_logo` khi người dùng chủ động cung cấp
  hoặc yêu cầu; không chèn logo thương hiệu mặc định.
- **Whisper hay "bịa" câu cuối** kiểu "Hãy subscribe cho kênh…" khi video kết thúc bằng khoảng lặng: xoá segment đó trong
  bản copy transcript (`"transcript": "transcript_clean.json"`) và đặt `duration` cắt đuôi.

## 2. Công thức nhịp (video 60–180s)

| Thành phần | Tần suất gợi ý |
|---|---|
| Cảnh full-screen (graphic hoặc B-roll full) | 1 cảnh mỗi 10–20s, mỗi cảnh 2–9s |
| Không thấy mặt liên tục | tối đa ~12s; xen lại cảnh nói giữa 2 scene dài |
| Overlay trên cảnh nói | khi có ý đáng nhấn, 2–8s, không chồng 2 overlay cùng lúc |
| Đổi khung zoom (shot) | mỗi câu/ý (4–8s), xen kẽ rộng (1.0) ↔ cận (1.12–1.16) |
| Punch-in | 1 lần mỗi 8–20s, đúng từ nhấn mạnh nhất; hệ số 1.08–1.13 |
| B-roll | 1–3 cảnh / phút; ưu tiên chỗ người nói kể tình huống, không dùng khi đang giảng ý trừu tượng cần đồ hoạ |

Quá nhiều cũng hỏng: phụ đề + overlay + pill + B-roll cùng lúc làm rối. Mỗi khoảnh khắc chỉ nên có **một** điểm nhấn chính.

## 3. Đồng bộ thời gian

- Lấy mốc từ `words.txt`. Phần tử liệt kê hiện **đúng lúc nói tên mục đó** (`t` = thời điểm từ đầu tiên của mục).
- Scene bắt đầu ~0.1–0.2s trước câu mở đầu ý, kết thúc ngay khi ý đó nói xong (≈ bắt đầu câu kế tiếp). Transition vào 0.25s,
  ra 0.2s đã có sẵn.
- `shots` phủ các đoạn nói (không cần phủ trong scene full). Cắt shot đúng đầu câu (`t` của từ đầu câu) → nhảy khung tự nhiên.
- Overlay nên vào trước câu liên quan ~0.2–0.5s để mắt kịp đọc tiêu đề, chi tiết bên trong hiện theo lời.
- `captions.exclude` cho đoạn hook nếu đã có thẻ câu hỏi hiển thị cùng nội dung.

## 4. Bố cục khung dọc 1080×1920

```
y 0-8      thanh tiến trình
y 150-230  logo (trong scene) / pill chương (x=70, y=175)
y 250-720  VÙNG OVERLAY (trên đầu người nói) — overlay mặc định y=300
y 720-1150 mặt + vai (đừng che)
y ~1475    phụ đề (ngực người nói)
y 1600+    bị UI TikTok/Reels che (caption, nút) — không đặt thông tin quan trọng
x > 950    icon bên phải của app — tránh chữ quan trọng
```
Nếu mặt người nói nằm cao/thấp khác mẫu: chỉnh `face` (tâm zoom) và `captions.y`, overlay `y`. Luôn kiểm bằng stills.

## 5. Chữ trên màn hình

- Tiêu đề ≤ 5 từ, mục liệt kê ≤ 4–5 từ. Viết lại lời nói cho gọn (lời nói: "những việc cực kỳ đơn giản như lặp đi lặp lại"
  → chữ: "Việc lặp lại"). Không chép nguyên câu.
- `highlight` 1 cụm then chốt mỗi tiêu đề (tô màu brand).
- Chỉ ghi điều người nói thực sự nói — không bịa số liệu, tính năng, giá. Tên phiên bản chỉ ghi nếu họ nói ra.
- Tiếng Việt có dấu: luôn kiểm stills xem dấu có bị cắt không.
- Font script (`title_box.script_line`, `statement.highlight`) chỉ dùng điểm xuyết 1–2 lần/video.

## 6. Màu & âm thanh

- **Màu da giữ nguyên như video gốc.** `grade` mặc định là `natural` = không đổi màu/nhiệt màu/độ bão hoà. KHÔNG dùng
  `warm_clean` (làm da vàng) trừ khi người dùng yêu cầu rõ "chỉnh ấm"/"chỉnh màu". `bright` chỉ khi video quá tối và người
  dùng đồng ý; `neutral` chỉ tăng nhẹ tương phản. Có thể truyền chuỗi filter ffmpeg tuỳ ý nếu người dùng yêu cầu.
- **Mịn da nhẹ**: `skin_smooth` mặc định 0.35 (chỉ làm mịn vùng màu da, không đổi màu, giữ chi tiết tóc/râu/mắt). Người dùng
  muốn mịn hơn → 0.5–0.6; không muốn → 0. Không vượt 0.7 (da bết như nhựa). Kiểm trên stills: so màu da với
  `contact_sheet.jpg` của video gốc — phải giống hệt, không ám vàng/cam.
- Nhạc: `synth` chỉ là nhạc tạm. Có file nhạc bản quyền → `{"mode":"file","file":"...","volume":0.12-0.18}`. Luôn giao kèm
  bản không nhạc để người dùng tự chèn nhạc trên nền tảng.
- `sfx_level` 0.6–1.2. Video trang trọng (tài chính, pháp lý) → 0.6.

## 7. Checklist trước khi render full

- [ ] Khung hình đầu (t=0) có tiêu đề hook đọc được.
- [ ] Mọi mục liệt kê khớp lời (xem stills tại t của mục + 0.4s).
- [ ] Không overlay nào đè mặt; không chữ tràn thẻ; không 2 overlay chồng nhau.
- [ ] Không đoạn nào >12s không thấy mặt; không đoạn nói nào >10s không có thay đổi (shot/overlay/scene).
- [ ] Từ đã sửa trong phụ đề đúng; từ đoán đã ghi chú để hỏi người dùng.
- [ ] B-roll đúng chủ đề, không có logo/brand lạ, không người nổi tiếng.
- [ ] CTA cuối có liên hệ đúng (từ config), giữ đến hết video.
- [ ] Màu da trên stills giống video gốc (không ám vàng/cam); da mịn nhẹ, râu/tóc/mắt vẫn sắc nét.
