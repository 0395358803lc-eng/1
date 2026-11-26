# Quy trình review-phim 1.3 — Transcript-first, phê duyệt từng bước

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

## Cơ chế phê duyệt từng bước — áp dụng bắt buộc
1. **Mỗi số bước là một đơn vị phê duyệt riêng.** Các tiêu đề Giai đoạn 1–11 chỉ để nhóm bước, không phải phạm vi phê duyệt. Không có nút duyệt cả giai đoạn.
2. Trước từng bước, kiểm tra checkpoint và chỉ chọn bước pending tiếp theo. Nêu số bước, tên, giai đoạn, job, mục tiêu, đầu vào, thao tác, đầu ra, rủi ro và thay đổi dự kiến.
3. Hiển thị đúng **một nút** `Thực thi bước NN`. Callback phải gửi câu phê duyệt nêu rõ job, giai đoạn, số bước, phạm vi và yêu cầu dừng sau bước đó. Ví dụ:
   ```jsx
   <button block onClick={() => GenUI.issueNewTurn("PHÊ DUYỆT THỰC THI: Job <job-id>; Giai đoạn 2; Bước 08 — Nhận dạng lời thoại. Chỉ thực hiện bước 08, kiểm tra, lưu checkpoint và báo cáo; không chạy bước 09.")}>Thực thi bước 08</button>
   ```
4. Chỉ câu xác nhận rõ số bước hoặc click nút mới là phê duyệt. “Tiếp tục”, “làm đi”, “chạy toàn bộ” hoặc duyệt một giai đoạn không phải phê duyệt các bước.
5. Sau khi thực hiện **một bước duy nhất**, xác minh kết quả, cập nhật state và append-only approval log, báo `pass / partial / blocked / stale`, bằng chứng, tệp, số liệu, lỗi và giới hạn; sau đó **dừng**.
6. Chỉ sau báo cáo mới hiển thị một nút cho bước pending kế tiếp. Không chạy xuyên bước hoặc tự thực hiện bước kế tiếp dù cùng giai đoạn.
7. Nếu `partial`/`blocked`, dừng tại bước đó, giải thích blocker và chỉ đề nghị bổ sung thông tin hoặc duyệt chạy lại đúng bước. Không bỏ qua để chạy bước sau.
8. Nếu cần chạy lại bước đã `pass`, nêu lý do, dùng version/artefact mới và xin duyệt lại. Khi upstream thay đổi, đánh dấu downstream `stale`.
9. Các thao tác bootstrap ngoài danh sách 40 bước (tạo workspace, nhập workspace cũ, cài dependency, tải model/cache, copy logo) phải có kế hoạch và phê duyệt riêng theo từng thao tác/nhóm có phạm vi rõ.
10. Phê duyệt bước không bao gồm xóa/ghi đè, crop/mask không phục hồi, cài hệ thống/driver, tải lớn/chi phí, chuyển dữ liệu ra ngoài, chia sẻ hoặc xuất bản; những việc này cần xác nhận riêng.
11. Kiểm tra process/tool call đang chạy trước khi chạy lại; không có hai phiên cùng ghi state. Nếu UI không hỗ trợ nút, yêu cầu câu xác nhận rõ số bước.
12. Dùng approval log append-only; ghi approval và completion cho từng bước. Không lưu credential, email, device/link/session IDs.

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
22. Tạo TTS bằng preset/thiết bị đã xác minh; lưu WAV từng đoạn và master.
23. Dùng ASR ngược làm chỉ báo sai khác, không coi là nghe trực tiếp.
24. Tạo candidate sửa, chọn bản có căn cứ, ghép Final và timeline. QC4.

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
