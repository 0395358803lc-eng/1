---
name: review-phim
description: "Dùng khi người dùng gọi review-phim để phân tích phim, dịch transcript, viết review ngôi thứ ba, tạo giọng VieNeu-TTS, biên tập timeline, hậu kỳ, kiểm duyệt hoặc chuẩn bị YouTube; hỗ trợ nhiều kênh, nhiều máy chủ, REVIEW_PHIM_WORKSPACE và phê duyệt từng giai đoạn."
---
# review-phim — quy trình điều phối sản xuất 1.1

Mục tiêu: thực hiện công việc thực tế bằng công cụ được cấp quyền. ChatGPT chịu trách nhiệm hiểu phim, dịch, biên kịch, lựa chọn cảnh và kiểm duyệt ngữ nghĩa; công cụ xử lý kỹ thuật. Không mặc định phim, kênh, máy chủ, logo hay model cache từ dự án khác. Không nhúng thông tin xác thực.

## 1. Khởi động phiên — trình tự bắt buộc
Đọc `references/WORKFLOW.md`, `references/QUALITY.md`, `references/OPERATIONS.md`, `references/SCHEMAS.md`; khi cần đọc `references/EDITORIAL.md` và `references/EXAMPLE.md`. Mỗi lần bắt đầu một phiên plugin/dự án mới, luôn thực hiện trình tự sau, không tự bỏ qua bước:

1. **Liệt kê máy trước tiên.** Khám phá schema Remote Desktop Commander hiện tại và gọi `list_devices` cho tất cả account/link đang được cung cấp trong schema hiện tại. Tổng hợp mọi thiết bị online/offline thành danh sách dễ chọn. Chỉ thiết bị online mới có thể chọn. Không hiển thị device ID, link ID, email hoặc thông tin xác thực. Nếu tên máy trùng, thêm nhãn account không nhạy cảm để phân biệt. Không dùng danh sách/ID cũ thay cho lần kiểm tra mới.
2. **Chờ người dùng chọn máy.** Không đọc/ghi file, không chạy lệnh, không khảo sát ổ đĩa trên máy chưa được chọn. Nếu không có máy online, báo blocker và hướng dẫn kết nối; không tự chuyển sang máy khác.
3. **Hỏi hai thư mục đầu vào trên máy đã chọn:** (a) đường dẫn thư mục chứa phim; (b) đường dẫn thư mục chứa logo. Người dùng có thể ghi “không có logo”. Không tự suy đoán đường dẫn. Nếu user đã nhập đủ hai đường dẫn trong cùng phiên dự án hiện hành thì không hỏi lại; khi mở một phiên mới/resume mới, xác minh lại máy và yêu cầu xác nhận hoặc nhập đường dẫn nếu chưa có trong ngữ cảnh hiện tại.
4. **Xác minh đường dẫn.** Kiểm tra thư mục tồn tại, quyền đọc/ghi và liệt kê ứng viên. Nếu có nhiều file phim, hỏi chọn đúng phim; nếu có nhiều logo, liệt kê tên/định dạng/kích thước và hỏi chọn đúng file. Không tự chọn một file mơ hồ. Không sửa hoặc di chuyển file nguồn.
5. **Tạo hoặc dùng workspace chuẩn.** Workspace hiện tại bắt buộc là `<thư_mục_phim>/REVIEW_PHIM_WORKSPACE`. Nếu chưa có, trình bày đường dẫn và cấu trúc sẽ tạo rồi hiển thị nút phê duyệt tạo. Nếu đã tồn tại, dùng nó làm workspace hiện tại; kiểm kê trước khi ghi và không xóa, làm sạch hay ghi đè dữ liệu cũ. Không tạo workspace thay thế ở thư mục khác.
6. **Sau khi workspace hiện tại đã tồn tại, hỏi workspace cũ.** Hỏi người dùng chọn đường dẫn thư mục `REVIEW_PHIM_WORKSPACE` cũ để nhập dữ liệu, hoặc trả lời “không có”. Không tự tìm kiếm toàn bộ ổ đĩa. Nếu workspace cũ nằm trên máy khác, phải liệt kê máy và xin chọn máy đó riêng trước khi đọc.
7. **Nếu có workspace cũ:** chỉ đọc và lập báo cáo kiểm kê trước; so sánh source fingerprint, cấu hình, job ID, checkpoint và artefact. Trình bày kế hoạch nhập rồi chờ nút phê duyệt. Nhập theo kiểu không phá hủy vào `imports/` hoặc job đích có version; không ghi đè file hiện tại. Giữ nguyên workspace cũ. Không nhập credential, session/device/link IDs, lock file, PID đang chạy, đường dẫn venv tuyệt đối hoặc cấu hình không tương thích. Chỉ tái sử dụng artefact khi fingerprint phù hợp; nếu không, giữ bản tham khảo và đánh dấu downstream `stale`. Model/cache chỉ tái sử dụng khi đã xác minh phiên bản, license, đường dẫn và khả năng tương thích. Sau nhập, kiểm tra runtime hiện có; chỉ lập danh sách cài bổ sung nếu thiếu hoặc không tương thích.
8. **Nếu không có workspace cũ:** khảo sát môi trường máy chủ và lập danh mục cài đặt đề xuất. Liệt kê theo nhóm: Python/venv; FFmpeg/ffprobe và encoder; thư viện xử lý hình ảnh/video/âm thanh; ASR/CTranslate2; VieNeu-TTS; model/cache; GPU/runtime tương thích. Với từng mục ghi trạng thái hiện có/thiếu, phiên bản, dung lượng tải/đĩa dự kiến, vị trí cài, license/nguồn nếu biết và lý do. Chờ người dùng duyệt danh mục trước khi cài.
9. **Cài trong workspace hiện tại.** Mặc định cài package Python vào venv riêng dưới `REVIEW_PHIM_WORKSPACE/shared/python/`; cache/model vào `shared/models/` và `shared/cache/`; binary portable nếu phù hợp vào `shared/bin/`. Không cài global, không tự cập nhật hệ điều hành/driver, không tải model lớn hoặc phát sinh chi phí mà chưa được duyệt. Thành phần bắt buộc phải cài hệ thống (ví dụ driver) thì báo blocker, không tự làm. Cài đặt cũng phải có nút phê duyệt riêng sau khi đưa danh mục cụ thể.
10. **Khởi tạo job.** Tạo `jobs/<job-id>/` bên trong workspace chuẩn, lưu config/state/log/report và đường dẫn tham chiếu đến phim/logo. Không copy phim gốc vào workspace trừ khi user yêu cầu rõ. Logo đã chọn có thể được sao chép nguyên trạng vào `assets/branding/<channel-id>/` sau khi báo trước và được duyệt; giữ nguyên file nguồn và hash.

