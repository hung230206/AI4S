# Chatbot Gemini trong Demo

## Thay đổi quyền riêng tư 19/10/2026 — thay thế mặc định cũ

Trang luôn bắt đầu ở Tra cứu trực tiếp. Cấp quyền tự nguyện ở Cài đặt quyền Gemini, chọn nhóm ngữ cảnh, xem trước rồi gửi. Enter gửi; Shift+Enter xuống dòng. Các lần Gemini trước chỉ được gửi lại khi đã chọn quyền lịch sử; không chuyển nội dung tra cứu nội bộ sang AI. Quyền theo phiên, tối đa một giờ, có thể thu hồi tại chat/Tài khoản.

Mặc định DEMO_ONLY chặn ngữ cảnh tài chính/tóm tắt hợp đồng cá nhân; chỉ truy xuất mẫu/tham khảo công khai khi có quyền tài liệu. Google miễn phí có thể dùng nội dung để cải thiện dịch vụ và có người đánh giá. Không sử dụng dữ liệu riêng/nhạy cảm; tra cứu trực tiếp vẫn đọc tài liệu cá nhân mà không gọi Google. Chi tiết: PRIVACY_GUIDE.md và docs/21_PRIVACY_PERMISSIONS_RESEARCH.md.


Mở **Trợ lý du học** (`/copilot`). Nếu máy chủ đã cấu hình khóa, **Gemini AI** được chọn sẵn. Bạn có thể hỏi về số dư, lịch thu/chi, hóa đơn, tỷ giá hoặc tài liệu đã tải lên; hỏi tiếp ngay trong cùng cuộc trò chuyện. Gemini trả lời theo ngôn ngữ giao diện Việt/Anh/Trung.

- **Gemini AI**: gửi câu hỏi, tối đa 3 lượt hội thoại gần nhất và phần dữ liệu liên quan tới Google để soạn câu trả lời. Thẻ nguồn bên dưới giúp mở trang đối chiếu hoặc đọc đoạn trích và số trang.
- **Tra cứu trực tiếp**: dùng dữ liệu và quy tắc của app, không gọi Gemini. Đây cũng là phản hồi dự phòng khi model lỗi, hết lượt gọi hoặc phản hồi quá thời gian; giao diện sẽ ghi rõ lý do.
- **Xóa cuộc trò chuyện**: xóa ngữ cảnh trong tab. App không lưu hội thoại vào database; tải lại trang bắt đầu cuộc trò chuyện mới. Google có chính sách xử lý dữ liệu riêng.

Trợ lý chỉ đọc và giải thích. Chuyển tiền, đổi tiền, ghi sổ và xác nhận giao dịch vẫn cần người dùng thực hiện trong luồng riêng. Số dư là dữ liệu tự khai báo; kết quả AI có thể sai và cần đối chiếu nguồn. Tỷ giá là tham chiếu theo ngày; phần thanh toán vẫn là sandbox.

## Thử từ A tới Z

1. Tạo tài khoản riêng, thêm sổ CNY số dư `1000.00`.
2. Thêm kế hoạch chi `1200.00 CNY`, hạn trong 5 ngày.
3. Chọn Gemini và hỏi: **30 ngày tới tôi có đủ tiền không?** Kiểm tra số dư cuối kỳ `-200.00 CNY` với thẻ nguồn ngân sách.
4. Hỏi tiếp: **Giải thích lại bằng hai câu ngắn.**
5. Tải tệp bảo hiểm mẫu trong Test A–Z lên Tài liệu bảo hiểm; hỏi **Hồ sơ bồi thường gồm những gì?** Đối chiếu đoạn trích, loại tài liệu và trang gốc.
6. Hỏi **Thanh toán giúp tôi ngay**: app chỉ hướng dẫn kiểm tra, không tạo giao dịch hoặc trừ tiền.
7. Chọn **Tra cứu trực tiếp**, hỏi lại để thử chế độ không gọi AI ngoài.

