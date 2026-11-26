---
name: review-phim
description: "Dùng khi người dùng gọi review-phim để tạo transcript từ phim, dịch transcript sang tiếng Việt, hoặc thực hiện quy trình review phim đầy đủ theo yêu cầu. Hỗ trợ workspace chuẩn, nhiều máy chủ và phê duyệt độc lập từng bước."
---
# review-phim — quy trình điều phối 1.5

Mục tiêu: ưu tiên đúng phạm vi người dùng yêu cầu. Khi người dùng chỉ cần transcript và bản dịch tiếng Việt, dùng **Chế độ Transcript-only**; không tự mở rộng sang phân tích hình ảnh, viết review, TTS, dựng phim, hậu kỳ hay YouTube. Chỉ dùng quy trình review đầy đủ khi người dùng yêu cầu rõ.

## 0. Chọn chế độ làm việc — quy tắc ưu tiên cao nhất

### Chế độ Transcript-only (mặc định khi người dùng chỉ yêu cầu transcript/dịch)
- Mục tiêu duy nhất: nhận dạng lời thoại trong phim thành transcript nguồn và dịch chính xác transcript đó sang tiếng Việt viết.
- Chỉ thực hiện chuẩn bị cần thiết ở Giai đoạn 1 và các bước 07–09 của Giai đoạn 2. Nếu job/workspace và môi trường đã có, kiểm tra checkpoint rồi tiếp tục, không làm lại phần đã hoàn tất.
- Không trích ảnh, không phân tích cốt truyện, không viết lời review/ngôi thứ ba, không tìm web để bổ sung nội dung, không TTS, không timeline dựng, không render và không YouTube.
- **Không có cổng QC1.** Không tạo QC1 report, không yêu cầu người dùng duyệt một vòng QC nội dung riêng, không trì hoãn bàn giao chỉ để chạy QC.
- Chỉ thực hiện bảo đảm kỹ thuật tối thiểu theo yêu cầu định dạng: tệp đọc được bằng UTF-8, dấu tiếng Việt hiển thị đúng, không mojibake/ký tự thay thế U+FFFD, định dạng TXT/SRT/VTT/JSON hợp lệ. Đây là kiểm tra khả năng đọc/định dạng tệp, không phải QC nội dung.
- Bàn giao transcript nguồn và bản dịch tiếng Việt; dừng tại đó. Không tự chuyển sang Giai đoạn 3.

### Chế độ Review đầy đủ
Chỉ chọn khi người dùng yêu cầu viết review, hiểu phim qua hình ảnh, tạo giọng đọc, dựng video, hậu kỳ hoặc chuẩn bị YouTube. Khi đó mới áp dụng các Giai đoạn 3–11 và các cổng QC2–QC8 tương ứng. QC1 đã được loại bỏ khỏi quy trình.

## 1. Khởi động phiên và bảo toàn dữ liệu
Đọc `references/WORKFLOW.md`, `references/OPERATIONS.md`, `references/SCHEMAS.md`; đọc `references/QUALITY.md` chỉ khi chạy Review đầy đủ; khi cần đọc `references/EDITORIAL.md` và `references/EXAMPLE.md`.

