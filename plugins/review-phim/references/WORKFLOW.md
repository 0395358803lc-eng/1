# Quy trình chuẩn: 11 giai đoạn · 40 bước · phê duyệt từng giai đoạn
Mỗi bước ghi checkpoint sau khi kiểm tra đầu ra. Số bước cố định, số lượng dữ liệu động theo phim. Gắn các cổng QC tại `QUALITY.md`. Không xuất bản ngoài yêu cầu.

## Khởi động phiên bắt buộc (trước bước 01, không tính vào 40 bước)
A. Liệt kê thiết bị bằng `list_devices` cho tất cả account/link hiện có trong schema công cụ của phiên; chỉ máy online có thể chọn. Luôn hiển thị danh sách máy trước khi hỏi đường dẫn. Không hiển thị device/link ID hoặc email. Chờ user chọn máy; không đọc/ghi trên máy chưa chọn.
B. Sau khi chọn máy, hỏi đường dẫn thư mục chứa phim và thư mục chứa logo (hoặc “không có logo”). Xác minh đường dẫn, quyền đọc/ghi và liệt kê file ứng viên. Nếu có nhiều phim/logo thì yêu cầu chọn đúng file.
C. Workspace chuẩn nằm ngay trong thư mục phim: `<film_dir>/REVIEW_PHIM_WORKSPACE`. Nếu chưa tồn tại, đưa kế hoạch tạo và chờ nút phê duyệt; nếu đã tồn tại, kiểm kê và dùng làm workspace hiện tại, không ghi đè/xóa.
D. Sau khi workspace hiện tại tồn tại, hỏi đường dẫn workspace `REVIEW_PHIM_WORKSPACE` cũ hoặc “không có”. Không tự quét toàn bộ ổ đĩa. Nếu workspace cũ ở máy khác, chọn máy đó trước khi đọc.
E. Có workspace cũ: kiểm kê read-only, so sánh fingerprint/config/checkpoint, đưa kế hoạch nhập và chờ duyệt. Nhập không phá hủy, giữ nguyên bản cũ, không overwrite, không nhập credentials/session IDs/lock/PID/venv path; artefact không khớp fingerprint được giữ tham khảo và đánh dấu stale. Kiểm tra runtime cũ, chỉ lập danh sách cài bổ sung nếu thiếu/không tương thích.
F. Không có workspace cũ: khảo sát OS/CPU/RAM/GPU/VRAM/disk, Python/venv, FFmpeg/ffprobe/encoders, thư viện, ASR/CTranslate2, VieNeu-TTS, model/cache. Xuất danh mục cài đặt theo nhóm, phiên bản, dung lượng, vị trí và license/nguồn nếu biết. Chờ duyệt trước khi cài.
G. Cài package Python trong venv riêng dưới `REVIEW_PHIM_WORKSPACE/shared/python/`; model/cache trong `shared/models/`, `shared/cache/`; binary portable phù hợp trong `shared/bin/`. Không cài global, không tự cập nhật driver/OS, không tải lớn hoặc phát sinh chi phí khi chưa được duyệt. Nếu workspace cũ tồn tại nhưng runtime thiếu, chỉ đề xuất phần thiếu và cũng chờ duyệt.
H. Mỗi thao tác bootstrap có nút phê duyệt riêng. Tạo job tại `REVIEW_PHIM_WORKSPACE/jobs/<job-id>/`. Không copy phim gốc vào workspace. Logo chỉ được copy nguyên trạng vào `assets/branding/<channel-id>/` sau khi user chọn file và duyệt.

## Cổng phê duyệt cho 11 giai đoạn
Trước khi chạy mỗi giai đoạn, trình bày phạm vi, đầu vào, thao tác ghi/cài đặt/render dự kiến, rủi ro và đầu ra. Hiển thị một nút `Thực thi Giai đoạn N` để user duyệt. Sau khi chạy xong, báo pass/partial/blocked/stale kèm evidence rồi mới hiện nút cho giai đoạn kế tiếp. Không tự động chuyển giai đoạn, kể cả khi user yêu cầu toàn quy trình. Mẫu nút:

```jsx
<button block onClick={() => GenUI.issueNewTurn("PHÊ DUYỆT THỰC THI: Giai đoạn N — [tên giai đoạn], đúng job/workspace đang chọn.")}>Thực thi Giai đoạn N</button>
```

