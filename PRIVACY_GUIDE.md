# Test quyền riêng tư và bàn phím

1. Mở **Trợ lý du học**. Mặc định là **Tra cứu trực tiếp**, không gửi câu hỏi tới Google.
2. Gõ câu hỏi: **Enter gửi**, **Shift+Enter xuống dòng**. Enter trong lúc bộ gõ đang ghép chữ không gửi.
3. Bấm **Cài đặt quyền Gemini**. Tất cả ô bổ sung/xác nhận mặc định bỏ chọn. Bấm Escape hoặc tiếp tục tra cứu trực tiếp sẽ không cấp quyền.
4. Nếu muốn Gemini, đọc thông báo, xác nhận đủ 18 tuổi, chỉ dùng dữ liệu không nhạy cảm và đồng ý xử lý. Chọn thêm lịch sử hoặc đoạn tài liệu nếu cần. Bỏ hết nhóm bổ sung để chỉ gửi câu hỏi và hướng dẫn chung.
5. Nhập câu hỏi, bấm **Xem dữ liệu sẽ gửi**: chưa gọi Google. Sau đó Enter để gửi.
6. Bấm **Thu hồi quyền Gemini**. Gemini bị tắt, tra cứu nội bộ vẫn dùng được. Quyền tự hết hạn sau tối đa 1 giờ; đăng nhập ở thiết bị khác cần cấp lại.
7. Mở **Tài khoản** để quản lý quyền. Tài khoản cá nhân có thêm **Đăng xuất trên mọi thiết bị**.
8. Đọc **Thông báo quyền riêng tư** ở chân trang hoặc trang đăng nhập; không cần đăng nhập để đọc.

## Vì sao có nhóm dữ liệu bị khóa?

Bản online mặc định `DEMO_ONLY`. Gemini miễn phí không phù hợp với dữ liệu cá nhân/nhạy cảm. Vì vậy nhóm ngân sách cá nhân và tóm tắt hợp đồng bị khóa ở máy chủ; tài liệu `USER_PROVIDED` không được đưa vào Gemini. Chọn **Tra cứu trực tiếp** để làm việc với chúng. Gemini có thể dùng đoạn mẫu tự soạn/tham khảo công khai nếu bạn cấp quyền; nhãn nguồn vẫn cần bạn kiểm tra.

Để test AI theo tài liệu, tải bộ mẫu từ **Bảo hiểm & hồ sơ**, upload `demo-policy.txt` với nhãn **Dữ liệu mẫu tự soạn**, cấp quyền **Gửi tối đa 3 đoạn tài liệu liên quan**, rồi hỏi về quyền lợi/hồ sơ trong tài liệu mẫu.

Không cần cấp camera, micro, vị trí hay quyền đọc toàn bộ máy. Chọn tệp chỉ chọn đúng tệp; nút tải lên mới gửi tới máy chủ. Dữ liệu mẫu dùng chung không phải không gian riêng.

Thu hồi không xóa được nội dung đã gửi cho Google. Xóa chat chỉ xóa nội dung trong tab. Chưa có chức năng tự xóa toàn bộ tài khoản; xem giới hạn cụ thể trong thông báo. Không dùng kết quả này để tuyên bố dự án đã được chứng nhận tuân thủ pháp luật.

Lượt kiểm tra Gemini online cuối ngày 19/10/2026 bị TIMEOUT. Ứng dụng hiện thông báo và chuyển sang tra cứu nội bộ; không giả làm câu trả lời AI. Các chốt cấp/thu hồi quyền vẫn hoạt động. Kết quả cụ thể được giữ trong báo cáo triển khai.

Nguồn nghiên cứu và cách triển khai: [docs/21_PRIVACY_PERMISSIONS_RESEARCH.md](docs/21_PRIVACY_PERMISSIONS_RESEARCH.md).
