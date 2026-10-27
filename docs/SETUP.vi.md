# Anlife trên VideoEdit

## Skill chứa gì?

Skill được cài ở `.agents/skills/anlife/` từ file `anlife.skill` người dùng cung cấp.
Nó gồm hướng dẫn dựng video talking-head dọc 9:16; kịch bản EDL JSON; các script
khảo sát video, nhận dạng lời nói theo từ, tìm B-roll, vẽ đồ hoạ/phụ đề, render,
xử lý âm thanh và ghép bản xuất; font Inter/Pacifico kèm giấy phép; tài liệu và EDL mẫu.
Không kèm video nguồn, model Whisper hay thư viện Python.

Các bước trong tài liệu là hướng dẫn dùng skill khi dựng video, không phải yêu cầu
tự động chạy dự án mẫu, đăng video, tải stock hoặc thay đổi nhận diện thương hiệu.
Brand mặc định ANLIFE, tên Mạnh Thành và dòng liên hệ được giữ nguyên trong config.
EDL mẫu chỉ minh hoạ bố cục; thông tin về các model trong ví dụ không được xác minh.

## Cần cài gì?

- Python 3.12 + venv; FFmpeg/ffprobe 7+ có libx264, AAC và các filter màu/âm thanh.
  Cloud hiện đã có Python 3.12.14 và FFmpeg 7.1.5, không cần cài lại ở máy này.
  Trên Debian/Ubuntu mới nếu thiếu: cài các gói `python3`, `python3-venv`, `ffmpeg`
  qua package manager của hệ điều hành; không cần GPU hay CUDA.
- `faster-whisper`, `opencv-python-headless`, `pillow`, `numpy`, `scipy` và dependency
  gián tiếp. Toàn bộ phiên bản được lưu trong `requirements.lock`; thư viện thực tế
  nằm trong `.venv/`, không đưa vào Git.
- OpenCV được ghim 4.12.0.88 và NumPy 2.2.6: bản OpenCV 5 được thử ban đầu thiếu
  `CascadeClassifier` mà `probe.py` dùng. Không tự nâng phiên bản nếu chưa kiểm thử.
- PyAV được ghim `av==16.0.1`: bản 19 không còn tham số `metadata_errors`
  mà faster-whisper 1.2.1 dùng khi đọc audio.
- Model mặc định `large-v3-turbo` tải lần đầu từ Hugging Face, khoảng 1.6 GB.
  Model/cache không commit. Font đã có trong skill, không cần cài font hệ thống.
- Pexels/Pixabay chỉ cần khi tự tìm stock; không cần cho render, phụ đề hoặc
  dùng clip/ảnh người dùng cung cấp. Không cần dịch vụ web, database hoặc API OpenAI.

## Cài và dùng

Tại gốc repo (trong cloud: `/workspace/VideoEdit`):

```bash
bash scripts/setup.sh
source scripts/activate.sh
python scripts/smoke_test.py
```

Setup dùng venv và dependency đã ghim, kiểm tra `pip check` và filter FFmpeg.
Lệnh activate cung cấp `python`, `SK`, `HF_HOME` trong shell hiện tại và giới hạn
thread cho thư viện số. Khi tool mở shell mới, phải source lại hoặc dùng đường dẫn
`.venv/bin/python` cùng cấu hình cache tương ứng.
Không cần tạo Git worktree: task cloud đã có checkout riêng.

Ví dụ dự án thật (thay đường dẫn video bằng file của bạn):

```bash
source scripts/activate.sh
mkdir -p video-work/demo
python "$SK/scripts/probe.py" /path/to/source.mp4 video-work/demo
python "$SK/scripts/transcribe.py" /path/to/source.mp4 video-work/demo --lang vi
# Đọc transcript, director-guide và edl-schema; tự lập EDL cho video này.
python "$SK/scripts/render.py" video-work/demo/edl.json stills 1 3
python "$SK/scripts/render.py" video-work/demo/edl.json render
python "$SK/scripts/audio.py" video-work/demo/edl.json
python "$SK/scripts/finalize.py" video-work/demo/edl.json --out outputs
```

Đường dẫn `source`, `transcript`, `workdir` trong EDL tính từ thư mục chứa EDL.
Đọc skill trước khi chọn cảnh và mốc preview. Job dài có thể dùng `run_bg.sh`;
theo dõi log và trạng thái tiến trình, không coi PID hay dòng DONE là bằng chứng
video đúng. Render và audio chạy tuần tự, job shell phải dùng `set -e` để dừng khi lỗi.

## Mạng, model và API key

Ban đầu proxy từ chối Hugging Face với `403` (CONNECT tunnel). Khi kiểm tra lại,
quyền mạng đã có hiệu lực: API truy cập được, model `large-v3-turbo` đã tải đầy đủ
và nạp thành công trên CPU int8. Script `transcribe.py` đã chạy hết và tạo đủ
`transcript.json`, `transcript.txt`, `words.txt`, `low_confidence.txt`.
Bài thử dùng tín hiệu âm thanh giả; chỉ xác nhận pipeline chạy, không chứng minh
độ chính xác trên lời nói thật. Whisper có thể tự sinh chữ trên tín hiệu không có
lời nói, nên không dùng transcript của bài thử làm nội dung thật.