Nếu UI không hỗ trợ button, yêu cầu user nhập câu phê duyệt nêu rõ giai đoạn. Phê duyệt giai đoạn không thay thế xác nhận riêng cho xóa/ghi đè, crop không phục hồi, cài đặt hệ thống, tải lớn/chi phí, chia sẻ dữ liệu hoặc xuất bản công khai.

## Giai đoạn 1 — Tiếp nhận và chuẩn bị (01–06)
01. Xác minh lại máy đã chọn còn online; kiểm tra đúng thư mục phim/logo và file phim/logo đã chọn; lập job riêng trong workspace chuẩn.
02. Kiểm tra OS, CPU, RAM, GPU/VRAM, dung lượng, quyền ghi, ffprobe streams/duration/fps/kích thước, subtitle và audio tracks; fingerprint nguồn (size, mtime, SHA256 nếu khả thi).
03. Tạo job folder `REVIEW_PHIM_WORKSPACE/jobs/<job-id>/`, config, state, logs; root workspace đã được tạo ở bootstrap. Không thay đổi phim gốc.
04. Kiểm tra Python/venv, FFmpeg/ffprobe, OpenCV, PySceneDetect, MoviePy, NumPy, SoundFile, Pillow, PyTorch. Tái sử dụng nếu tương thích; chỉ cài thiếu vào venv/workspace đã duyệt; không cài global.
05. Kiểm tra Faster-Whisper Large-v3 Turbo, Small, CTranslate2 và VieNeu-TTS; kiểm tra cache, chọn ngôn ngữ/model/preset đã xác minh. GPU nếu hỗ trợ, CPU fallback nếu phù hợp; không tải model lớn nếu chưa duyệt. Ghi revision/hash/license khi biết.
06. Chạy smoke test thật: tensor/ASR/TTS, decode và encode GPU/CPU, scene detection; đo lỗi, RAM/VRAM và thời gian. Chốt environment report, inventory, config/state, tests/logs. Không qua bước nếu công cụ thiết yếu không chạy.

## Giai đoạn 2 — Âm thanh và transcript (07–09)
07. FFmpeg giải mã track lời thoại đúng ngôn ngữ sang mono PCM 16 kHz (có thể stream/chunk, không cần lưu cả WAV). Xác nhận timebase.
08. Faster-Whisper nhận dạng toàn bộ phim; chia chunk có overlap, VAD, word timestamps nếu phù hợp, dịch offset về timeline nguồn, bỏ trùng có căn cứ, giữ confidence/flags. Xuất JSON, TXT timed, SRT/VTT. Kiểm tra coverage, khoảng im lặng, timestamp hợp lệ, resume theo chunk.
09. ChatGPT dịch toàn bộ transcript sang ngôn ngữ lời kể (mặc định Việt) theo batch, giữ ID/start/end, source text, đánh dấu chưa rõ/tên riêng/quảng cáo; kiểm tra đủ ID, không mất dòng, không gán timestamp từ nguồn thành timestamp từng từ tiếng Việt. Xuất song ngữ và báo cáo. QC1.

## Giai đoạn 3 — Hình ảnh (10–12)
10. Trích ảnh toàn phim theo mặc định 5 giây/ảnh, giữ timestamp thực, index và kích thước; kiểm tra đủ coverage; không nhầm khoảng intro/credit với phim. Nếu người dùng chỉ yêu cầu trích xuất, dừng tại đây.
11. ChatGPT nhìn tất cả ảnh qua bảng đủ rõ hoặc ảnh riêng; mô tả từng frame ID, nhân vật (chỉ theo vai trò/chứng cứ cốt truyện), hành động, bối cảnh, chữ liên quan, cảm xúc có căn cứ, điểm chưa rõ. Lưu batch coverage.
12. Đối chiếu từng ảnh với cả hai transcript theo thời gian, lập visual_transcript_timeline và mạch truyện. Không tự động coi ảnh cạnh lời thoại là chứng minh người nói. QC2 tạm.

