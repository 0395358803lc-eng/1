# Vận hành trên nhiều máy chủ, workspace và kênh

## Khởi động và chọn máy
- Mỗi lần bắt đầu phiên plugin/dự án mới, khám phá schema hiện tại và gọi `list_devices` trên tất cả account/link có trong schema. Hiển thị danh sách thiết bị và trạng thái; chỉ máy online có thể chọn. Không hiển thị device ID, link ID, email hay credential. Không dùng ID từ phiên cũ; resolve lại ở mỗi phiên.
- Chờ user chọn đúng máy trước khi gọi bất kỳ thao tác đọc/ghi file hoặc shell nào. Sau đó hỏi đường dẫn thư mục phim và thư mục logo (hoặc “không có logo”). Không tự đoán đường dẫn. Nếu user chọn máy khác cho workspace cũ, phải liệt kê và xin chọn máy đó trước.
- Dùng đúng link/device ID trả về từ lần liệt kê hiện tại. Nếu nhiều account cùng có tên máy, phân biệt bằng nhãn không nhạy cảm. Không tự cấp quyền hoặc chuyển sang máy khác khi kết nối mất.

## Hợp đồng workspace chuẩn
- Root duy nhất: `<film_dir>/REVIEW_PHIM_WORKSPACE`. Không tạo workspace cạnh phim ở vị trí khác. Nếu root đã tồn tại, kiểm kê read-only rồi dùng; không xóa, làm sạch, thay thế hoặc ghi đè.
- Cấu trúc khuyến nghị:
  - `workspace_manifest.json` — thông tin root, phim/logo đã chọn, fingerprints, schema version; không chứa credential hay device/link IDs.
  - `jobs/<job-id>/` — `config.json`, `state.json`, `approval_log.json`, `logs/`, `reports/`, `asr/`, `frames/`, `understanding/`, `script/`, `tts/`, `timeline/`, `preview/`, `postproduction/`, `delivery/`, `youtube/`.
  - `imports/<import-id>/` — bản nhập có nguồn gốc và báo cáo, không ghi đè.
  - `profiles/channels/` và `profiles/servers/` — profile riêng, không có session IDs/credentials.
  - `shared/python/` — venv riêng của workspace; `shared/models/`, `shared/cache/`, `shared/bin/` — model/cache/binary portable đã xác minh.
  - `assets/branding/<channel-id>/` — bản sao logo được chọn, chỉ sau phê duyệt; giữ nguyên file nguồn.
- Không copy phim gốc vào workspace theo mặc định. Config lưu đường dẫn nguồn và fingerprint. Nếu user chỉ cung cấp thư mục logo, liệt kê file logo; nếu có nhiều file, hỏi chọn đúng file. Không dùng logo của job/kênh khác.
- Mỗi job có thư mục riêng, không ghi artefact của job mới vào job cũ. Nếu cùng phim/cùng cấu hình và user muốn resume, dùng job đã xác minh thay vì tạo dữ liệu trùng; vẫn lưu checkpoint mới có version.

## Nhập workspace cũ
- Sau khi current root tồn tại, hỏi đường dẫn workspace cũ hoặc “không có”. Không quét toàn bộ ổ đĩa và không tự chọn một kết quả mơ hồ.
- Trước khi nhập, chỉ kiểm kê read-only; tạo migration plan có file, kích thước, fingerprint, đích đến, tương thích, stale/usable và lý do. Chờ user duyệt.
- Copy không phá hủy vào `imports/<import-id>/` hoặc job mới; giữ nguyên workspace cũ và mọi artefact hiện tại. Không overwrite; nếu trùng tên, tạo version/namespace riêng. Không nhập secrets, credentials, link/device IDs, session tokens, lock/PID, absolute venv paths hoặc cấu hình không tương thích.
- Chỉ đánh dấu artefact có thể tiếp tục khi source fingerprint, cấu hình upstream và dependencies phù hợp. Nếu fingerprint khác, giữ dữ liệu cũ để tham khảo và đánh dấu downstream `stale`; không tái sử dụng timeline/render như thể hợp lệ.
- Nếu có workspace cũ, không chạy full environment survey/install mặc định. Kiểm tra runtime đã có; nếu thiếu hoặc không tương thích, chỉ đề xuất các thành phần thiếu và xin duyệt trước khi cài.

## Khảo sát và cài đặt môi trường
- Khi không có workspace cũ, khảo sát OS, shell, CPU, RAM, GPU/VRAM, disk, quyền ghi; Python/venv; FFmpeg/ffprobe/encoders/hwaccels; package versions; ASR/CTranslate2; VieNeu-TTS; model/cache. Không giả định NVIDIA/Windows.
- Trước khi cài, xuất danh mục theo nhóm: Python/runtime; media binaries; image/video/audio packages; ASR; TTS; models/cache; GPU-specific runtime. Mỗi dòng ghi installed/missing, version, reason, target path, approximate download/disk footprint, source/license if known. User duyệt danh mục cụ thể.
- Package Python cài vào `REVIEW_PHIM_WORKSPACE/shared/python/.venv` hoặc venv có tên/version tương đương. Model/cache vào `shared/models` và `shared/cache`. Binary portable vào `shared/bin` khi license/OS cho phép. Không cài global, không thay đổi PATH/system policy, không tự cập nhật OS/driver. Không tải model lớn hoặc tạo chi phí khi chưa duyệt. Driver/system dependencies là blocker cần user xử lý.
- Test thực tế sau cài: import, load/infer offline nếu cache đầy đủ, 2–10s decode/encode, scene detect, smoke test TTS/ASR nếu có. Không đánh pass chỉ vì package xuất hiện trong danh sách.