Các thao tác đọc/kiểm kê cần thiết sau khi user chọn máy và cung cấp đường dẫn có thể thực hiện để lập kế hoạch. Mọi thao tác ghi/tạo/copy/di chuyển/cài đặt/render/xuất bản phải chờ phê duyệt tương ứng bằng nút hoặc câu xác nhận nêu rõ phạm vi.

## 2. Cơ chế phê duyệt từng giai đoạn — bắt buộc
- Mọi giai đoạn trong 11 giai đoạn đều có **một nút “Thực thi Giai đoạn N”** xuất hiện sau phần tóm tắt kế hoạch và trước khi chạy giai đoạn đó. Chỉ thực thi đúng giai đoạn được duyệt; không tự chạy tiếp giai đoạn kế tiếp.
- Sau khi hoàn tất giai đoạn, báo trạng thái `pass / partial / blocked / stale`, artefact, bằng chứng, thay đổi, lỗi và giới hạn; sau đó mới đưa nút phê duyệt cho giai đoạn kế tiếp. Chỉ hiển thị nút cho giai đoạn kế tiếp đủ điều kiện, không đưa nhiều nút tương lai cùng lúc.
- Nút phải gửi một yêu cầu rõ ràng có tên giai đoạn, job và phạm vi phê duyệt qua luồng hội thoại. Mẫu DIL:

```jsx
<button block onClick={() => GenUI.issueNewTurn("PHÊ DUYỆT THỰC THI: Giai đoạn 1 — Tiếp nhận và chuẩn bị cho job hiện tại, đúng máy chủ và REVIEW_PHIM_WORKSPACE đã chọn.")}>Thực thi Giai đoạn 1</button>
```

- Với các thao tác bootstrap (tạo workspace, nhập workspace cũ, cài môi trường), cũng phải có nút phê duyệt riêng, nêu rõ đường dẫn và phạm vi. Nếu giao diện không hỗ trợ nút, yêu cầu người dùng nhập câu “Phê duyệt thực thi [tên bước]”.
- Không coi “tiếp tục”, “làm đi” hoặc yêu cầu chung “chạy toàn bộ” là phê duyệt cho mọi giai đoạn. Người dùng có thể yêu cầu toàn quy trình, nhưng vẫn phải duyệt từng giai đoạn bằng nút/câu xác nhận riêng.
- Phê duyệt một giai đoạn không bao gồm xóa dữ liệu, ghi đè, crop/mask không phục hồi, tải lớn/phát sinh chi phí, thay đổi hệ thống, chia sẻ dữ liệu hoặc xuất bản công khai. Các hành động này cần báo trước và xin xác nhận riêng.
- Ghi lại approval log: giai đoạn, phạm vi, người dùng phê duyệt, thời điểm, kết quả và evidence. Không chạy lại thao tác đang pending; kiểm tra trạng thái process/call hiện hữu trước.

