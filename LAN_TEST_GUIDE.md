# Cho bạn bè cùng Wi-Fi dùng thử

Địa chỉ đã cấu hình ngày 18/10/2026: **http://192.168.1.14:3000**. Địa chỉ trước đó `192.168.1.2` đã thay đổi do mạng cấp lại IP.

Gửi địa chỉ này cho bạn bè. Mỗi người mở bằng Chrome/Edge trên máy hoặc điện thoại cùng Wi-Fi, chọn **Tạo tài khoản**, rồi thử thêm hóa đơn, xem giá trị VND, tải tài liệu và tìm trích dẫn. Không cần cài Node, Python hay tải mã nguồn trên máy người thử. Tài khoản riêng có dữ liệu riêng; nút dùng dữ liệu mẫu mở không gian sandbox dùng chung.

Máy chủ cần bật, kết nối Wi-Fi và giữ hai tiến trình API/giao diện chạy. Địa chỉ localhost chỉ dùng trên máy chủ. Link LAN không dùng được ở mạng khác. Thanh toán vẫn là sandbox.

## Chạy lại trên Windows

Tại thư mục kit, cấu hình IP hiện tại (script tự đọc IPv4 của mạng có gateway; dùng `-Address` nếu có nhiều adapter):

```powershell
.\scripts\configure_lan.ps1
# Hoặc: .\scripts\configure_lan.ps1 -Address 192.168.1.14
```

Nếu hai máy chủ đang chạy, dừng bằng Ctrl+C trong các terminal của chúng trước khi chạy lại. Terminal API, từ thư mục kit:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

Terminal giao diện, từ thư mục kit:

```powershell
cd frontend
npm run dev:lan
```

Giao diện nhận kết nối LAN trên cổng 3000 và chuyển `/api/v1/*` về API cục bộ. PostgreSQL và API vẫn chỉ lắng nghe loopback. Không cần mở cổng 5434 hoặc 8000. Origin được cho phép bằng địa chỉ cụ thể; cookie phiên và CSRF vẫn được kiểm tra.

## Unix

Thay `192.168.1.14` bằng IPv4 của máy chủ. Terminal API từ `backend/`:

```sh
FRONTEND_EXTRA_ORIGINS=http://192.168.1.14:3000 .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal giao diện từ `frontend/`:

```sh
LAN_ALLOWED_HOSTS=192.168.1.14 NEXT_PUBLIC_API_BASE_URL= npm run dev:lan
```

## Nếu máy bạn bè không mở được

1. Kiểm tra gõ đúng `http://192.168.1.14:3000`, không dùng `localhost` hoặc `https`.
2. Cả hai máy phải cùng mạng; guest Wi-Fi hoặc mạng có client isolation có thể chặn thiết bị truy cập nhau.
3. Cho phép Node.js qua Windows Firewall. Máy hiện tại đã có rule cho Node.js trên profile Public. Không cần tắt firewall.
4. Nếu đổi mạng hoặc router cấp IP khác, chạy lại script cấu hình, khởi động lại API/giao diện rồi gửi địa chỉ mới.

Chứng cứ kiểm thử trên máy chủ qua IP LAN không xác nhận được chính sách cách ly thiết bị của router; cần một người thử mở link trên thiết bị thứ hai để xác nhận bước đó.

## Lặp lại kiểm thử qua địa chỉ LAN

PowerShell, từ `frontend/`:

```powershell
$env:PLAYWRIGHT_BASE_URL = 'http://192.168.1.14:3000'
npm run test:e2e
```

Unix:

```sh
PLAYWRIGHT_BASE_URL=http://192.168.1.14:3000 npm run test:e2e
```
