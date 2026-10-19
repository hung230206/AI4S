# Gemini và RAG trong Demo

## Hỏi đáp bảo hiểm: RAG + Gemini

Mở `/knowledge`, chọn nguồn và nhập câu hỏi. Ứng dụng tìm các đoạn phù hợp trong kho do admin xuất bản, rồi đưa tối đa ba đoạn cho Gemini giải thích bằng ngôn ngữ giao diện. Kết quả có đoạn gốc, trang và phiên bản để đối chiếu. Không đủ nguồn thì báo thiếu thông tin, không gọi model để suy đoán quyền lợi.

Lần đầu bấm hỏi mở popup **Đồng ý / Không đồng ý** với link chi tiết. Đồng ý tiếp tục câu đang chờ; Không đồng ý không gửi câu hỏi và vẫn cho phép tra cứu tại máy chủ. Có thể xem trước dữ liệu gửi, chọn **Trích đoạn tại máy chủ** hoặc thu hồi quyền. Enter gửi; Shift+Enter xuống dòng. Quyền theo phiên, tối đa một giờ, không tự gia hạn.

Kho có sẵn ba nguồn mẫu tự soạn, không phải hợp đồng bảo hiểm thật. Các nguồn do admin xuất bản được dùng chung trong ứng dụng; hồ sơ cá nhân không tự đưa vào kho. Luồng quản trị, tài khoản test và tệp upload: [RAG_GUIDE.md](RAG_GUIDE.md).

## Trợ lý du học

`/copilot` bắt đầu ở **Tra cứu trực tiếp**. Chọn Gemini để mở popup cấp quyền; cấp quyền ở đây chỉ bật chế độ, không tự gửi câu hỏi. Chỉ các lượt hội thoại Gemini cùng quyền còn hiệu lực mới được dùng làm lịch sử giới hạn. Không tự chuyển nội dung đã tra cứu nội bộ sang Google.

Giao diện cấp phạm vi SAMPLE_ASSISTANT cố định: câu hỏi, tối đa ba lượt gần nhất và tối đa ba đoạn mẫu/tham khảo phù hợp. Không cấp quyền dữ liệu thu chi, tóm tắt hợp đồng cá nhân hoặc hồ sơ bồi thường. Khi thích hợp, các đoạn từ kho RAG đã xuất bản được điền vào các vị trí ngữ cảnh còn trống, vẫn giữ tổng tối đa ba đoạn.

Google miễn phí có chính sách xử lý dữ liệu riêng. Luồng demo chỉ dành cho nội dung mẫu/công khai không nhạy cảm; xem [thông báo quyền riêng tư](PRIVACY_GUIDE.md) và [điều khoản Google](https://ai.google.dev/gemini-api/terms). Chat không thực hiện thanh toán, đổi tiền, phê duyệt bảo hiểm hay gửi hồ sơ.

## Model và giới hạn chờ

Kiểm tra cùng khóa đã tái hiện Gemini 3.8 trả 503; Gemini 3.5 Flash-Lite trả lời thành công. Cấu hình mới ưu tiên `gemini-3.5-flash-lite`, với thinking thấp. API và giao diện hiển thị model thực sự trả lời.

Nếu cấu hình cũ vẫn dùng 3.8, lần thử đầu có hạn 8 giây, rồi chỉ thử thêm một model dự phòng khi timeout, lỗi mạng/5xx hoặc model không khả dụng. Cả hai lần nằm trong tổng hạn 25 giây. Không thử lại khi sai khóa, hết quota, dữ liệu sai hoặc đầu ra không hợp lệ. Một câu hỏi có thể phát sinh tối đa hai lần gọi Google; hạn mức câu hỏi của ứng dụng giữ nguyên.

Nếu không có model trả lời hợp lệ, kết quả được ghi rõ là tra cứu/trích đoạn dự phòng cùng mã lý do. Citation IDs không bảo đảm mọi câu AI đều đúng; luôn đối chiếu đoạn nguồn.

## Cấu hình máy chủ

Chỉ đặt trong `.env` hoặc Environment của hosting, không đặt trong frontend hoặc `NEXT_PUBLIC_*`:

```dotenv
GEMINI_ENABLED=true
GEMINI_API_KEY=<khóa trong môi trường máy chủ>
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite
GEMINI_PRIMARY_TIMEOUT_SECONDS=8
GEMINI_TIMEOUT_SECONDS=25
GEMINI_DATA_MODE=DEMO_ONLY
```

Khởi động lại backend sau khi đổi cấu hình; Render cần deploy. Blueprint đã khai báo các lựa chọn model/timeout, không chứa API key. Không có khóa thì tra cứu nội bộ vẫn hoạt động. Có thể để GEMINI_FALLBACK_MODEL trống để tắt lần gọi dự phòng; nếu hai model giống nhau thì chỉ gọi một lần.

## Kiểm thử

Từ thư mục dự án, PowerShell:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q
cd ../frontend
npm run lint
npx tsc --noEmit
cd ..
backend/.venv/Scripts/python.exe scripts/check_rag_live.py --url https://ai4s-demo.onrender.com --admin-credentials .local/rag-admin-test.json --with-gemini
```

Unix thay đường dẫn Python bằng `backend/.venv/bin/python` (hoặc `.venv/bin/python` khi đang trong backend). Bộ pytest và trình duyệt thông thường dùng model giả lập; `--with-gemini` mới phát sinh yêu cầu thật với nội dung kiểm thử tự soạn. `scripts/check_rag_browser_real.mjs` kiểm tra giao diện với một yêu cầu Google thật, chỉ cho phép máy QA localhost.

Kết quả thực tế và phiên bản triển khai: [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md). Cơ sở kỹ thuật: [docs/22_TOPIC_D_MANAGED_RAG.md](docs/22_TOPIC_D_MANAGED_RAG.md).