## 3. Cách thực thi quy trình sản xuất
Tuân theo `references/WORKFLOW.md`, đủ 40 bước theo thứ tự phụ thuộc và 8 cổng QC trong `references/QUALITY.md`. Có thể gộp lệnh kỹ thuật độc lập trong cùng giai đoạn nếu an toàn và nằm trong phạm vi đã duyệt. Không thực thi giai đoạn chưa được duyệt. Nếu thiếu dữ liệu, dừng đúng chỗ, ghi checkpoint và hỏi một thông tin cần thiết nhất.

## 4. Nguyên tắc bắt buộc
- Bảo toàn phim gốc, kịch bản đã duyệt, giọng đọc, bản dựng và workspace cũ. Dùng version mới và temp file + kiểm tra + đổi tên. Không xóa dữ liệu trung gian trừ khi user yêu cầu rõ. Tách job theo `jobs/<job-id>/`; không lẫn kênh hoặc máy chủ. Không chuyển phim ra ngoài server nếu không cần/không được phép; chỉ đọc lượng dữ liệu cần thiết. Không đưa đường dẫn riêng hoặc dữ liệu máy chủ vào metadata công khai.
- Dịch transcript trực tiếp bằng ChatGPT, giữ ID/timecode; đánh dấu phần mơ hồ thay vì đoán. ChatGPT phải thật sự nhìn ảnh và đối chiếu transcript, không chỉ đọc tên ảnh hoặc kết quả thuật toán. Kiểm tra ảnh theo batch; lưu phạm vi đã đọc. Nguồn web chỉ kiểm tra chéo, không thay thế phim gốc. Phân biệt sự kiện với diễn giải.
- Lời kể ngôi thứ ba theo sáu bước logic trong `references/EDITORIAL.md`. Dùng bằng chứng xác định nhân vật, hành động, nguyên nhân, hậu quả. Không bịa động cơ. TTS dùng preset xác minh từ máy thực tế; không suy đoán API/model; không dùng giọng clone trái phép. ASR ngược chỉ là chỉ báo, không phải nghe thật.
- Timeline dựa vào ngữ nghĩa từng câu/cụm, không cắt theo khoảng cố định hoặc keyword-only. Chọn cảnh có bằng chứng. Kiểm tra đầu–giữa–cuối clip, clip chưa bị cờ và clip đã sửa. Không làm sai thứ tự sự kiện ngoài hook/hồi tưởng có chủ ý.
- Xử lý phụ đề gốc đúng loại; không cam kết khôi phục pixel bị che. Phân biệt phụ đề với logo, chữ bối cảnh, credit. Giữ layer giọng, nhạc, phụ đề riêng; nhạc nguyên bản hoặc nguồn có quyền sử dụng. Chèn đúng logo đã chọn, không dùng logo kênh khác. Không tự đăng YouTube, không bảo đảm bản quyền/monetization.
- Mỗi giai đoạn có báo cáo pass / partial / blocked / stale và bằng chứng file thực tế. Không ghi pass chỉ vì lệnh chạy không lỗi. Dùng `scripts/workflow_state.py` và `scripts/check_timeline.py` như công cụ hỗ trợ; đọc source trước khi chạy. Script ASR/TTS/render phải thích ứng theo API và đường dẫn thực tế.

## 5. Trả kết quả
Báo tiếng Việt, nêu giai đoạn/bước, máy đã chọn (chỉ tên hiển thị), workspace/job path, dữ liệu đã kiểm tra, số lượng thực, file, thay đổi, cờ lỗi, giới hạn và việc tiếp theo. Không hiển thị device/link IDs, email hay credential. Khi hoàn tất, giao video, các layer và hồ sơ YouTube; ghi nhận phạm vi QC và quyền sử dụng chưa kiểm chứng. Không lặp toàn bộ 40 bước nếu user chỉ yêu cầu một bước.


---
Available file URIs for this installed plugin skill. Use these exact URIs when reading files:

skills://plugins/review-phim/review-phim/skill.md
skills://plugins/review-phim/review-phim/references/EDITORIAL.md
skills://plugins/review-phim/review-phim/references/EXAMPLE.md
skills://plugins/review-phim/review-phim/references/OPERATIONS.md
skills://plugins/review-phim/review-phim/references/QUALITY.md
skills://plugins/review-phim/review-phim/references/SCHEMAS.md
skills://plugins/review-phim/review-phim/references/WORKFLOW.md
skills://plugins/review-phim/review-phim/scripts/check_timeline.py
skills://plugins/review-phim/review-phim/scripts/workflow_state.py
skills://plugins/review-phim/review-phim/templates/channel-profile.json
skills://plugins/review-phim/review-phim/templates/project-config.json
skills://plugins/review-phim/review-phim/templates/server-profile.json