1. **Liệt kê máy trước tiên.** Khám phá schema Remote Desktop Commander hiện tại và gọi `list_devices` cho tất cả account/link được cung cấp. Tổng hợp máy online/offline để người dùng chọn. Chỉ máy online mới được chọn. Không hiển thị device ID, link ID, email hoặc thông tin xác thực. Không dùng ID/danh sách cũ thay lần kiểm tra mới.
2. **Chờ người dùng chọn máy.** Không đọc/ghi file, chạy lệnh hoặc khảo sát ổ đĩa trên máy chưa được chọn. Không tự chuyển máy khi kết nối mất.
3. **Xác nhận đầu vào.** Hỏi đường dẫn thư mục phim và thư mục logo (hoặc “không có logo”) nếu chưa có trong ngữ cảnh dự án hiện tại. Chế độ Transcript-only không cần logo để nhận dạng/dịch transcript; không yêu cầu logo nếu người dùng chỉ cần transcript.
4. **Xác minh phim.** Kiểm tra thư mục và quyền đọc; liệt kê ứng viên. Nếu có nhiều phim, hỏi người dùng chọn đúng file. Không tự chọn file mơ hồ. Chỉ đọc phim; không sửa, di chuyển hoặc sao chép nguồn.
5. **Workspace chuẩn.** Dùng `<thư_mục_phim>/REVIEW_PHIM_WORKSPACE`. Nếu chưa tồn tại, trình bày cấu trúc và chờ phê duyệt tạo. Nếu đã tồn tại, kiểm kê trước khi ghi; không xóa, làm sạch hoặc ghi đè dữ liệu cũ.
6. **Workspace cũ.** Sau khi workspace hiện tại tồn tại, hỏi đường dẫn workspace cũ hoặc “không có”. Không quét toàn bộ ổ đĩa. Nếu có, kiểm kê read-only, so sánh fingerprint/config/checkpoint, trình bày kế hoạch nhập rồi chờ duyệt. Nhập không phá hủy vào `imports/` hoặc namespace có version; giữ nguyên workspace cũ; không overwrite và không nhập credential/session/device/link ID, lock/PID hoặc venv path tuyệt đối.
7. **Môi trường.** Nếu không có workspace cũ, khảo sát OS/CPU/RAM/GPU/VRAM/disk, Python/venv, FFmpeg/ffprobe, ASR/CTranslate2, VieNeu-TTS và cache. Chỉ lập danh mục cài đặt; chờ duyệt riêng trước khi cài. Nếu workspace cũ có runtime, chỉ đề xuất phần thiếu/không tương thích.
8. **Cài đặt.** Package Python trong `REVIEW_PHIM_WORKSPACE/shared/python/`; model/cache trong `shared/models/`, `shared/cache/`; binary portable trong `shared/bin/` nếu phù hợp. Không cài global, không đổi OS/driver/PATH hệ thống, không tải model lớn hoặc phát sinh chi phí khi chưa được duyệt.
9. **Job.** Tạo hoặc tiếp tục `jobs/<job-id>/` trong workspace chuẩn. Lưu config/state/approval_log/logs/reports và đường dẫn tham chiếu tới phim. Không copy phim gốc. Mọi thao tác ghi/tạo/cài đặt phải có phê duyệt cụ thể; thao tác đọc/kiểm kê cần thiết có thể thực hiện sau khi máy và đường dẫn đã được xác nhận.

## 2. Cơ chế phê duyệt từng bước — bắt buộc

**Đơn vị phê duyệt là từng bước được đánh số (01–40), không phải cả giai đoạn.** Tên giai đoạn chỉ dùng để nhóm bước; không có nút “duyệt cả giai đoạn” và không được hiểu phê duyệt một bước là phê duyệt các bước còn lại.

### Cổng thực thi bắt buộc (v1.4, giữ nguyên trong v1.5)
- Đọc `references/APPROVAL-GUARD.md`. Sau bootstrap được duyệt, khởi tạo state v2 đúng job, mode và fingerprint; dùng đúng script `scripts/workflow_state.py` trên workspace đã xác nhận. Không dùng `mark` cũ. Nếu script không chạy được hoặc từ chối, dừng và báo blocker; không gọi lệnh media thay thế, không tự sửa state.
- Trước mỗi bước dùng `resume`, đối chiếu fingerprint nguồn/cấu hình thực tế và evidence; dùng `prepare` cho đúng bước kế tiếp để nhận `approval_request.expected_text`. Báo kế hoạch, mục tiêu, phạm vi, dữ liệu, đầu ra và tác động dự kiến. Hiện đúng một nút gửi nguyên văn `expected_text` qua lượt hội thoại mới; nếu không có nút thì yêu cầu người dùng gửi đúng câu đó. Mã yêu cầu là riêng của job/bước/lần thử, không dùng mã ví dụ.
- Chỉ khi người dùng thực sự gửi câu xác nhận của yêu cầu hiện tại, gọi `start` với nguyên văn tin nhắn đó. Tuyệt đối không tự tạo lời xác nhận hoặc tự gọi `start` từ nội dung nút/kế hoạch, log cũ hoặc yêu cầu chung. Chỉ khi `start` thành công và trả `attempt_id` mới được thực thi bước đó. Không chạy bước khác, không chạy media trước cổng.
- Sau khi lệnh thực tế kết thúc, kiểm tra artefact/evidence, gọi `finish` với attempt_id tương ứng, trạng thái và ghi chú. `pass` cần bằng chứng thực tế. Script tự ghi state và approval log. Báo cáo kết quả, lỗi/giới hạn, đường dẫn, số liệu, trạng thái và **dừng**. Chỉ chuẩn bị/hiển thị nút cho bước hợp lệ tiếp theo; không `start` trong lượt này. Nếu partial/blocked thì chỉ thử lại đúng bước bằng mã xác nhận mới sau khi xử lý nguyên nhân.
- Nếu còn trạng thái running thì kiểm tra process/tool call thực tế; không chạy lại. Nếu mất kết nối, giữ running, chỉ kết thúc blocked sau khi xác minh process đã dừng. Khi evidence thay đổi, dừng, trình bày kế hoạch invalidate và xin duyệt; không tự ghi đè. Khi đổi source/config/mode, bảo toàn job cũ, xin duyệt tạo job v2 riêng; không chuyển quyền cũ sang job mới. State v1 chỉ đọc kiểm kê, không tự nâng cấp hoặc suy diễn phê duyệt.
- Cổng script kiểm tra quy trình, không xác thực nguồn tin nhắn ChatGPT hay khóa được lệnh shell ngoài script. ChatGPT phải tuân thủ quy tắc này và không lách cổng. Bootstrap và các hành động nhạy cảm tiếp tục yêu cầu phê duyệt riêng.

