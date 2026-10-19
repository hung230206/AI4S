# Test kho RAG và tài khoản quản trị

- Người dùng: https://ai4s-demo.onrender.com/knowledge — **Hỏi đáp bảo hiểm RAG** trên menu.
- Quản trị: https://ai4s-demo.onrender.com/admin/rag — đăng nhập bằng tài khoản test trong `.local/RAG_ADMIN_TEST.txt` hoặc `.local/rag-admin-test.json` trên máy dự án. Đây là tệp riêng, không nằm trên GitHub hoặc ZIP bàn giao. Tài khoản thường và mã vận hành sandbox không có quyền quản trị.

Luồng mới tại **Hỏi đáp bảo hiểm RAG**: hỏi → tìm đoạn phù hợp trong kho → Gemini giải thích bằng ngôn ngữ giao diện → đối chiếu trang nguồn. Lần hỏi đầu mở popup **Đồng ý / Không đồng ý** trước khi gửi tới Google. Đồng ý tiếp tục câu hỏi đang chờ; Không đồng ý không gửi câu hỏi và vẫn cho phép tra cứu trích đoạn. Có thể xem trước dữ liệu gửi hoặc thu hồi quyền.

Gemini 3.8 đã tái hiện lỗi 503/timeout; cấu hình mới ưu tiên 3.5 Flash-Lite. Nếu máy chủ còn cấu hình 3.8, giới hạn lần thử đầu 8 giây rồi thử một model dự phòng, trong tổng hạn 25 giây. Giao diện ghi đúng model thực sự trả lời. Khi cả hai không trả lời, hệ thống hiển thị trích đoạn và lý do lỗi, không giả làm câu trả lời AI.

## Tài liệu Trung Quốc và tệp mẫu để thử

Tài liệu thật để tải lên: `output/China_RAG_Corpus/prepared/`, điền thông tin trong `metadata.csv`. Không nhập lại bản trùng vào kho đang có đủ 9 nguồn. Chọn nguồn NFRA 2021 rồi hỏi: **Bảo hiểm sức khỏe ngắn hạn có bảo đảm tái tục không?**

Nếu chỉ muốn thử CRUD bằng tài liệu giả lập, mở `fixtures/rag_upload_samples/`: có `student-policy-sample-en.txt`, `claims-guide-sample-vi.md`, `insurance-glossary-sample-zh.txt`. Đây là bản rời của ba nguồn mẫu tự soạn đã có trong kho, dùng để thử thêm/thay tệp; không phải hợp đồng thật. `README.md` trong thư mục ghi thông tin metadata và câu hỏi đối chiếu. Không tải README thành nguồn bảo hiểm.

## Một luồng đầy đủ

1. Đăng nhập admin. Bấm **Thêm tài liệu**. Nhập tên, tác giả, loại nguồn, quyền sử dụng, ngôn ngữ và lãnh thổ.
2. Chọn **Soạn văn bản** hoặc **Tải PDF / ảnh / TXT**. Tải tệp cần chọn **Đồng ý** trong popup xử lý đúng tệp. Lưu thành **bản nháp**; người dùng chưa thấy tài liệu.
3. **Đọc và kiểm tra**: đối chiếu từng trang, xem SHA-256 và số đoạn. Nhập câu hỏi, bấm **Thử truy xuất bản nháp**; bước này chạy nội bộ, chưa gửi Google.
4. Bấm **Xuất bản**. Popup có hai nút Đồng ý / Không đồng ý và link chi tiết. Đồng ý xác nhận quyền công bố, nội dung đã kiểm tra và không chứa thông tin cá nhân/nhạy cảm. Người dùng trong ứng dụng mới có thể đọc, tải và hỏi từ nguồn này.
5. Mở **Hỏi đáp bảo hiểm RAG**, chọn nguồn và hỏi. Nếu đã cấu hình Gemini, lần đầu chọn **Đồng ý** trong popup để tiếp tục câu hỏi qua RAG + Gemini. Kết quả có giải thích, trích đoạn gốc, trang, phiên bản và nút **Đọc trang nguồn**. Không có bằng chứng thì báo thiếu thông tin và không gọi LLM để đoán.
6. Trong phiên đã cấp quyền, câu hỏi tiếp theo tự qua RAG rồi Gemini. Có thể **Xem dữ liệu sẽ gửi**, **Thu hồi quyền Gemini** hoặc chọn **Trích đoạn tại máy chủ**. Tối đa ba đoạn, không gửi tệp gốc/hồ sơ cá nhân. Enter gửi, Shift+Enter xuống dòng. Chọn **Bật trả lời RAG + Gemini** sau khi từ chối chỉ bật quyền, không tự gửi lại câu đã từ chối.
7. Quay lại admin **Sửa**. Văn bản tự soạn sửa trực tiếp được; PDF/ảnh phải **Thay tệp gốc** để giữ trích dẫn khớp nguồn. Mọi sửa đổi đưa tài liệu về nháp và cập nhật chỉ mục trong cùng giao dịch. Kiểm tra rồi xuất bản lại.
8. Mở liên kết trích dẫn phiên bản cũ để kiểm tra: hệ thống báo nguồn đã thay đổi. Hỏi lại sẽ dùng phiên bản mới.
9. **Gỡ xuất bản** hoặc **Chuyển vào thùng rác**: không dùng nguồn này cho câu hỏi mới. Thùng rác có thể khôi phục thành nháp. Lịch sử giữ thao tác, phiên bản và mã băm; không có chức năng khôi phục toàn bộ nội dung phiên bản cũ.

Kho live/local hiện có 9 nguồn tham khảo Trung Quốc thật (IAC, NFRA, NHSA); ba mẫu tự soạn đã gỡ về nháp. Xem docs/23_CHINA_RAG_CORPUS.md và output/China_RAG_Corpus/README.md để chọn nguồn, upload và hỏi thử. Nguồn công khai thật cần URL gốc và quyền sử dụng do admin kiểm tra. RAG không train lại Gemini và không xác minh tài liệu là thật. Nó bổ sung hỏi đáp có nguồn cho Topic D; phân tích quyền lợi và chuẩn bị hồ sơ ở **Bảo hiểm & hồ sơ** vẫn yêu cầu người dùng đối chiếu hợp đồng.

## Tạo admin trên máy khác

PowerShell, từ `backend/`:

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m app.seed
.venv/Scripts/python.exe -m app.rag_admin --email rag-admin@example.com
```

Unix dùng `.venv/bin/python` tương ứng. CLI ghi mật khẩu ngẫu nhiên vào `.local/rag-admin-test.json`, không in mật khẩu và không thay mật khẩu tài khoản đã tồn tại. Không có API tự đăng ký quyền admin.

Trên Render: đặt `RAG_ADMIN_EMAIL` và `RAG_ADMIN_PASSWORD` bằng giá trị trong tệp riêng, rồi triển khai. Khởi tạo chỉ tạo tài khoản mới; không nâng quyền tài khoản thường đã trùng email và không đặt lại mật khẩu admin sau mỗi lần deploy. Sau khi đổi mật khẩu trong Tài khoản, cập nhật thông tin bàn giao riêng; các bản triển khai không tự đồng bộ mật khẩu giữa các cơ sở dữ liệu.