Allowlist cần giữ trong Environment settings: `huggingface.co`, `*.huggingface.co`,
`*.hf.co`. Các miền này đã được lưu vào draft; máy hiện tại tải model được.
Để tái sử dụng cấu hình và snapshot ở task mới, review/lưu rồi publish môi trường.
Chưa xác minh publication hoặc phục hồi trong task mới.
Nếu máy mới báo 403 CONNECT, kiểm tra các miền trên có trong cấu hình đang áp dụng,
lưu cấu hình và thử lại sau khi cập nhật runtime. Nếu file model chuyển hướng tới
CDN khác và bị chặn, bổ sung đúng host bị từ chối; không tắt TLS hoặc checksum.

Model lưu dưới `.cache/huggingface/` sau khi source activate. Nếu cache được phục hồi
thì dùng lại; nếu không phải tải lại. Có thể truyền `--model /path/to/local/model`
cho model CTranslate2 tương thích đã tải sẵn.

API key được nhúng trong archive gốc đã được xoá khỏi bản đưa vào repo.
Không commit archive gốc. Chủ sở hữu nên thu hồi/đổi Pexels key đã chia sẻ.
Khi cần stock, đặt `PEXELS_API_KEY` hoặc `PIXABAY_API_KEY` trong environment settings
an toàn; không gửi key qua chat, command-line hoặc ghi vào `assets/config.json`.
`.env.example` chỉ ghi tên biến; các script không tự đọc `.env`.
Stock chưa kiểm thử vì không có key được cấu hình. Cần mở mạng tới API và host
download thực tế nếu dùng stock, ví dụ `api.pexels.com`, `images.pexels.com`,
`videos.pexels.com`, `pixabay.com` và `cdn.pixabay.com`. Chưa thêm các miền stock
tuỳ chọn vào draft, chưa khai báo key là yêu cầu bắt buộc.

## Session mới: cài lại / commit lại gì?

| Thành phần | Session mới cần làm gì? | Commit lại? |
|---|---|---|
| Skill, script, font, tài liệu, lockfile | Đã có sau khi checkout commit này | Không, trừ khi sửa nội dung |
| `.venv/` | Dùng lại nếu snapshot còn; nếu thiếu chạy `bash scripts/setup.sh` | Không |
| FFmpeg/Python | Dùng bản có sẵn; cài nếu máy mới chưa có | Không |
| Shell activation | `source scripts/activate.sh` trong mỗi shell mới | Không |
| Model Whisper/cache | Dùng cache nếu còn, tải lại nếu thiếu và mạng cho phép | Không |
| API key | Cấu hình an toàn, kiểm tra được inject ở máy mới; chỉ cần khi dùng stock | Không bao giờ |
| Video, transcript, EDL dự án, bản xuất | Lưu/backup riêng; cloud snapshot không thay backup | Không mặc định |
| Process render chạy dở | Không giả định sống qua session; kiểm tra file/log rồi chạy lại khi cần | Không |
| Cấu hình cloud install/start/network | Lưu ở Environment settings và publish để tái sử dụng | Không phải Git commit |

Git commit lưu file trong checkout hiện tại. Muốn lấy commit trên một máy khác
qua GitHub thì phải push; commit cục bộ không tự cập nhật `main` trên GitHub.
Publication cloud và push Git là hai bước khác nhau. Chưa kiểm chứng phục hồi
snapshot trong task mới.

## Kiểm chứng

`scripts/smoke_test.py` tạo video giả 4 giây và transcript giả (không nhận dạng lời nói),
chạy probe → preview → render → audio → finalize. Nó kiểm tra hai bản H.264/AAC
1080×1920 đủ 120 frame, thời lượng, khả năng decode đầy đủ, ảnh preview và sự kiện SFX.
Output nằm trong `video-work/smoke-*` và được Git bỏ qua.
Đây không phải kiểm tra độ chính xác phụ đề tiếng Việt từ giọng thật hoặc chất lượng
face detection trên người thật. Cần video thật để kiểm tra các phần đó.

Kết quả trong session cài đặt: smoke test đạt cả hai bản xuất; preview đã được xem
và hiển thị dấu tiếng Việt. `pip check`, kiểm tra filter FFmpeg và chạy lại setup
(cả qua wrapper của skill lẫn khi venv đã activate) đều đạt. Đã rà các file sẽ commit
và xác nhận không chứa API key nhúng trong archive gốc. Sau khi quyền mạng có hiệu lực và ghim PyAV 16.0.1, pipeline transcribe đã chạy
được trên âm thanh giả. Stock vẫn chưa kiểm chứng do chưa cấu hình API key.
