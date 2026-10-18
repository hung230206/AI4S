# Dùng bản MVP hiện tại

Bản mới có **Trợ lý du học**, **Ngân sách & thu chi**, **Tỷ giá & ngân sách** và nhập hóa đơn từ ảnh/PDF. Xem [STUDENT_FINANCE_GUIDE.md](STUDENT_FINANCE_GUIDE.md) để dùng trọn luồng; các bước nền tảng dưới đây vẫn áp dụng.

Bạn bè dùng máy khác cùng Wi-Fi: mở **http://192.168.1.14:3000** khi máy chủ đang chạy (IP kiểm tra ngày 18/10/2026). Cách chạy lại hoặc đổi địa chỉ IP: xem [LAN_TEST_GUIDE.md](LAN_TEST_GUIDE.md).

Giao diện mới bắt đầu bằng hai lựa chọn: **Tôi cần chuẩn bị bao nhiêu tiền?** và **Tôi muốn hiểu điều khoản bảo hiểm**. Popup **Bắt đầu cùng Bảo An** xuất hiện lần đầu dùng trên mỗi trình duyệt/tài khoản. Có thể đóng bằng **Để sau**, nút đóng hoặc Escape; mở lại bằng **Hướng dẫn** ở đầu trang. Nút Hướng dẫn tự chọn chủ đề của trang đang xem. Các khung hướng dẫn có dấu `+` mở thêm giải thích ngay tại bước cần làm.

Mở **http://localhost:3000** và tải lại trang. Nếu đang ở tài khoản dữ liệu mẫu, chọn **Đăng xuất** trước.

1. **Tạo tài khoản**: nhập tên, email và mật khẩu từ 10 ký tự. Bạn vào không gian riêng, chưa có hóa đơn hoặc chính sách. Email hiện là tên đăng nhập; chưa có gửi thư xác minh hay khôi phục mật khẩu qua email.
2. **Thêm hóa đơn**: vào Hóa đơn → Thêm hóa đơn. Nhập mã, đơn vị phát hành, bên nhận, số CNY, ngày đến hạn, nguồn và ghi chú từ thông báo thu phí của bạn. Lưu xong có thể xem, sửa, tìm kiếm hoặc lưu trữ. Bên nhận chưa được xác minh với nhà cung cấp thanh toán.
3. **Xem giá trị VND**: mở hóa đơn → Xem giá trị VND → Lấy tỷ giá và tính VND. App lấy tỷ giá tham chiếu Frankfurter, lưu ngày dữ liệu/nguồn và tính tại máy chủ. Không sử dụng tỷ giá mẫu cho hóa đơn bạn nhập. Khi nguồn không khả dụng và không có bản lưu đủ mới, app báo lỗi, không tự thay bằng một con số giả lập.
4. **Kiểm tra báo giá**: xem số CNY, tỷ giá, ngày dữ liệu, giá trị quy đổi và phí ứng dụng. Phí ứng dụng mặc định 0; phí ngân hàng/nhà cung cấp chưa được tính do chưa kết nối tài khoản dịch vụ. Tỷ giá theo ngày phục vụ lập kế hoạch, không phải cam kết đổi tiền của ngân hàng. Có thể Cập nhật báo giá; báo giá cũ vẫn giữ nguyên dữ liệu đã chụp tại thời điểm tạo.
5. **Thử thanh toán nếu cần**: chỉ xem VND chưa tạo giao dịch. Muốn thử luồng xử lý, tích đồng ý sandbox rồi chọn Chạy thử thanh toán sandbox. Không chuyển tiền thật. Công cụ Vận hành sandbox dùng mã cục bộ riêng để phát kết quả có chữ ký; chi tiết trong RUNBOOK.md. Một hóa đơn chỉ có một giao dịch hoạt động hoặc thành công.
6. **Tài liệu bảo hiểm**: tải PDF có văn bản, TXT hoặc MD lên, tối đa 5 MB/50 trang. Đặt tên, thêm đường dẫn nguồn nếu có. Tìm câu hỏi/từ khóa; app trả đoạn trích gốc, tên tệp và số trang. Có thể đọc toàn văn đã trích xuất, tải bản gốc hoặc xóa tài liệu. PDF ảnh quét/ảnh có thể nhận dạng cục bộ tối đa 5 trang; hệ thống không đoán nội dung thiếu và không tự sinh câu trả lời bảo hiểm.
7. **Lịch sử giao dịch**: tìm theo mã, lọc trạng thái, xuất CSV. Mỗi giao dịch có dòng thời gian, nhật ký JSON; giao dịch sandbox thành công có biên nhận thử nghiệm riêng. Nhãn sandbox được giữ vì chưa có ngân hàng/cổng thanh toán thật được kết nối.
8. **Tài khoản**: sửa tên hiển thị, đổi mật khẩu và thu hồi các phiên, hoặc đăng xuất. Phiên cá nhân lưu trong cookie HttpOnly nên tải lại trang vẫn đăng nhập; dữ liệu nằm trong PostgreSQL.

**Dùng thử sandbox với dữ liệu mẫu** là lựa chọn tách riêng trên màn hình đăng nhập. Các hóa đơn hư cấu, tỷ giá cố định và kết quả thử nghiệm của phiên bản trước chỉ nằm trong không gian đó. Tài khoản cá nhân mới không được nạp các dữ liệu này.

Để chạy lại máy chủ hoặc tự kiểm thử, xem RUNBOOK.md và phần MVP ở đầu file. Kết quả thực tế được ghi trong IMPLEMENTATION_REPORT.md. Không nhập thẻ thanh toán, mật khẩu ngân hàng hay giấy tờ tùy thân: các chức năng này không được sử dụng trong MVP.
