# Nghiệm thu Demo từ A đến Z

Mở `/test-lab`, tạo tài khoản riêng và dùng bộ mẫu tải ngay trong app. Mục tiêu là kiểm tra tác vụ hoạt động và truy vết được dữ liệu; tiền trong sổ là dữ liệu tự khai báo, thanh toán là sandbox.

| Ca | Thao tác | Kết quả cần thấy |
|---|---|---|
| A01 | Tải ZIP, giải nén | Có thư mục hóa đơn, bảo hiểm, thử lỗi và hướng dẫn |
| A02 | Upload `01_en_800.png`, chọn Tiếng Anh | Mã DEMO-20261018-EN-800, Demo University, Demo Education, 800.00 CNY, hạn 2026-11-01; lưu bị khóa trước đối chiếu |
| A03 | Đối chiếu và lưu | Có hóa đơn riêng, tải lại được nguồn gốc đúng byte; upload không tự thanh toán |
| A04 | Tạo sổ 1.000 CNY, đưa hóa đơn vào kế hoạch | Hiện tại 1.000, dự phóng 30 ngày 200; thêm lại không trùng kế hoạch |
| A05 | Lấy giá trị VND | Có nguồn/ngày Frankfurter; tổng tính ở server, không coi phí ứng dụng 0 là phí ngân hàng 0 |
| A06 | Upload policy Việt 3 trang, loại TEST_FIXTURE | Tìm hồ sơ bồi thường thấy đoạn trang 2; loại trừ thấy trang 3 |
| A07 | Upload PDF BFSU gốc tải từ nguồn, loại PUBLIC_REFERENCE | Phải điền URL; đọc bản scan và tìm `hospital`/`理赔`, dẫn trang 1; không hiển thị là hợp đồng cá nhân đã xác thực |
| A08 | SUCCESS, tích đồng ý, chạy thử | PROCESSING trước; vài giây sau SUCCEEDED do webhook có chữ ký; không cần mã vận hành |
| A09 | Mở biên nhận | Có nhãn NO REAL FUNDS MOVED; không xác nhận trường/bảo hiểm nhận tiền |
| A10 | Mở sổ, xác nhận kỳ hóa đơn đã chi | Số dư 200; dự phóng vẫn 200, không trừ 800 thêm lần nữa |
| A11 | Tải hồ sơ ZIP ở giao dịch | Có nguồn, hash, quote, consent, event, receipt và plan/ledger nếu có; không có mật khẩu/token/mã vận hành |
| A12 | DECLINED với hóa đơn khác | FAILED, không có biên nhận; báo giá mới và consent mới cho phép thử lại SUCCESS |
| A13 | Đổi phương thức sau khi tích đồng ý | Checkbox được bỏ chọn; không tự gửi request thanh toán |
| A14 | Gửi lại cùng request/idempotency key | Không tạo provider intent hoặc khoản ghi sổ thứ hai |
| A15 | PUBLIC_REFERENCE không URL | Bị từ chối với DOCUMENT_SOURCE_REQUIRED; không tạo bản ghi |
| A16 | Tệp USD/PDF trắng/PDF hỏng/CSV | Cảnh báo sai tiền tệ hoặc lỗi định dạng/không có chữ theo bộ mẫu |
| A17 | Đăng nhập tài khoản khác | Không tải được nguồn, hồ sơ hoặc trạng thái của tài khoản trước |
| A18 | Đăng xuất rồi gọi lại API | Phiên bị thu hồi và trả 401 |

Ngày trong mẫu được cố định theo bộ dữ liệu 18/10/2026. Nếu test sau hạn hóa đơn, sửa ngày đến hạn khi đối chiếu và ghi rõ đã sửa; không mô tả dữ liệu mẫu là hóa đơn thật. Với hóa đơn có số khác 800 hoặc sổ không phải 1.000, tự tính lại giá trị kỳ vọng, không ép UI phải hiển thị ví dụ 200.

## Kiểm thử kỹ thuật nâng cao

Chọn MANUAL trước khi đồng ý, xác nhận tới PROCESSING rồi người vận hành mở bảng riêng bằng mã trong `.env`. Mã giao dịch lấy từ URL hoặc trang chi tiết. Phát outcome sẽ tự điền `evt_...`; Phát lại dùng cùng ID, backend nhận trùng và không cấp biên nhận lần hai. API simulate/replay vẫn yêu cầu role OPERATOR được máy chủ xác thực; tài khoản sinh viên không có quyền.

Bộ backend còn thử chữ ký giả, timestamp quá 5 phút, amount/currency sai, quote hết hạn/tamper, xung đột request key, thứ tự sự kiện và cạnh tranh ghi. Các ca này không yêu cầu người thử nhập raw webhook bằng tay; xem test_payments.py và test_journey.py.

## Bằng chứng và cách báo lỗi

Khi báo lỗi, gửi tên ca, URL trang, thời điểm, tên tệp mẫu, bước vừa bấm và thông báo lỗi. Có thể gửi hồ sơ ZIP của dữ liệu mẫu; không gửi cookie, mật khẩu hoặc `.env`. Không đưa tài liệu cá nhân vào nhóm khi chưa kiểm tra nội dung.

`submission/evidence/acceptance-live.json` ghi kết quả gọi API thực, có hash của PDF gốc nếu chạy tùy chọn nguồn công khai. `backend-junit.xml` và `browser-results.json` ghi kết quả suite. IMPLEMENTATION_REPORT.md phân biệt kiểm tra đã chạy với phần chưa chạy trên Docker/Unix.
