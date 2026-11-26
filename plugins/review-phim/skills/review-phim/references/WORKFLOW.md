# Quy trình review-phim 1.5 — Transcript-first, phê duyệt từng bước

Quy trình có hai chế độ:
- **Transcript-only:** mặc định khi người dùng chỉ yêu cầu transcript/phụ đề và bản dịch tiếng Việt. Chỉ chạy chuẩn bị cần thiết (nếu chưa có) và Giai đoạn 2, sau đó bàn giao và dừng.
- **Review đầy đủ:** chỉ chạy khi người dùng yêu cầu viết review, phân tích hình ảnh, TTS, dựng/hậu kỳ hoặc YouTube; khi đó mới tiếp tục Giai đoạn 3–11.

**QC1 đã được loại bỏ.** Giai đoạn 1 không có QC1; Giai đoạn 2 cũng không có cổng QC1. Transcript-only chỉ có bảo đảm kỹ thuật định dạng/encoding để tránh lỗi font tiếng Việt, không có vòng QC nội dung riêng.

## Khởi động phiên (trước bước 01)
A. Liệt kê thiết bị bằng `list_devices` cho tất cả account/link có trong schema công cụ hiện tại; hiển thị tên và online/offline, không hiển thị ID/email. Chỉ máy online được chọn.
B. Chờ người dùng chọn máy. Không đọc/ghi/chạy lệnh trên máy chưa chọn.
C. Xác nhận thư mục phim và file phim cụ thể. Chỉ hỏi thư mục logo nếu Review đầy đủ cần logo; Transcript-only không cần logo.
D. Workspace chuẩn là `<film_dir>/REVIEW_PHIM_WORKSPACE`. Nếu chưa có, trình bày cấu trúc và chờ duyệt tạo; nếu đã có, kiểm kê read-only và dùng lại, không xóa/ghi đè.
E. Hỏi workspace cũ hoặc “không có”; không quét toàn bộ ổ đĩa. Nếu có, kiểm kê read-only, so sánh fingerprint/config/checkpoint, trình bày kế hoạch nhập và chờ duyệt. Nhập không phá hủy, không overwrite, giữ nguyên workspace cũ; không nhập credential/session/device/link IDs, lock/PID hoặc absolute venv paths.
F. Nếu không có workspace cũ, khảo sát OS/CPU/RAM/GPU/VRAM/disk, Python/venv, FFmpeg/ffprobe/encoder, thư viện media, ASR/CTranslate2, VieNeu-TTS và cache. Lập danh mục cài đặt có phiên bản, vị trí, dung lượng và nguồn/license nếu biết; chờ duyệt trước khi cài.
G. Cài package Python trong `shared/python/`, model/cache trong `shared/models/` và `shared/cache/`, binary portable trong `shared/bin/`. Không cài global, không đổi OS/driver/PATH hệ thống, không tải lớn hoặc phát sinh chi phí khi chưa duyệt.
H. Tạo/tiếp tục job tại `jobs/<job-id>/`; không copy phim gốc. Mọi thao tác ghi/tạo/cài đặt đều cần phê duyệt riêng.

## Phê duyệt từng bước
Tuân thủ `../SKILL.md` và `APPROVAL-GUARD.md`: mỗi bước 01–40 là một đơn vị phê duyệt. Sau bootstrap đã duyệt, dùng `resume` → `prepare` → hiển thị duy nhất một nút gửi nguyên văn `expected_text` → chờ lượt người dùng → `start` → chỉ thực hiện bước đã được cấp `attempt_id` → kiểm tra evidence → `finish` → báo cáo → dừng. Không gọi `start` cho bước sau trong cùng lượt. Partial/blocked phải thử lại đúng bước với yêu cầu mới; running phải xác minh process thực tế; evidence đổi phải dừng và xin duyệt invalidate. Không dùng lệnh `mark` cũ, không tự tạo lời phê duyệt. Transcript-only kết thúc ở bước 09; full-review kết thúc ở 40, bước 40 chỉ thực hiện nếu người dùng yêu cầu YouTube (nếu không, xin duyệt ghi skipped có lý do). Bootstrap, cài đặt, tải lớn, xóa/ghi đè, crop không phục hồi, chia sẻ/xuất bản vẫn cần phê duyệt riêng. Không QC1.

