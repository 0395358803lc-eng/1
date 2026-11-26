# Tám tầng kiểm duyệt (cổng chất lượng)
Mỗi cổng lưu JSON hoặc Markdown có job_id, gate, status, input/output fingerprints, phương pháp, phạm vi, metrics, issue IDs, bằng chứng, quyết định sửa/giữ, giới hạn, thời gian kiểm tra. pass = đủ tiêu chí kỹ thuật và phạm vi đã công bố; không có nghĩa chính xác tuyệt đối. partial = còn việc cần làm; blocked = thiếu khả năng/dữ liệu; stale = input đổi. skipped chỉ khi không áp dụng hoặc user chủ động bỏ qua, ghi lý do. Không tự nâng partial thành pass.

| Cổng | Sau bước | Phạm vi và bằng chứng tối thiểu |
|---|---:|---|
| QC1 — Nhận dạng âm thanh | 09 | Stream/language đúng, mọi chunk có manifest, segment ID/timecode hợp lệ, không mất dòng khi dịch, các khoảng im lặng và flags được ghi, nguồn không đổi. Bản dịch không có tiếng Trung sót ngoài tên/chú thích có chủ ý. Kiểm tra chéo số segment, timestamp, file đọc được. |
| QC2 — Hiểu phim | 16 | Kiểm tra coverage ảnh ban đầu theo ID, transcript liên kết, tất cả vùng nghi vấn có kết quả hoặc lý do chưa xác minh. Dossier nhân vật/sự kiện/nguyên nhân/hậu quả, chứng cứ timecode, phân biệt diễn giải. Không khẳng định nhận dạng khuôn mặt người thật từ ảnh; tên nhân vật dựa vào phim/lời gọi/credit hoặc nguồn văn bản. |
| QC3 — Kịch bản | 20 | V1/V2 riêng; ngôi thứ ba, hook có thật, 6 logic kể chuyện, trình tự hợp lý, không bịa động cơ hoặc số liệu, tên thống nhất, mọi bổ sung từ web có nguồn đọc được và căn cứ phim; độ dài phù hợp mục tiêu. Lưu audit. |
| QC4 — Giọng đọc | 24 | Đủ segment và đúng text, tín hiệu/duration/samplerate/peak, ghép theo mẫu, ASR ngược 2 model và chọn candidate có căn cứ, tên riêng chưa chắc được ghi cờ. Giữ master Final và timeline. Nghe thực tế chỉ khi có khả năng; nếu không, ghi chưa nghe. |
| QC5 — Timeline | 28 | Mỗi đơn vị lời kể có clip(s) và lý do chọn; không lẫn nguồn, source bounds hợp lệ, frame intervals liên tục, duration audio-video sai lệch trong dung sai một frame, reuse/cross-cut có cờ. Dựng không phụ thuộc điểm cắt keyword-only. |
| QC6 — Hình ảnh bản dựng | 32 | Đọc ảnh đầu–giữa–cuối của từng clip; ghi batch ID/coverage; kiểm tra flagged trước rồi toàn bộ; clip sửa có ảnh từ bản render mới. Phân biệt cut cùng hành động với cut sai ngữ nghĩa. Nêu rõ không phải xem chuyển động liên tục nếu chỉ lấy mẫu. |
| QC7 — Hậu kỳ | 36 | Subtitle text đầy đủ, cue time không overlap; mẫu trước/sau xử lý subtitle gốc (rời hoặc ghi cứng), đo LUFS/true peak, track lengths, không clipping, music rights/original, ducking, tệp riêng. Ghi mất hình do crop, chữ chưa xác minh, không nghe nếu chưa nghe. |
| QC8 — Thành phẩm | 39 | FFprobe codec/fps/width/height/duration/nb_frames và decode đầy đủ; so frame count timeline; thử cue midpoint và các nối đang có chữ, xác nhận logo đúng file/kênh ở đầu giữa cuối, audio hash khi copy; check source preserved, output path, bytes, SHA256. Không tuyên bố đã kiểm tra mọi frame nếu chỉ mẫu. |

## Ngưỡng đề xuất (thay đổi theo profile)
- Không bỏ sót ID hoặc clip không có timestamp; không có gap/overlap trên timeline review trừ transition được mô hình hóa rõ ràng. Nguồn in/out trong duration nguồn. Sai lệch tổng thời lượng hình/tiếng tối đa một frame, trừ codec padding đã giải thích. Không nhầm tổng thời lượng đúng với khớp ngữ nghĩa.
- Kiểm tra subtitle nguyên văn, tối đa 2 dòng, thời lượng đủ đọc; đánh dấu cue ngắn <1s hoặc >25 ký tự/s để rà soát, không bắt buộc cắt sai câu để đạt ngưỡng. Kiểm tra chữ không tràn/cắt dấu. Có thể kiểm tra pixel presence nhưng không coi là OCR/chứng minh đúng văn bản.
- Nhạc nền mặc định thấp hơn lời đọc rõ rệt; hướng tới voice khoảng -17 đến -19 LUFS và bed khoảng -30 đến -35 LUFS, peak bản phối <= -1 dBTP, điều chỉnh theo profile và đo thực. Không coi giá trị gain đặt vào là phép đo đầu ra. Nếu áp limiter/gain chung, giữ đồng bộ stem.
- Cờ kỹ thuật không mặc nhiên là lỗi nội dung: cross-cut cùng sự kiện, reuse có chủ ý cho hook/hồi tưởng, ASR số/đồng âm, có thể giữ nếu lý do rõ.

## Khi thất bại
Ghi lỗi và scope; tìm nguyên nhân; chỉ chạy lại phần phụ thuộc; giữ bản cũ; kiểm tra lại cả vùng sửa lẫn giáp ranh; cập nhật fingerprint và state. Nếu không đủ quyền, không tự chạy ở thiết bị khác. Nếu user chấp nhận hạn chế, ghi accepted_with_limitations (trạng thái bước partial hoặc pass kèm phạm vi chấp nhận rõ). Không coi kiểm tra kỹ thuật là xác nhận quyền sử dụng/đủ điều kiện kiếm tiền YouTube.
