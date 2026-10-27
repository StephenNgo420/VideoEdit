# Troubleshooting

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| Lệnh bị dừng sau 300s, file dở dang | Chạy job dài bằng `run_bg.sh`, theo dõi `tail`. File .m4a/.mp4 dở dang báo "moov atom not found" → chạy lại. |
| Tiến trình nền biến mất không log | Dùng `run_bg.sh` (setsid). `nohup ... &` thường bị kill khi lệnh bash kết thúc. |
| Transcribe chậm / hết RAM | `--model medium` (nhanh hơn, kém chính xác hơn). Model tải ~1.6GB lần đầu từ HuggingFace. |
| Tên riêng sai hàng loạt | Thêm vào `--prompt` khi transcribe; sửa phần còn lại bằng `captions.fixes`. |
| Phụ đề lệch tiếng | Timestamp Whisper lệch ở đoạn nói nhanh — chỉnh `word_overrides` hoặc chấp nhận (lệch <0.2s không thấy). Kiểm tra video nguồn có VFR không: renderer ép 30fps khi decode nên vẫn khớp audio. |
| Chữ tràn thẻ | Rút ngắn chữ (≤ 4–5 từ). Các component tự co font nhưng có giới hạn dưới. |
| Dấu tiếng Việt bị cắt/ô vuông | Chỉ dùng font trong `assets/fonts` (Inter, Pacifico đều hỗ trợ tiếng Việt). |
| Mặt bị cắt khi zoom | Sửa `face` cho đúng tâm mặt; giảm scale shot xuống 1.08–1.1. |
| Nguồn ngang 16:9 | Tự cắt 9:16 quanh `reframe_x` (lấy từ probe.json). Kiểm stills; người nói di chuyển nhiều → cân nhắc layout split cho toàn video. |
| B-roll đen/đứng hình | Clip hỏng hoặc codec lạ: xoá `broll/prep_*.mp4` tương ứng, tải lại hoặc chọn pick khác. |
| fetch_broll 401/403 | Sai key hoặc hết quota; thử nguồn còn lại (Pixabay/Pexels). |
| Âm lượng nhạc át giọng | Giảm `music.volume` (0.08–0.12). Nhạc có lời → dùng bản instrumental. |
| Render quá lâu | Mỗi scene/overlay tốn ít; chậm chủ yếu do decode HEVC + encode. Test đoạn ngắn bằng `render <edl> render t0 t1`. |
| Muốn xuất ngang 16:9 | Chưa hỗ trợ bố cục ngang — component thiết kế cho 9:16. Báo người dùng; có thể dựng dọc rồi làm bản ngang riêng. |