## Giai đoạn 1 — Tiếp nhận và chuẩn bị (01–06)
01. Xác minh máy đã chọn còn online; xác minh thư mục/file phim và quyền đọc; nếu Review đầy đủ thì xác minh thêm logo. Xác định job hiện tại hoặc đề xuất job mới.
02. Chạy ffprobe để đọc streams, duration, fps, kích thước, audio/subtitle tracks; ghi fingerprint nguồn (size, mtime, SHA256 nếu khả thi). Không sửa nguồn.
03. Tạo/kiểm tra job folder, config, state, approval_log, logs và reports; lưu đường dẫn tham chiếu đến phim, không sao chép phim.
04. Kiểm tra Python/venv, FFmpeg/ffprobe và thư viện cần cho ASR. Chỉ cài thành phần thiếu trong venv workspace đã duyệt; cài đặt phải có phê duyệt bootstrap riêng.
05. Kiểm tra Faster-Whisper/CTranslate2, model cache và runtime. Nếu user yêu cầu GPU-only, xác minh GPU và dừng nếu GPU không sẵn sàng; không tự fallback CPU.
06. Chạy smoke test tối thiểu phù hợp phạm vi đã duyệt (decode audio và ASR runtime; GPU tensor nếu yêu cầu). Ghi environment report. Đây là chuẩn bị môi trường, không phải QC transcript.

**Mỗi bước 01–06 phải được duyệt, thực thi, xác minh và báo cáo riêng.** Nếu cần tạo workspace, nhập workspace hoặc cài package, các thao tác đó còn cần phê duyệt bootstrap riêng; phê duyệt bước không tự động bao gồm chúng.

## Giai đoạn 2 — Transcript và dịch tiếng Việt (07–09)
07. Giải mã đúng audio track sang PCM mono 16 kHz hoặc định dạng đầu vào phù hợp model. Giữ timebase/offset của nguồn; nếu có nhiều track lời thoại và không xác định được track đúng, hỏi người dùng.
08. Faster-Whisper nhận dạng toàn bộ phim theo chunk có overlap. Ghép timestamp về timeline nguồn, xử lý biên chunk không lặp/mất câu, giữ segment ID ổn định và lưu transcript nguồn. Không tự sửa câu bằng suy đoán. Xuất JSON và TXT/SRT/VTT nếu được yêu cầu.
09. ChatGPT dịch từng segment trực tiếp từ transcript nguồn sang tiếng Việt viết. Giữ nguyên ID/start/end/thứ tự; không tóm tắt, không thêm/bớt, không biến thành văn kể review. Giữ nhất quán tên riêng/xưng hô; chỗ nguồn không rõ thì đánh dấu `[không rõ]` hoặc `[cần xác minh]`, không đoán. Xuất `transcript_vi.json` và TXT/SRT/VTT tương ứng. Trong chính bước 09, mở/đọc lại tệp và kiểm tra UTF-8/NFC, U+FFFD/mojibake và cú pháp container; không tạo QC1.

**Mỗi bước 07, 08 và 09 cần phê duyệt độc lập.** Sau bước 09, báo cáo và bàn giao transcript nguồn + bản dịch tiếng Việt. Nếu người dùng chỉ yêu cầu transcript, dừng hẳn; không hiển thị bước 10.

## Giai đoạn 3 — Hình ảnh (10–12, chỉ Review đầy đủ)
10. Trích ảnh toàn phim theo khoảng mặc định 5 giây, lưu timestamp thực và index.
11. ChatGPT quan sát ảnh theo batch, ghi frame ID, hành động, bối cảnh, vai trò nhân vật và điểm chưa rõ.
12. Đối chiếu ảnh với transcript theo thời gian, lập visual-transcript timeline. QC2 chỉ áp dụng trong Review đầy đủ.

## Giai đoạn 4 — Hiệu đính hiểu phim (13–16, chỉ Review đầy đủ)
13. Khoanh vùng transcript thiếu/confidence thấp/tên riêng sai và mâu thuẫn hình ảnh.
14. Nhận dạng lại các vùng có vấn đề, lưu candidate riêng, không ghi đè transcript nguồn.
15. Trích ảnh bổ sung ở vùng cần xác minh và đối chiếu lời thoại.
16. Lập dossier nhân vật/sự kiện/nguyên nhân/hậu quả/chủ đề với timecode chứng cứ. QC2.