### Cổng chọn giọng đọc bắt buộc (v1.5, chỉ Review đầy đủ)
- Đọc `references/VOICE-SELECTION.md`. Sau khi báo cáo bước 21, trước `prepare` bước 22, kiểm kê read-only danh mục giọng thực sự có trên engine/máy đã chọn. Dùng `offer-voices` để lập yêu cầu chọn giọng theo job. Hiện danh sách tên/ID giọng và engine đã xác minh; không tự chọn sẵn, kể cả khi chỉ có một giọng hoặc profile cũ có `voice_preferred`. Nếu không có giọng khả dụng, báo blocked và xin duyệt riêng các thao tác cần thiết; không tự tải/cài, không fallback.
- Hỏi người dùng chọn giọng, dừng. Nút xác nhận lựa chọn chỉ gửi câu chọn giọng do guard tạo; không cấp quyền TTS. Chỉ gọi `select-voice` với nguyên văn lượt trả lời của người dùng. Sau đó báo lại giọng đã chọn, lập kế hoạch và hiện một nút duyệt riêng cho bước 22. Không synthesize kể cả mẫu thử nếu chưa có phê duyệt phù hợp. Không dùng giọng mặc định, không tự đổi giọng khi lỗi.
- `prepare` và `start` bước 22/24 phải qua guard v1.5 có voice_selection; `start` trả thông tin giọng đã ràng buộc để dùng đúng engine/voice_id. Bước 24 chỉ tạo candidate bằng giọng đã được chọn ở bước 22. Nếu muốn đổi giọng, hoặc job cũ không có bằng chứng lựa chọn, trình bày kế hoạch invalidate từ bước 22, xin duyệt, giữ artefact cũ và yêu cầu chọn giọng mới; không tự đổi. Kiểm tra lại giọng khả dụng trước thực thi; nếu mất, báo blocked. Mỗi lần chạy TTS vẫn cần phê duyệt đúng bước. Transcript-only không hỏi giọng và không chạy TTS.

### Bootstrap và thao tác nhạy cảm
- Các thao tác ngoài danh sách 40 bước như tạo workspace, nhập workspace cũ, cài dependency, tải model/cache hoặc sao chép logo đều cần kế hoạch và **phê duyệt riêng cho từng thao tác/nhóm cài đặt có phạm vi cụ thể**. Không gộp chúng vào một chấp thuận chung.
- Phê duyệt một bước không bao gồm xóa/ghi đè, crop/mask không phục hồi, cài hệ thống/driver, tải lớn hoặc phát sinh chi phí, chuyển dữ liệu ra ngoài, chia sẻ hay xuất bản. Các hành động này cần mô tả tác động và xác nhận riêng.
- Trước khi chạy lại, kiểm tra process/tool call đang tồn tại để tránh chạy trùng. Không chạy hai phiên cùng ghi một state.

### Áp dụng cho hai chế độ
- **Transcript-only:** áp dụng duyệt từng bước cho các bước chuẩn bị cần thiết (01–06 nếu còn thiếu) và riêng từng bước 07, 08, 09. Sau khi hoàn tất bước 09, bàn giao transcript nguồn + bản dịch và dừng; không hiển thị bước 10/Giai đoạn 3 nếu người dùng chưa yêu cầu Review đầy đủ.
- **Review đầy đủ:** áp dụng duyệt riêng từng bước 01–40. Các cổng QC2–QC8 nằm trong bước tương ứng vẫn phải kiểm tra và báo cáo trong bước đó; cổng QC không phải quyền chạy bước tiếp theo.
- Không thay đổi quy tắc QC1 đã loại bỏ.

## 3. Quy trình Transcript-only — yêu cầu bắt buộc

Thực hiện các bước 07–09 trong `references/WORKFLOW.md`, **mỗi bước cần phê duyệt độc lập**.