Khi demo Gemini, dùng dữ liệu mẫu hoặc đã ẩn danh. Không gửi hồ sơ y tế, dữ liệu cá nhân hoặc tài liệu bí mật vào gói miễn phí: [điều khoản Gemini về dữ liệu](https://ai.google.dev/gemini-api/terms#unpaid-services) giải thích cách Google xử lý đầu vào/đầu ra. Chọn tra cứu trực tiếp cho nội dung nhạy cảm.

## Cấu hình trên máy chủ

Khóa chỉ đặt trong `.env` của backend hoặc Environment của hosting. Không đưa vào frontend, GitHub, ảnh chụp hay tài liệu bàn giao.

```dotenv
GEMINI_ENABLED=true
GEMINI_API_KEY=<nhập khóa mới trong môi trường máy chủ>
GEMINI_MODEL=gemini-3.8-flash
GEMINI_TIMEOUT_SECONDS=25
```

Khởi động lại backend sau khi thay đổi. Bản local hiện đã cấu hình và đã gọi Gemini thật. Bản Render cần nhập các biến trên tại **ai4s-demo → Environment**, rồi **Manual Deploy → Deploy latest commit**. Không nhập khóa vào `NEXT_PUBLIC_*`. Xem [DEPLOY_RENDER.md](DEPLOY_RENDER.md).

Model hiện được kiểm thử là `gemini-3.8-flash`; quyền truy cập và quota phụ thuộc project Google, không có cam kết miễn phí hoặc không giới hạn. `gemini-2.5-flash` trả 404 với project mới trong lần thử này; [tài liệu model](https://ai.google.dev/gemini-api/docs/models) ghi nhận hạn chế truy cập 2.5 với project mới. Không có tự động đổi model hay thử lại nhiều lần gây phát sinh lượt gọi.

Nếu khóa đã xuất hiện trong chat hoặc nơi chia sẻ, tạo khóa thay thế trong Google AI Studio, cập nhật môi trường rồi thu hồi khóa cũ theo [hướng dẫn của Google](https://ai.google.dev/gemini-api/docs/api-key#security-and-secret-management).

## Kiểm thử cho team

PowerShell:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q
cd ../frontend
npx playwright test
cd ..
backend/.venv/Scripts/python.exe scripts/check_gemini_live.py
```

Unix:

```sh
cd backend
.venv/bin/python -m pytest -q
cd ../frontend
npx playwright test
cd ..
backend/.venv/bin/python scripts/check_gemini_live.py
```

Backend tests và ba kiểm thử UI Gemini dùng dữ liệu/provider giả lập để không tiêu quota. Lệnh `check_gemini_live.py` là kiểm tra thật, tạo tài khoản QA với dữ liệu tự soạn và gọi model đúng 3 lần; chỉ chạy khi muốn kiểm tra kết nối thực. Các máy chủ và database phải đang chạy.

## Cách triển khai

Backend gọi REST [`generateContent`](https://ai.google.dev/api/generate-content) bằng HTTPX qua host cố định, khóa trong header. Model nhận dữ liệu đã giới hạn từ các truy vấn có điều kiện chủ sở hữu: tối đa 8 sổ ngân sách, 5 hóa đơn, 5 lịch gần nhất, tỷ giá có nguồn và 3 đoạn tài liệu khớp từ khóa. Email, mật khẩu, token, thông tin bên nhận và tệp gốc không được lấy vào ngữ cảnh tự động. Câu hỏi/tài liệu vẫn có thể chứa thông tin bạn tự nhập nên cần kiểm tra trước khi gửi.

Phản hồi JSON phải qua kiểm tra schema, trạng thái hoàn thành và danh sách mã nguồn. Nguồn và đường dẫn hiển thị do máy chủ gắn lại; model không tạo nút thao tác. Không dùng function calling, agent thực thi, Google Search hoặc vector database. Trích xuất OCR/tìm kiếm từ khóa vẫn chạy ở máy chủ; Gemini là lớp diễn giải bổ sung.

Giới hạn hiện tại: 500 ký tự/câu hỏi, 6 tin nhắn lịch sử, ngữ cảnh 40.000 ký tự, đầu ra tối đa 1.200 token và timeout 25 giây mặc định. Có giới hạn bền vững 20 lần/tài khoản+IP/15 phút và 60 lần/IP proxy/15 phút. Giới hạn quota của Google có thể thấp hơn. Chưa có lưu hội thoại dài hạn, streaming từng token, tìm kiếm ngữ nghĩa hay xác minh tự động rằng mọi câu văn của AI đều đúng với trích dẫn.
