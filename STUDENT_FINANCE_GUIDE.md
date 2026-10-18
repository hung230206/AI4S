# Dùng bản nâng cấp theo bài toán tài chính du học

**Chatbot mới:** chọn Gemini AI hoặc Tra cứu trực tiếp trong Trợ lý du học. Hướng dẫn dùng API thật, dữ liệu mẫu, quyền riêng tư và cấu hình Render: [GEMINI_GUIDE.md](GEMINI_GUIDE.md).

Mở http://localhost:3000 và tạo tài khoản riêng. Bạn bè cùng Wi-Fi dùng http://192.168.1.14:3000 khi máy chủ đang chạy; IP được kiểm tra ngày 18/10/2026. Không cần API key, tài khoản OCR hay tài khoản ngân hàng để thử các chức năng dưới đây.

## 1. Từ thông báo thu phí tới hóa đơn

1. Mở **Hóa đơn → Thêm hóa đơn**.
2. Trong **Nhập từ ảnh hoặc PDF**, chọn PNG/JPG/WebP/PDF/TXT/MD. Giới hạn 5 MB, PDF hóa đơn tối đa 5 trang; ảnh tối đa 16 megapixel.
3. Chọn ngôn ngữ chính **Tiếng Trung và Anh**, **Tiếng Việt và Anh** hoặc **Tiếng Anh** khi biết. Chế độ kết hợp cũng có thể đọc nhưng chọn ngôn ngữ đúng thường tốt hơn.
4. Chọn **Đọc và điền thông tin**. Kết quả có dòng nguồn và số trang cho từng trường. Tệp được xử lý tại máy chủ của app; nội dung không gửi đến API OCR bên ngoài.
5. Đối chiếu mã hóa đơn, đơn vị, bên nhận, số CNY và hạn với bản gốc. Sửa trực tiếp nếu cần; ô không đọc được sẽ để bạn bổ sung.
6. Tích **Tôi đã đối chiếu...** rồi **Lưu hóa đơn**. Chưa có giao dịch hoặc khoản chi nào được tạo.
7. Ở trang chi tiết, mở **Chứng từ gốc và nội dung đã đọc** để tải bản gốc hoặc kiểm tra lại văn bản.

OCR có thể đọc sai; điểm nhận dạng không phải bảo đảm số tiền đúng. App hiện lưu hóa đơn CNY. Nếu tệp không xác định được CNY, đọc cảnh báo và kiểm tra tiền tệ trước khi điền số tiền; app không tự biến hóa đơn USD/VND thành CNY.

## 2. Sổ CNY/VND và dự phóng

1. Mở **Ngân sách & thu chi**.
2. **Thêm sổ tiền**: đặt tên, chọn CNY hoặc VND, nhập số dư đã đối chiếu và ngày bắt đầu. VND là số nguyên; CNY tối đa 2 chữ số thập phân.
3. Tab **Thu / chi thực tế**: nhập khoản đã xảy ra, chọn đúng sổ, nhóm và ngày thực tế; **Ghi vào sổ** cập nhật số dư. Nhập sai có thể **Hủy ghi nhận → Xác nhận hủy ghi nhận**; nhật ký vẫn được giữ. Có thể xuất CSV các khoản gần nhất.
4. Tab **Kế hoạch**: thêm tiền nhà, học phí, học bổng, trợ cấp hoặc khoản định kỳ. Chọn một lần/hàng tháng. Kế hoạch chưa ảnh hưởng số dư thực tế.
5. Tab **Dự phóng**: chọn 30/60/90 ngày. Xem số dư hiện tại, cuối kỳ, đường diễn biến, mức thấp nhất và ngày có thể thiếu tiền. Khoản quá hạn chưa ghi nhận được đưa vào ngày đầu dự phóng và gắn nhãn quá hạn.
6. Khi khoản đã xảy ra ngoài thực tế, chọn **Ghi nhận đã chi/thu → Xác nhận ghi sổ**. Hệ thống chỉ ghi một lần và bỏ kỳ kế hoạch tương ứng khỏi phần dự kiến để tránh tính trùng.
7. Dừng lịch không còn dùng bằng **Dừng kế hoạch**. Các khoản thực tế đã ghi không bị xóa.

