# Test luồng C + D

Mở **Bảo hiểm & hồ sơ** (`/insurance`). Tạo tài khoản riêng để dữ liệu không lẫn với người khác.

1. Bấm **Tải bộ tệp test C + D**, giải nén ZIP.
2. Bấm **Thêm hợp đồng**. Tải `demo-policy.txt`, chọn **Dữ liệu mẫu tự soạn**, rồi **Tải lên và đọc tài liệu**.
3. Chọn `review-fields.json` ở mục nạp trường. Đây chỉ là điền nháp. Đọc văn bản nguồn, đối chiếu số liệu, tích xác nhận rồi lưu.
4. Vào **Ngân sách & thu chi**, tạo sổ CNY có **1.000 CNY**. Quay lại hợp đồng → **Dự trù phí vào ngân sách** → chọn sổ → xác nhận. Dự phóng còn **200 CNY**; số dư hiện tại vẫn **1.000 CNY**.
5. Sang **Kiểm tra quyền lợi**, bấm so sánh. Ngoại trú khớp hạn mức **2.000 CNY**, vận chuyển y tế có khoảng trống. Đổi hạn mức ngoại trú thành **4.000 CNY** sẽ thấy thiếu hạn mức. Đổi ngày/lãnh thổ để thử trường hợp khác. Đây là so sánh dữ liệu bạn nhập, không phải quyết định bảo hiểm.
6. Trong hợp đồng, bấm **Tạo dự trù phí để thử sandbox** và đọc xác nhận. Khoản phí này do bạn tạo trong app, không phải hóa đơn nhà bảo hiểm. Mở **Xem giá trị VND**, lấy tỷ giá, kiểm tra tổng, chọn sandbox thành công, tích đồng ý rồi chạy thử. Biên nhận có dòng **NO REAL FUNDS MOVED**. Kế hoạch phí không bị tạo thêm lần nữa khi mở từ hóa đơn.
7. Sang **Hồ sơ bồi thường**, chọn hợp đồng, nhập tên hồ sơ và chi phí **500 CNY**, ngày sự kiện hôm nay rồi tạo.
8. Đính kèm `claim-invoice.txt`, `claim-medical-record.txt`, `claim-claim-form.txt` vào đúng ba mục. Các mục định danh/tài khoản chỉ tích đã chuẩn bị ngoài app, không tải giấy tờ thật lên.
9. Đối chiếu checklist → **đánh dấu đủ checklist** → tích xác nhận → cập nhật. Bấm **Xuất bộ hồ sơ ZIP** để kiểm tra checklist, nguồn hợp đồng, tệp đính kèm và nhật ký.
10. Nếu cần sửa, dùng **Sửa thông tin hồ sơ**, gỡ tệp sai hoặc quay lại chuẩn bị. Sau khi sửa cần xác nhận checklist lại. Nút **Ghi nhận tôi đã gửi ngoài ứng dụng** chỉ lưu lời xác nhận của bạn và mã/kênh tiếp nhận; ứng dụng không gửi hồ sơ tới công ty bảo hiểm.

Tệp test đều tự soạn, ngày được tạo lúc tải. Không dùng làm hợp đồng, hóa đơn hoặc chứng từ y tế thật. Các tệp đính kèm hồ sơ bồi thường không được gửi sang Gemini.

**Dùng được:** lưu và sửa hợp đồng, trích dẫn trang nguồn, kiểm tra quyền lợi, lập kế hoạch phí, dự phóng ngân sách, sandbox thanh toán, checklist/chứng từ/ZIP, nhắc việc khi mở trang, trợ lý đọc dữ liệu có giới hạn, tiếng Việt/Anh/Trung và sáng/tối.

**Chưa phát triển:** chuyển/đổi tiền thật; mua hoặc kích hoạt bảo hiểm; gửi hồ sơ qua API nhà bảo hiểm; xác thực hợp đồng/chứng từ; xét duyệt và chi trả bồi thường; email/SMS nhắc việc; theo dõi tỷ giá trong ngày. Gemini cần cấu hình riêng trên máy chủ; nếu thiếu khóa hoặc API lỗi vẫn có tra cứu trực tiếp.
