# Các cổng chất lượng cho chế độ Review đầy đủ

**QC1 đã được loại bỏ khỏi quy trình.** Không có QC1 ở Giai đoạn 1 hoặc Giai đoạn 2. Khi người dùng chỉ yêu cầu transcript và dịch tiếng Việt, không chạy bất kỳ cổng QC nội dung nào; chỉ kiểm tra kỹ thuật tệp để bảo đảm UTF-8, dấu tiếng Việt hiển thị đúng và định dạng TXT/SRT/VTT/JSON đọc được. Kiểm tra định dạng này không phải QC và không cần người dùng phê duyệt riêng.

Các cổng dưới đây chỉ áp dụng khi người dùng yêu cầu Review đầy đủ và thực hiện các giai đoạn tương ứng. `pass` chỉ có nghĩa đạt phạm vi đã công bố, không phải chính xác tuyệt đối; `partial` là còn việc; `blocked` là thiếu dữ liệu/khả năng; `stale` là đầu vào đã đổi. Không tự nâng partial thành pass.

| Cổng | Sau bước | Phạm vi |
|---|---:|---|
| QC2 — Hiểu phim | 16 | Coverage ảnh theo ID, transcript liên kết, vùng nghi vấn có kết quả/lý do chưa xác minh; dossier nhân vật/sự kiện/nguyên nhân/hậu quả và timecode chứng cứ. Không nhận dạng danh tính người thật từ ảnh. |
| QC3 — Kịch bản | 20 | V1/V2 riêng; ngôi thứ ba, trình tự hợp lý, hook có thật, không bịa động cơ/số liệu, tên nhất quán; bổ sung web có nguồn đọc được. |
| QC4 — Giọng đọc | 24 | Đủ segment, đúng text, tín hiệu/duration/sample rate/peak; ASR ngược là chỉ báo, không thay nghe thật. |
| QC5 — Timeline | 28 | Mỗi đơn vị lời kể có clip và lý do chọn; source bounds hợp lệ, frame liên tục, duration A/V trong dung sai, reuse/cross-cut có cờ. |
| QC6 — Hình ảnh bản dựng | 32 | Ảnh đầu–giữa–cuối từng clip, batch coverage, clip bị cờ và clip đã sửa; nêu rõ nếu chỉ lấy mẫu still. |
| QC7 — Hậu kỳ | 36 | Subtitle đầy đủ/không overlap, xử lý subtitle gốc, LUFS/true peak, track lengths, clipping, nguồn nhạc/quyền sử dụng và các stem. |
| QC8 — Thành phẩm | 39 | FFprobe/decode, codec/fps/kích thước/duration/frame count, cue midpoint/nối, logo đúng file, source preserved, output path/bytes/SHA256. Không tuyên bố kiểm tra mọi frame nếu chỉ lấy mẫu. |

## Nguyên tắc khi QC đầy đủ được yêu cầu
- Mỗi cổng có thể lưu JSON/Markdown gồm job_id, gate, status, input/output fingerprints, phương pháp, phạm vi, metrics, issue IDs, evidence, quyết định, giới hạn và thời gian.
- Không dùng kiểm tra kỹ thuật để khẳng định độ chính xác ngữ nghĩa hoặc quyền sử dụng/đủ điều kiện kiếm tiền YouTube.
- Khi thất bại, ghi lỗi/phạm vi, sửa đúng phần phụ thuộc, giữ bản cũ, kiểm tra lại vùng sửa và vùng giáp ranh, cập nhật fingerprint/state.
- Nếu người dùng chỉ muốn transcript, dừng sau khi đã tạo transcript nguồn và bản dịch tiếng Việt; không mở các cổng QC2–QC8.
