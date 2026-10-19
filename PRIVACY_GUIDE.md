# Test popup đồng ý quyền

1. Mở **Trợ lý du học**, bấm **Gemini AI**: popup hiện ngay, không có checkbox.
2. Popup cho biết phạm vi cố định: câu hỏi, tối đa 3 lượt Gemini gần nhất và 3 đoạn tài liệu mẫu/công khai. Link **Xem chi tiết quyền và cách xử lý dữ liệu** mở thông báo đúng mục trong tab mới.
3. Chọn **Không đồng ý** hoặc Escape: không cấp quyền; tiếp tục tra cứu trực tiếp. Chọn **Đồng ý**: bật Gemini, chưa gửi câu hỏi. Nút này cũng xác nhận điều kiện tuổi và nội dung nêu trong popup.
4. Nhập câu hỏi. **Enter gửi**, **Shift+Enter xuống dòng**. Có thể **Xem dữ liệu sẽ gửi** trước khi gửi; xem trước chưa gọi Google.
5. **Thu hồi quyền Gemini** ở chat hoặc Tài khoản chặn lần gửi tiếp theo. Quyền hết hạn sau tối đa 1 giờ, khi phiên đăng nhập hết hiệu lực hoặc khi thông báo thay đổi. Đăng nhập khác cần cấp riêng.
6. Khi **Đọc và điền thông tin** hóa đơn, **Tải lên và đọc/trích xuất** tài liệu hoặc chọn chứng từ đính kèm hồ sơ: popup riêng xin phép xử lý đúng tệp đó. Chọn **Không đồng ý** thì không gửi tệp. Chọn **Đồng ý** thì tiếp tục thao tác vừa chọn. Mỗi lần tải tệp hỏi lại; không ghi nhớ bằng localStorage.
7. Link chi tiết giải thích mục đích, bên xử lý, dữ liệu, lưu trữ, xóa và giới hạn. Các tệp được lưu/xử lý tại máy chủ ứng dụng; không cấp quyền đọc cả máy, camera, micro hay vị trí.

Gemini không nhận dữ liệu tài chính, hợp đồng cá nhân, hồ sơ bồi thường hoặc tệp gốc qua popup này. Tài liệu mẫu phải có nhãn **Dữ liệu mẫu tự soạn** hoặc **Tài liệu tham khảo công khai**. Mặc định tệp mới là **Tài liệu do bạn cung cấp** và không được gửi cho Gemini.

Từ chối quyền Gemini không cản OCR hoặc ngân sách. Từ chối xử lý một tệp chỉ hủy lần tải tệp đó. Thu hồi không xóa được nội dung đã gửi cho Google; xóa chat chỉ xóa tab. Chưa có tự xóa toàn bộ tài khoản hoặc lịch xóa tự động. Lần kiểm tra provider trước thay đổi này bị TIMEOUT; bản này không tuyên bố đã sửa khả năng đáp ứng của Google.

Nguồn và giới hạn: [Nghiên cứu quyền riêng tư](docs/21_PRIVACY_PERMISSIONS_RESEARCH.md).
