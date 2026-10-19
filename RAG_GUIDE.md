# Test kho RAG và tài khoản quản trị

- Người dùng: https://ai4s-demo.onrender.com/knowledge — **Hỏi đáp bảo hiểm RAG** trên menu.
- Quản trị: https://ai4s-demo.onrender.com/admin/rag — đăng nhập bằng tài khoản test trong `.local/RAG_ADMIN_TEST.txt` hoặc `.local/rag-admin-test.json` trên máy dự án. Đây là tệp riêng, không nằm trên GitHub hoặc ZIP bàn giao. Tài khoản thường và mã vận hành sandbox không có quyền quản trị.

Đã kiểm thử trên Render: đăng nhập admin và đầy đủ 7 nhóm luồng RAG/CRUD. Gemini diễn giải hiện bị **TIMEOUT** khi gọi thật; trích đoạn gốc có nguồn vẫn dùng được. Không coi kết quả chuyển sang trích đoạn là câu trả lời Gemini.

## Tệp tải lên để thử

Mở thư mục `fixtures/rag_upload_samples/`: có `student-policy-sample-en.txt`, `claims-guide-sample-vi.md`, `insurance-glossary-sample-zh.txt`. Đây là bản rời của ba nguồn mẫu tự soạn đã có trong kho, dùng để thử thêm/thay tệp; không phải hợp đồng thật. `README.md` trong thư mục ghi thông tin metadata và câu hỏi đối chiếu. Không tải README thành nguồn bảo hiểm.

## Một luồng đầy đủ

1. Đăng nhập admin. Bấm **Thêm tài liệu**. Nhập tên, tác giả, loại nguồn, quyền sử dụng, ngôn ngữ và lãnh thổ.
2. Chọn **Soạn văn bản** hoặc **Tải PDF / ảnh / TXT**. Tải tệp cần chọn **Đồng ý** trong popup xử lý đúng tệp. Lưu thành **bản nháp**; người dùng chưa thấy tài liệu.
3. **Đọc và kiểm tra**: đối chiếu từng trang, xem SHA-256 và số đoạn. Nhập câu hỏi, bấm **Thử truy xuất bản nháp**; bước này chạy nội bộ, chưa gửi Google.
4. Bấm **Xuất bản**. Popup có hai nút Đồng ý / Không đồng ý và link chi tiết. Đồng ý xác nhận quyền công bố, nội dung đã kiểm tra và không chứa thông tin cá nhân/nhạy cảm. Người dùng trong ứng dụng mới có thể đọc, tải và hỏi từ nguồn này.
5. Mở **Hỏi đáp bảo hiểm RAG**, chọn nguồn và hỏi. Mặc định là **Trích đoạn tại máy chủ**. Kết quả có trích đoạn gốc, trang, phiên bản và nút **Đọc trang nguồn**. Câu ngoài dữ liệu sẽ báo chưa đủ thông tin.
6. Nếu muốn Gemini diễn giải, bấm **Gemini diễn giải**, chọn Đồng ý, có thể xem trước dữ liệu sẽ gửi rồi gửi câu hỏi. Tối đa ba đoạn, không gửi tệp gốc/hồ sơ cá nhân. Enter gửi, Shift+Enter xuống dòng. Khi nhà cung cấp lỗi, ứng dụng hiển thị nguyên văn và lý do; không giả làm câu trả lời AI.
7. Quay lại admin **Sửa**. Văn bản tự soạn sửa trực tiếp được; PDF/ảnh phải **Thay tệp gốc** để giữ trích dẫn khớp nguồn. Mọi sửa đổi đưa tài liệu về nháp và cập nhật chỉ mục trong cùng giao dịch. Kiểm tra rồi xuất bản lại.
8. Mở liên kết trích dẫn phiên bản cũ để kiểm tra: hệ thống báo nguồn đã thay đổi. Hỏi lại sẽ dùng phiên bản mới.
9. **Gỡ xuất bản** hoặc **Chuyển vào thùng rác**: không dùng nguồn này cho câu hỏi mới. Thùng rác có thể khôi phục thành nháp. Lịch sử giữ thao tác, phiên bản và mã băm; không có chức năng khôi phục toàn bộ nội dung phiên bản cũ.

Kho có sẵn ba tài liệu **tự soạn để kiểm thử**, không phải hợp đồng nhà bảo hiểm. Nguồn công khai thật cần URL gốc và quyền sử dụng do admin kiểm tra. RAG không train lại Gemini và không xác minh tài liệu là thật. Nó bổ sung hỏi đáp có nguồn cho Topic D; phân tích quyền lợi và chuẩn bị hồ sơ ở **Bảo hiểm & hồ sơ** vẫn yêu cầu người dùng đối chiếu hợp đồng.

## Tạo admin trên máy khác

PowerShell, từ `backend/`:

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m app.seed
.venv/Scripts/python.exe -m app.rag_admin --email rag-admin@example.com
```

Unix dùng `.venv/bin/python` tương ứng. CLI ghi mật khẩu ngẫu nhiên vào `.local/rag-admin-test.json`, không in mật khẩu và không thay mật khẩu tài khoản đã tồn tại. Không có API tự đăng ký quyền admin.

Trên Render: đặt `RAG_ADMIN_EMAIL` và `RAG_ADMIN_PASSWORD` bằng giá trị trong tệp riêng, rồi triển khai. Khởi tạo chỉ tạo tài khoản mới; không nâng quyền tài khoản thường đã trùng email và không đặt lại mật khẩu admin sau mỗi lần deploy. Sau khi đổi mật khẩu trong Tài khoản, cập nhật thông tin bàn giao riêng; các bản triển khai không tự đồng bộ mật khẩu giữa các cơ sở dữ liệu.
