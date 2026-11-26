# review-phim 1.3.0

Plugin hỗ trợ hai chế độ. **Transcript-only** là mặc định khi người dùng chỉ cần transcript và bản dịch tiếng Việt: nhận dạng lời thoại, dịch sát theo từng segment, giữ ID/timecode, xuất TXT/SRT/VTT/JSON với UTF-8 và dấu tiếng Việt đúng; không QC1, không viết review, không TTS, không dựng/render. **Review đầy đủ** chỉ chạy khi người dùng yêu cầu, theo 11 giai đoạn/40 bước và các cổng QC2–QC8.

**Cơ chế kiểm soát mới:** mỗi bước 01–40 cần một lần xác nhận riêng. Plugin trình bày kế hoạch trước bước, thực hiện đúng một bước sau khi được duyệt, kiểm tra kết quả, lưu checkpoint và báo cáo; sau đó dừng và chỉ hiển thị nút xác nhận cho bước kế tiếp. Các thao tác bootstrap (tạo/nhập workspace, cài dependency, tải model/cache, sao chép logo) có phê duyệt riêng. Không có phê duyệt theo cả giai đoạn và không tự chạy xuyên bước.

Plugin tiếp tục hỗ trợ workspace chuẩn `REVIEW_PHIM_WORKSPACE`, nhiều máy chủ, bảo toàn nguồn và checkpoint. Không sửa/sao chép phim gốc, không cài global, không tự đăng YouTube.
