# B-roll guide — cảnh trám video/ảnh

## Khi nào dùng B-roll (thay vì đồ hoạ)
- Người nói kể **tình huống cụ thể nhìn thấy được**: "khách hàng gọi điện phàn nàn", "nhân viên làm báo cáo đến khuya",
  "đội ngũ họp", "bạn đang lướt điện thoại". → B-roll.
- Người nói giảng **ý trừu tượng / số liệu / danh sách** → dùng scene đồ hoạ (rõ hơn, không lạc đề).
- 1–3 cảnh / phút là đủ. Mỗi cảnh 3–6s. Không B-roll ở hook (khán giả cần thấy mặt để tin) và ở CTA.

## Viết query
- Tiếng Anh, 3–6 từ, mô tả **hình ảnh** chứ không mô tả ý: "stressed woman working late laptop office" tốt hơn "productivity".
- Đưa 2–3 query dự phòng trong list, từ cụ thể đến chung.
- Thêm bối cảnh châu Á nếu cần gần gũi: "asian businessman meeting", "vietnamese street cafe laptop".
- Tránh query dễ ra logo thương hiệu, người nổi tiếng, cảnh nhạy cảm.

## Chọn clip
1. `fetch_broll.py <edl> --preview` → xem `broll/candidates_<t0>.jpg` (ô `#k` = pick k, có thời lượng và độ phân giải).
2. Chọn clip: đúng ý câu nói, ánh sáng/tông gần video chính, chuyển động nhẹ, không chữ/logo, đủ dài (≥ độ dài scene).
3. Đặt `"pick": k` vào scene rồi chạy lại không có `--preview` để tải. Script không dùng lại 1 clip cho 2 scene.
4. Luôn xem stills tại giữa scene B-roll trước khi render.

## Layout
- `full`: khi câu nói hoàn toàn là mô tả tình huống; có thể thêm `headline` ngắn (≤ 5 từ) ở trên.
- `split`: khi người nói vẫn đang biểu cảm/nhấn mạnh — giữ mặt ở nửa dưới. Clip ngang hợp split hơn.

## Nguồn & bản quyền
- **Pexels** (pexels.com/api) và **Pixabay** (pixabay.com/api/docs): miễn phí, dùng thương mại, không bắt buộc ghi nguồn.
  Không được bán lại clip nguyên bản hoặc gợi ý người trong clip xác nhận sản phẩm. `broll/credits.json` lưu nguồn từng clip.
- Clip/ảnh người dùng upload: đặt thẳng `"clip"`/`"src"`. Đây là lựa chọn tốt nhất cho demo sản phẩm, màn hình phần mềm.
- Không lấy video từ YouTube/TikTok/Facebook hay nguồn không rõ giấy phép.

## Không có API key
Hỏi người dùng 1 lần: "Anh có API key Pexels (miễn phí, đăng ký 1 phút tại pexels.com/api) không? Hoặc gửi em vài clip
minh hoạ." Nếu không có: giữ scene đồ hoạ thay cho B-roll — renderer tự bỏ qua scene B-roll thiếu clip.
Key có thể điền sẵn vào `assets/config.json` trước khi cài skill để lần sau không phải hỏi.