Sổ là dữ liệu bạn khai báo, không phải ví giữ tiền thật. CNY và VND được theo dõi riêng. Tổng VND là giá trị tham chiếu theo ngày, không tự đổi tiền hoặc bù thiếu hụt giữa các sổ. Dự phóng từ lịch đã nhập; thiếu khoản thu/chi sẽ làm kết quả thiếu thông tin. Đây không phải dự báo học máy hay dự đoán thị trường.

## 3. Đưa hóa đơn vào kế hoạch

Tạo sổ CNY trước. Mở hóa đơn đang mở, chọn sổ trong **Đưa vào ngân sách**, rồi **Đưa vào kế hoạch chi**. Máy chủ lấy số tiền và ngày đến hạn từ hóa đơn, không nhận số tiền thay thế từ nút này. Thêm lại cùng hóa đơn không tạo kế hoạch thứ hai.

Kế hoạch lưu bản chụp số tiền/hạn tại lúc thêm, không tự thay đổi theo lần sửa hóa đơn về sau. Việc lưu kế hoạch và thanh toán sandbox đều không tự ghi thu/chi. Khi đã chi thực tế, xác nhận kỳ kế hoạch tương ứng.

## 4. Theo dõi tác động tỷ giá

Mở **Tỷ giá & ngân sách**, xem lịch sử CNY/VND từ Frankfurter. Có nguồn và ngày dữ liệu. Chọn hóa đơn hoặc nhập số CNY, thêm ngân sách VND nếu cần rồi **Phân tích ngân sách**. Xem giá trị theo tham chiếu, hai kịch bản giảm/tăng 5% và phần vượt/còn ngân sách.

Đây là kiểm tra độ nhạy của chi phí, không dự đoán khi nào nên đổi tiền. Chưa gồm phí của ngân hàng/nhà cung cấp. Frankfurter cung cấp dữ liệu tham chiếu theo ngày; bấm cập nhật không tạo dữ liệu từng giây. Khi FX không có dữ liệu đủ mới, phần sổ vẫn hiển thị dự phóng nguyên tệ và không tự dùng tỷ giá mẫu.

## 5. Trợ lý và tài liệu bảo hiểm

**Trợ lý du học** có các câu hỏi gợi ý về đủ tiền trong 30 ngày, hóa đơn gần hạn, tỷ giá và hồ sơ bảo hiểm. Trả lời lấy từ kế hoạch/tài liệu đã lưu, có đường dẫn hoặc trang nguồn. Nếu thiếu dữ liệu, trợ lý nêu phần cần bổ sung. Chọn Gemini AI để diễn giải bằng mô hình sinh văn bản, có hội thoại nối tiếp và nguồn đối chiếu; chọn Tra cứu trực tiếp để dùng quy tắc/tìm đoạn gốc. Chỉ chế độ Gemini gửi ngữ cảnh liên quan tới Google.

**Tài liệu bảo hiểm** nhận PDF, ảnh, TXT hoặc MD. PDF có chữ tối đa 50 trang; OCR ảnh/PDF quét tối đa 5 trang; tệp tối đa 5 MB. Chọn ngôn ngữ chính cho bản quét. Sau khi tải, đọc toàn văn hoặc tìm từ khóa. Có hỗ trợ từ khóa Trung/Việt/Anh và trích dẫn số trang, không tự quyết định quyền lợi/bồi thường.

Trợ lý không tự ghi sổ, sửa hóa đơn, chọn bên nhận, đổi tiền hoặc xác nhận thanh toán. Các nút đề xuất mở màn hình để bạn kiểm tra và thao tác. Thanh toán vẫn là sandbox, không chuyển tiền hoặc kích hoạt bảo hiểm.

## Khởi động trên máy mới

Làm theo RUNBOOK.md để cài Python/Node/PostgreSQL, khởi tạo `.env` và chạy migrations. Sau khi `npm ci` trong `frontend/`, chạy từ thư mục kit:

```powershell
python scripts/setup_ocr.py
backend\.venv\Scripts\python.exe scripts/create_student_finance_fixtures.py
```

Unix:

```sh
python3 scripts/setup_ocr.py
backend/.venv/bin/python scripts/create_student_finance_fixtures.py
```

Lệnh thứ hai chỉ tạo các tệp tự soạn cho kiểm thử trong `.local/qa-documents`; không phải hóa đơn/chính sách thật và không nạp dữ liệu vào tài khoản của bạn. Không cần chạy lệnh này để dùng tệp của bạn.