## Giai đoạn 4 — Hiệu đính hiểu phim (13–16)
13. Khoanh vùng lời thoại thiếu, confidence thấp, tên sai, hình ảnh/mạch truyện mâu thuẫn, cao trào, sự kiện chưa rõ.
14. Nhận dạng lại vùng đó bằng model phù hợp, chỉnh VAD/ngôn ngữ/chunk, giữ kết quả riêng, không ghi đè nguồn.
15. Trích ảnh bổ sung mặc định 1 giây/ảnh; vùng rất ngắn có thể mật hơn. ChatGPT đọc bảng có phụ đề đủ rõ, kiểm chứng thứ tự và đối chiếu lời thoại.
16. Xây dựng dossier đã hiệu đính: nhân vật, quan hệ, sự kiện, nguyên nhân/hậu quả, động cơ có căn cứ, cao trào, kết, chủ đề, timestamp chứng cứ, danh sách chưa rõ. QC2; không gọi là phụ đề hiệu đính hoàn toàn nếu chỉ xác minh vùng.

## Giai đoạn 5 — Kịch bản (17–20)
17. ChatGPT viết V1 bằng ngôi thứ ba từ dossier, dùng logic kể chuyện sáu bước (`EDITORIAL.md`); giữ mạch nhân quả, hook có thật, tránh đọc phụ đề máy móc. Không tự áp thời lượng cố định; điều chỉnh theo yêu cầu.
18. Tìm web: nguồn giới thiệu chính thức, tóm tắt, bài phân tích đáng tin bằng ngôn ngữ phù hợp; xác nhận đúng phim/phiên bản/năm. Lưu URL, ngày, đoạn căn cứ, tình trạng đọc được/bị chặn. Nếu không có web, báo chưa hoàn thành phần đối chiếu.
19. Đối chiếu nguồn ngoài với phim; sửa lỗi, bổ sung tình tiết xác thực; ưu tiên phim gốc khi mâu thuẫn, đánh dấu chưa giải quyết. Không lấy bài báo thay kịch bản chính thức.
20. Trau chuốt V2: nhịp, tên riêng, ngôi kể, chuyển tiếp, hook/kết, lược lặp, chuẩn bị văn bản thuần TTS; giữ V1 và audit nguồn. QC3.

## Giai đoạn 6 — Giọng đọc (21–24)
21. Chia V2 theo đoạn, câu và giới hạn engine thực; lưu ID và nguyên văn; chuẩn hóa phát âm riêng nhưng giữ nguyên nội dung gốc.
22. TTS dùng preset/thiết bị đã xác minh, mặc định Trúc Ly nếu phù hợp. Lưu WAV từng đoạn và master, gap theo profile, timeline chính xác theo mẫu âm thanh. Kiểm tra tín hiệu, NaN, clip, sample rate/duration.
23. ASR ngược bằng Large-v3 Turbo và Small (hoặc model thay thế đã xác minh), đối chiếu từ/cụm, chuẩn hóa số và dấu câu; phân biệt ASR lỗi với TTS lỗi.
24. Tạo lại đoạn có dấu hiệu sai, so sánh bản cũ/mới, chọn bản có bằng chứng tốt hơn; lưu candidate, báo cáo sai khác, ghép Final, cập nhật word/paragraph timeline. QC4. Không coi ASR là nghe trực tiếp.

## Giai đoạn 7 — Timeline hình ảnh (25–28)
25. Chia lời đọc Final theo đơn vị ngữ nghĩa nhỏ; căn bằng timestamp từ, interpolate vùng không khớp và đánh cờ; đủ nội dung, timeline liên tục.
26. Phát hiện ranh giới cảnh qua FFmpeg hoặc PySceneDetect đã kiểm tra; proxy/threshold linh hoạt, không coi detector là chính xác tuyệt đối. Tạo database shot + mô tả/ảnh.
27. ChatGPT chọn cảnh cho từng đơn vị bằng hiểu biết phim và ảnh chứng cứ, ưu tiên hành động trực tiếp > phản ứng > nguyên nhân/bối cảnh > chuyển tiếp > minh họa chung; có thể chia thêm clip. Không chọn bằng keyword-only hoặc ngẫu nhiên.
28. Tính source in/out, review in/out theo frame, speed/transition; kiểm tra clip hợp lệ, liên tục, độ dài, reuse, cross-cut; xuất JSON/CSV và HTML preview. QC5.