## Giai đoạn 5 — Kịch bản (17–20, chỉ Review đầy đủ)
17. Viết V1 ngôi thứ ba từ dossier theo `EDITORIAL.md`.
18. Tra cứu nguồn chính thức/đáng tin để xác nhận phim, phiên bản và tình tiết.
19. Đối chiếu nguồn ngoài với phim gốc; ưu tiên phim khi mâu thuẫn.
20. Biên tập V2, giữ V1 và audit. QC3.

## Giai đoạn 6 — Giọng đọc (21–24, chỉ Review đầy đủ)
21. Chia kịch bản thành đoạn/câu, giữ ID và nguyên văn.

**Cổng bắt buộc giữa bước 21 và 22:** báo cáo bước 21, chỉ kiểm kê giọng khả dụng; hiển thị danh sách không chọn sẵn, hỏi người dùng chọn giọng và dừng. Ghi nhận lựa chọn qua `offer-voices` / `select-voice`. Sau khi chọn xong, mới `prepare` bước 22, hiển thị nút phê duyệt riêng và chờ xác nhận. Không tạo audio, kể cả mẫu, trước khi có lựa chọn và quyền thực thi phù hợp. Xem `VOICE-SELECTION.md`.

22. Tạo TTS bằng engine và voice_id được người dùng chọn rõ qua cổng `VOICE-SELECTION.md`, sau phê duyệt riêng bước 22; kiểm tra giọng khả dụng, lưu WAV từng đoạn và master, không fallback/default.
23. Dùng ASR ngược làm chỉ báo sai khác, không coi là nghe trực tiếp.
24. Tạo candidate sửa bằng đúng giọng đã chọn tại bước 22, chọn bản có căn cứ, ghép Final và timeline. Nếu muốn đổi giọng, xin duyệt invalidate từ bước 22 rồi chọn lại; không tự đổi. QC4.

## Giai đoạn 7 — Timeline hình ảnh (25–28, chỉ Review đầy đủ)
25. Chia lời đọc Final theo đơn vị ngữ nghĩa và căn thời gian.
26. Phát hiện cảnh bằng FFmpeg/PySceneDetect; lưu scene database.
27. ChatGPT chọn cảnh dựa trên ảnh chứng cứ và ngữ nghĩa, không keyword-only/ngẫu nhiên.
28. Tạo timeline theo frame, kiểm tra source bounds, duration, reuse/cross-cut. QC5.

## Giai đoạn 8 — Dựng và kiểm duyệt (29–32, chỉ Review đầy đủ)
29. Dựng thử hook và kiểm tra mẫu.
30. Render proxy, kiểm tra frame/audio/concat.
31. ChatGPT xem ảnh đại diện các clip bị cờ, ghi retain/revise/verify.
32. Kiểm tra các clip còn lại, sửa và render version mới. QC6. Không tuyên bố xem chuyển động liên tục nếu chỉ xem still.

## Giai đoạn 9 — Hậu kỳ (33–36, chỉ Review đầy đủ)
33. Tạo phụ đề theo lời đọc Final và timecode.
34. Xử lý subtitle gốc đúng loại; không nhầm chữ bối cảnh/logo/credit.
35. Dùng nhạc nguyên bản hoặc nguồn có quyền; giữ stem riêng.
36. Cân âm, ducking, đo LUFS/true peak và lưu các stem/mix. QC7.

## Giai đoạn 10 — Xuất phim và logo (37–39, chỉ Review đầy đủ)
37. Render final theo profile, giữ version cũ và layer.
38. ffprobe/decode, kiểm tra frame/audio/subtitle và sửa lỗi bằng version mới.
39. Dùng đúng logo đã chọn, giữ tỷ lệ/alpha; nếu không yêu cầu logo thì bỏ qua có ghi chú. QC8.

## Giai đoạn 11 — Nội dung YouTube (40, chỉ khi người dùng yêu cầu)
40. Chuẩn bị title, thumbnail, description, CTA, hashtag và nguồn. Không tự đăng nếu không có yêu cầu rõ.

## Báo cáo sau mỗi bước
Báo cáo phải nêu: job và bước vừa thực hiện; trạng thái; đầu vào/đầu ra; đường dẫn và kích thước artefact; số liệu thực; kiểm tra đã chạy; cảnh báo/lỗi/giới hạn; fingerprint nếu liên quan; approval/checkpoint đã ghi. Không tuyên bố hoàn thành nếu thiếu bằng chứng. Sau báo cáo, chỉ hiện nút duyệt cho bước kế tiếp hợp lệ.