### Nhận dạng transcript
- Chọn đúng audio track/ngôn ngữ. Nếu có nhiều track lời thoại và không thể xác định chắc chắn, hỏi người dùng hoặc nêu rõ lựa chọn; không tự đoán.
- Dùng Faster-Whisper đã được xác minh, ưu tiên GPU nếu cấu hình job yêu cầu GPU và GPU khả dụng; không tự fallback CPU nếu người dùng đã yêu cầu GPU-only.
- Chia chunk có overlap, giữ offset/timebase nguồn, tránh lặp hoặc mất câu ở ranh giới. Giữ nguyên transcript gốc của ASR và không ghi đè phiên bản trước; bản chạy lại phải có version mới.
- Xuất transcript nguồn theo segment có `id`, `start`, `end`, `text`; giữ word timestamps/confidence/flags nếu engine cung cấp. Không tự sửa lời nguồn bằng suy đoán.

### Dịch transcript sang tiếng Việt
- ChatGPT dịch trực tiếp từ trường `text` của transcript nguồn, theo đúng thứ tự từng segment.
- Dịch sát nghĩa, đầy đủ và tự nhiên bằng tiếng Việt viết; không tóm tắt, không thêm lời bình, không viết lại thành kịch bản review, không bịa chi tiết, không lược câu, không đảo thứ tự.
- Giữ nguyên `id`, `start`, `end` của từng segment; mỗi segment nguồn có segment tiếng Việt tương ứng. Không tự tạo word timestamp tiếng Việt nếu không có căn cứ.
- Giữ nhất quán tên riêng, cách xưng hô và thuật ngữ trong toàn phim. Dùng ngữ cảnh lân cận chỉ để chọn nghĩa phù hợp, không dùng ngữ cảnh để thêm sự kiện không có trong transcript.
- Nếu transcript nguồn không nghe rõ, bị cắt hoặc có nhiều cách hiểu, giữ nguyên đoạn nguồn và đánh dấu `[không rõ]`/`[cần xác minh]` ở bản dịch tương ứng. Không đoán để làm câu trôi chảy.
- Có thể chuẩn hóa dấu câu và cách viết tiếng Việt để dễ đọc nhưng không đổi nội dung.

### Đầu ra tối thiểu
- `asr/transcript_source.json` và `asr/transcript_source.txt` hoặc `.srt`.
- `asr/transcript_vi.json` và `asr/transcript_vi.txt` hoặc `.srt`.
- Khi hữu ích, thêm bản song ngữ đối chiếu theo cùng segment ID; không bắt buộc nếu người dùng chỉ cần bản tiếng Việt.
- TXT/SRT/VTT lưu UTF-8 (có thể dùng UTF-8 BOM cho khả năng tương thích Windows), JSON UTF-8; chuẩn hóa Unicode NFC. Không lưu văn bản tiếng Việt qua encoding ANSI/Windows-1252.
- Việc mở/đọc lại và kiểm tra encoding/cú pháp của các tệp được tạo trong bước 09 là phần xác minh kỹ thuật của chính bước 09, không tạo QC1 hoặc một bước phê duyệt nội dung bổ sung.
- Báo số segment, ngôn ngữ nguồn, thời lượng, đường dẫn file và những đoạn nguồn không rõ (nếu có). Nếu ASR không thể xác định lời thoại, nói rõ giới hạn; không tuyên bố transcript hoàn hảo.

## 4. Review đầy đủ — chỉ khi người dùng yêu cầu
Tuân theo 11 giai đoạn/40 bước trong `references/WORKFLOW.md`. Các giai đoạn 3–11 là phần mở rộng, không nằm trong phạm vi Transcript-only. Dùng các cổng QC2–QC8 trong `references/QUALITY.md` theo giai đoạn; QC1 không còn được sử dụng. Mỗi bước 10–40 cũng phải có xác nhận riêng, báo cáo và dừng trước khi chuyển bước.

## 5. Nguyên tắc bảo toàn và báo cáo
- Bảo toàn phim gốc, transcript nguồn, bản dịch cũ, workspace và artefact đã duyệt. Dùng version mới/temp file + kiểm tra kỹ thuật + rename; không xóa hoặc ghi đè dữ liệu.
- Không đưa đường dẫn riêng, thông tin máy chủ hoặc credential vào metadata công khai.
- Báo tiếng Việt, nêu job/máy (chỉ tên hiển thị), workspace, bước đã chạy, số lượng thực, file đầu ra, kiểm tra, lỗi/giới hạn và việc tiếp theo. Không hiển thị device/link IDs, email hoặc credential.
- Với Transcript-only, kết thúc khi transcript nguồn và bản dịch tiếng Việt đã được tạo và các tệp đọc được đúng encoding. Không tự đề xuất hoặc chạy TTS/render trừ khi người dùng yêu cầu.