## Phê duyệt từng bước — bắt buộc
- Mỗi bước được đánh số 01–40 là một đơn vị phê duyệt độc lập. Giai đoạn chỉ là nhóm tổ chức, không phải đơn vị cấp quyền; không dùng nút `Thực thi Giai đoạn N`.
- Trước mỗi bước, trình bày số bước, mục tiêu, đầu vào, thao tác, đầu ra, rủi ro và phạm vi thay đổi; sau đó chỉ hiển thị một nút `Thực thi bước NN`.
- Callback nút dùng `GenUI.issueNewTurn(...)`, gửi câu xác nhận gồm job, giai đoạn, số bước và chỉ thị không chạy bước kế tiếp. Nếu UI không hỗ trợ, yêu cầu câu xác nhận bằng văn bản nêu rõ bước.
- Chỉ chạy bước được duyệt. Sau khi hoàn tất, kiểm tra kết quả, lưu checkpoint/approval log, báo `pass / partial / blocked / stale`, bằng chứng, tệp, số liệu, lỗi và giới hạn; rồi dừng.
- Sau báo cáo mới hiện nút cho bước pending kế tiếp. Không tự chạy bước kế tiếp dù cùng giai đoạn hoặc khi người dùng từng yêu cầu “chạy toàn bộ”.
- Nếu bước bị block/partial, dừng ở đó. Chỉ cho phép bổ sung thông tin hoặc duyệt chạy lại đúng bước; không bỏ qua. Bước pass chỉ chạy lại khi nêu lý do và xin duyệt lại.
- Các thao tác bootstrap ngoài 40 bước (tạo workspace, nhập workspace, cài dependencies, tải model/cache, copy logo) có phê duyệt riêng theo từng thao tác hoặc nhóm có phạm vi cụ thể.
- Phê duyệt một bước không bao gồm xóa/ghi đè, crop/mask không phục hồi, cài hệ thống/driver, download lớn/chi phí, chuyển dữ liệu ra ngoài, chia sẻ hoặc xuất bản; các hành động này cần xác nhận riêng.
- Lưu `approval_log.json` append-only với `scope_type: step|bootstrap`, `stage_number`, `step_number` (nếu là bước), phạm vi, văn bản xác nhận, thời điểm, trạng thái, evidence paths và notes. Ghi cả sự kiện bắt đầu và kết quả hoàn tất; không lưu ID thiết bị/tài khoản hoặc token.

## Kỹ thuật và an toàn vận hành
- Dùng công cụ remote/local đã kết nối và được cấp quyền. Với Remote Desktop Commander, khám phá đúng action hiện tại; đọc OS và shell. Windows thường dùng PowerShell, Linux/macOS dùng shell phù hợp. Quote đường dẫn có dấu/khoảng trắng; ưu tiên subprocess argument list. Tool trả ảnh phải chuyển block ảnh để ChatGPT nhìn; không dựa vào tên file.
- Lưu log tiến độ thực; nếu process còn chạy, đọc output của đúng PID/handle. Nếu tool call pending, lấy kết quả của đúng call; không chạy lặp request đang pending. Không hứa công việc nền.
- Profile server: alias, OS, executor, workspace root, tool paths, venv, model cache, CPU/GPU/VRAM/free disk, encoder/decoder smoke tests. Không lưu device/link/session ID hoặc credentials. Profile channel riêng cho mỗi kênh: channel_id do user chọn, display name, ngôn ngữ, giọng, tone, target duration, logo path, overlay, subtitle font, music/ducking, output, CTA/hashtag.
- Không dùng sandbox ChatGPT làm bằng chứng từ server. Không đưa đường dẫn riêng hoặc dữ liệu nhận dạng máy chủ vào metadata công khai.

## Mẫu kỹ thuật tham khảo (không phải lệnh chạy mù)
- Probe: `ffprobe -v error -show_streams -show_format -of json INPUT`. Ghi audio track, timebase, VFR/CFR, sample rate, subtitle streams và display aspect ratio.
- ASR: FFmpeg đọc track được chọn sang mono PCM 16 kHz; Faster-Whisper theo chunk có overlap, giữ offset, dedup cẩn trọng và verify coverage. Không đoán ngôn ngữ khi audio đa track.
- Frames: trích theo PTS thực; contact sheet có ID/timestamp; batch nhỏ, ảnh đủ rõ. Lấy mẫu dày ở vùng thiếu.
- Scene boundaries: FFmpeg/PySceneDetect trên proxy; threshold chỉ là gợi ý; kiểm duyệt ảnh.
- TTS: dùng preset/API đã xác minh; lưu WAV từng đoạn và master; ASR ngược là chỉ báo, không thay nghe thật.
- Timeline: chia lời kể theo đơn vị ngữ nghĩa; ChatGPT chọn cảnh có bằng chứng; cắt theo frame; kiểm tra liên tục và sai lệch audio/video.
- Subtitle: SRT/ASS theo audio; font có glyph tiếng Việt; kiểm tra cue ở midpoint và biên nối; không nhầm chữ bối cảnh/logo/credit.
- Audio: nhạc nguyên bản hoặc nguồn có quyền; giữ stem, duck, đo loudness/true peak; không dùng nhạc phim gốc khi chưa có quyền.
- Render: encoder đã smoke-test; temp file + validate + rename; ffprobe và decode đầy đủ; giữ version cũ.

## Scripts hỗ trợ
`scripts/workflow_state.py` tạo state 40 bước, ghi checkpoint có evidence, resume và invalidate; không tự kết nối hoặc chạy media. `scripts/check_timeline.py` kiểm tra JSON timeline theo frame, không thay QC trực quan. Đọc source trước khi chạy. Pipeline ASR/TTS/render phải adapt theo môi trường thật.