## Giai đoạn 8 — Dựng và kiểm duyệt (29–32)
29. Dựng thử đoạn hook, lấy ảnh đầu/giữa/cuối, đối chiếu lời kể, sửa sai rồi mới dựng rộng.
30. Render proxy toàn timeline bằng codec khả dụng; kiểm tra số frame mỗi clip, concat, audio duration, giải mã. Không trộn thoại gốc lấn lời đọc; giữ nguồn.
31. ChatGPT kiểm tra trực quan clip bị cờ: cross-cut, reuse, timing, sai nhân vật, chữ quảng cáo, nhảy cảnh; ghi retain/revise/verify và lý do. Lấy ảnh nguồn bổ sung nếu cần.
32. Kiểm tra mọi clip còn lại; chỉnh điểm cắt có căn cứ, render lại bản V2 riêng, kiểm tra lại ảnh đầu/giữa/cuối của các clip đã chỉnh; QC6. Nếu có thể xem nghe liên tục, kiểm tra thêm và ghi đúng phương pháp. Không tuyên bố làm khi chỉ nhìn still.

## Giai đoạn 9 — Hậu kỳ (33–36)
33. Tạo phụ đề theo lời kể Final, timecode từ ASR căn chỉnh; SRT/ASS và cue manifest; không chồng lấn, dễ đọc, đủ nguyên văn.
34. Kiểm tra loại subtitle (rời/ghi cứng); remove stream hoặc crop/mask/inpaint được phép và kiểm chứng; xử lý cả chữ dọc/ngang ở vùng khác; không xóa chữ bối cảnh/logo/credit nhầm. Kiểm tra trước/sau; báo phần hình mất. Giữ nguyên kích thước hoặc tỷ lệ theo profile.
35. Tạo/nhận nhạc nền riêng có quyền sử dụng, nhẹ, không lời theo profile; có thể dùng hòa âm nguyên bản tổng hợp bằng code, không dùng bản nhạc nhận diện được nếu chưa có quyền. Giữ stem riêng, fade.
36. Cân giọng/nhạc, đo LUFS/true peak, duck, chống clipping; lưu narration master, music original/ducked, mix; đủ thời lượng. QC7. Nếu không nghe được thì ghi rõ.

## Giai đoạn 10 — Xuất và logo (37–39)
37. Render chất lượng nguồn hoặc profile, frame-count chính xác, codec/GPU đã kiểm tra. Tách layer, giữ tệp timeline và log.
38. ffprobe/giải mã đầy đủ, xác minh tổng frame/audio, cue midpoint và các điểm nối có phụ đề; sửa nháy bằng reset PTS/đặt tpad trước ASS hoặc render subtitle toàn timeline; kiểm tra lại sau sửa. Khảo sát phụ đề sót, báo mức độ bao phủ. Chốt Final kỹ thuật, không ghi đè bản trước.
39. Dùng logo đúng file đã chọn trong thư mục logo, giữ tỷ lệ/alpha, mặc định góc trên trái và kích thước tương đối; kiểm tra mẫu đầu/giữa/cuối, audio copy nếu chỉ overlay; không thêm logo giả khi thiếu. Nếu không yêu cầu logo, đánh dấu skipped với lý do. QC8.

## Giai đoạn 11 — Bộ nội dung YouTube (40)
40. Chuẩn bị tiêu đề thu hút nhưng đúng phim (<=100 ký tự theo yêu cầu nền tảng cần xác minh khi đăng), vài phương án; thumbnail 16:9 (ưu tiên 1280x720 hoặc cao hơn, đúng dấu tiếng Việt, kiểm tra hiển thị), mô tả hấp dẫn, CTA và hashtag liên quan, thông tin phim đã kiểm chứng, ghi spoiler/quyền tư liệu phù hợp. Dùng ảnh được phép hoặc sáng tạo riêng; nếu công cụ tạo ảnh không có, cung cấp thiết kế/prompt hoặc thumbnail thực từ tư liệu được cấp quyền nếu phù hợp. Lưu text/thumbnail và nguồn. Không đăng tự động; chỉ xuất bản khi user yêu cầu rõ và có kết nối, kiểm tra quyền và lựa chọn kênh. Không hứa tránh Content ID hoặc đảm bảo kiếm tiền. Giao final + stems + metadata + báo cáo.
