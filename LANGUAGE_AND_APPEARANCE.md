# Đổi ngôn ngữ và giao diện

Ở đầu trang, chọn **Tiếng Việt**, **English** hoặc **中文**. Nút này dùng được cả trước và sau khi đăng nhập.

Nút biểu tượng **mặt trăng / mặt trời** chuyển trực tiếp giữa sáng và tối bằng một lần bấm. Khi chưa chọn, giao diện tự theo thiết bị; sau khi bấm, web ưu tiên lựa chọn của bạn.

Web nhớ lựa chọn trên trình duyệt hiện tại, giữ lại khi tải lại trang và đồng bộ giữa các tab cùng địa chỉ. Máy hoặc trình duyệt khác chọn riêng. Khi trình duyệt chặn lưu trữ, lựa chọn vẫn dùng trong tab hiện tại nhưng không bảo đảm được lưu sau khi đóng/tải lại.

Đổi ngôn ngữ khi đang nhập sẽ giữ các trường đang nhập. Giao diện, menu, form, hướng dẫn và nhãn trạng thái có bản dịch; dấu phân cách tiền và ngày hiển thị theo ngôn ngữ, thời gian vẫn theo Việt Nam. Số tiền gửi lên máy chủ và quy tắc làm tròn không đổi.

Tên, nội dung người dùng nhập, chứng từ, đoạn trích, câu trả lời từ dữ liệu tài khoản và thông báo nguyên gốc từ máy chủ giữ ngôn ngữ gốc. Trợ lý hiện hỗ trợ câu hỏi Việt/Anh theo quy tắc; chọn giao diện Trung không bổ sung khả năng hiểu câu hỏi Trung. Ngôn ngữ OCR chọn riêng theo chữ trong tệp, không theo ngôn ngữ giao diện. Nút chọn tệp và lịch có thể theo ngôn ngữ của trình duyệt/hệ điều hành.

Biên nhận luôn giữ cảnh báo `SIMULATED TRANSACTION — NO REAL FUNDS MOVED`. Khi in từ chế độ tối, biên nhận chuyển sang nền trắng để đọc rõ.

Để thử: nhập dở một hóa đơn, chuyển English rồi 中文, kiểm tra dữ liệu còn nguyên; bấm nút mặt trăng để bật tối, tải lại; mở tab khác và bấm nút mặt trời để về sáng. Để kiểm tra tự động:

```powershell
cd frontend
npx playwright test preferences.spec.ts
```

```sh
cd frontend
npx playwright test preferences.spec.ts
```

Máy chủ frontend và backend phải đang chạy. Xem `TEAM_HANDOFF.md` để khởi động. Bản cập nhật trên GitHub cần **Manual Deploy → Deploy latest commit** trên Render trước khi có ở web online; xem `DEPLOY_RENDER.md`.
