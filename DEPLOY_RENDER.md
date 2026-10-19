# Đưa Demo lên Render từ GitHub

## Quyền riêng tư Gemini (19/10/2026)

Giữ `GEMINI_DATA_MODE=DEMO_ONLY` (mặc định nếu không đặt biến). Bản miễn phí không gửi sổ tài chính hoặc tóm tắt hợp đồng cá nhân sang Google. Người dùng vẫn phải tự cấp quyền theo phiên; dữ liệu tài liệu mẫu/công khai chỉ gửi khi chọn nhóm tương ứng. Không đặt `PAID_PRIVATE` để vượt giới hạn: cần kiểm tra dự án Google thực sự trả phí, điều khoản/DPA, vùng hỗ trợ và nghĩa vụ dữ liệu của đơn vị vận hành trước. Migration `c41a15fa8b20` được launcher chạy trước khi phục vụ web; dữ liệu cũ được giữ nguyên.

Sau deploy, kiểm tra `python scripts/check_privacy_live.py --url https://ai4s-demo.onrender.com --with-gemini --evidence submission/evidence/privacy-render-live.json`. Lệnh tạo tài khoản QA và dùng dữ liệu tự soạn, tối đa một lượt Gemini; bỏ `--with-gemini` nếu không muốn gọi mô hình. Không gửi khóa vào tham số dòng lệnh hoặc chat.


Phương án được chọn: hosting miễn phí để demo, chạy độc lập với máy cá nhân. Đây chưa phải môi trường vận hành tiền thật. App luôn dùng MOCK, không chuyển tiền hoặc kích hoạt bảo hiểm.

## Bấm để bắt đầu

[Deploy Demo to Render](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fhung230206%2FAI4S)

1. Đăng ký/đăng nhập [Render](https://dashboard.render.com/register), có thể dùng GitHub. Nếu Render yêu cầu quyền repo, chọn `hung230206/AI4S`.
2. Mở liên kết deploy ở trên hoặc chọn **New → Blueprint**, nhập URL repo và chọn nhánh `main`.
3. Xem lại màn hình tài nguyên: một web service `ai4s-demo` và một PostgreSQL `ai4s-demo-db`, **cả hai phải là Free**. Không chọn gói trả phí khi chỉ muốn demo miễn phí. Nếu tài khoản có yêu cầu thanh toán/xác minh, tự xem điều kiện Render trước khi tiếp tục.
4. Tạo Blueprint và chờ build/deploy. Bí mật được Render sinh riêng, không lấy `.env` trên máy cá nhân. Tên/URL thực tế do Render cấp; không tự đoán URL từ ví dụ trong tài liệu.
5. Khi service báo **Live**, mở URL HTTPS do Render cấp, thêm `/test-lab`, tạo tài khoản riêng và chạy các bước trong ACCEPTANCE_TESTS.md. Máy bạn có thể tắt.

Không gửi mật khẩu, database URL có mật khẩu, cookie hoặc API key vào chat/nhóm. Muốn Codex triển khai và theo dõi trực tiếp, kết nối tài khoản Render trong Codex, rồi chọn workspace khi được hỏi. Nếu chưa đăng nhập/kết nối, việc chuẩn bị mã và nút deploy không có nghĩa app đã lên cloud.

## Mô hình chạy

```text
Trình duyệt → HTTPS Render → Next.js standalone ($PORT)
                                  ↓ proxy cùng origin
                              FastAPI (127.0.0.1:8000)
                                  ↓ private network
                              PostgreSQL Render
```

Một container giữ cùng origin cho UI/API, tránh cấu hình CORS giữa hai web service Free và không mở API riêng ra Internet. `render.yaml` chỉ tạo một web service và một DB. Render Free không nhận private-network traffic vào web service nên không dùng kiến trúc hai web service kết nối private với nhau. DB được đặt `ipAllowList: []` để chặn kết nối từ Internet; web service vẫn kết nối qua private network trong cùng vùng Singapore.

`deploy/cloud.Dockerfile` build frontend ở chế độ standalone, kèm static assets; cài Python, Node, OCR dependencies và ba model trong image. Các file upload, văn bản OCR, dữ liệu tài khoản, sổ và sự kiện được lưu trong PostgreSQL, không phụ thuộc thư mục tạm của container.

`scripts/cloud_start.py` chuyển URL PostgreSQL của Render sang driver psycopg đã cài, lấy origin từ `RENDER_EXTERNAL_URL` hoặc `PUBLIC_APP_URL`, bật cookie Secure, kiểm tra bí mật và giữ chế độ sandbox. Launcher migrate/seed không reset dữ liệu, khởi động API một worker, đợi health rồi chạy UI; nếu một tiến trình dừng, tiến trình còn lại do nó tạo cũng được dừng. Không tự dùng DB localhost khi thiếu biến cloud.

## Giới hạn miễn phí cần biết

- Web service ngủ sau 15 phút không có request; lần mở lại có thể chờ khoảng một phút. Không dùng ping giả để né giới hạn.
- **PostgreSQL Free hết hạn sau 30 ngày**, không phải nơi lưu dữ liệu lâu dài. Render có thời gian gia hạn nâng cấp rồi có thể xóa DB. Xuất hồ sơ thử trước hạn; nếu cần lưu lâu, chọn một DB/gói phù hợp và xem giá hiện tại trong Dashboard.
- Web Free chỉ có tài nguyên nhỏ. Cấu hình OCR tối đa một tiến trình, Node heap 192 MB; nhận dạng vẫn giữ giới hạn 75 giây. Ảnh rõ/text PDF là bộ thử đầu tiên. PDF scan dày hoặc nhiều người dùng đồng thời có thể chạm OCR_TIMEOUT/giới hạn RAM; bản build thành công không chứng minh OCR nặng sẽ chạy đủ nhanh trên Free.
- Dùng chung quota giờ chạy/bandwidth/build của workspace. Xem Billing/usage; không có bảo đảm chạy 24/7 hoặc SLA.
- DB cloud ban đầu trống ngoài các fixture seed. Không tự chuyển tài khoản/tài liệu riêng từ máy đang chạy lên cloud.
- Đây là public demo, chưa bổ sung email recovery/MFA, worker sandbox chống file độc hại hay chính sách retention đầy đủ. Dùng dữ liệu mẫu để chia sẻ/test; giới hạn hiện hành xem SECURITY_SELF_ASSESSMENT.md.

## Cập nhật sau khi sửa code

Blueprint dùng `autoDeployTrigger: commit` theo lựa chọn auto deploy của chủ dự án. Push lên `main` sẽ kích hoạt build khi service đã liên kết Git provider và bật **On Commit**. Nếu chỉ dùng public repository URL mà chưa liên kết Git provider, dùng **Manual Deploy → Deploy latest commit** trên service. Không tạo lại DB hoặc xóa tài nguyên chỉ để cập nhật code. Bí mật và bản ghi hiện có được giữ nguyên.

Nếu thêm custom domain, khai báo `PUBLIC_APP_URL=https://ten-mien-cua-ban` trong Environment và deploy lại. Giữ nguyên `COOKIE_SECURE=true`. Chỉ một origin chính được launcher chấp nhận; không nhập wildcard hoặc danh sách URL vào biến này.

## Khi gặp lỗi

- **Build failed:** xem Build logs, lấy dòng lỗi và commit, không copy Environment/secrets. Docker build cần tải dependencies và model OCR lần đầu.
- **Deploy failed/health failed:** kiểm tra DB Available, cùng region, DATABASE_URL liên kết đúng; bí mật đủ dài; API khởi động trước UI. Không thay DATABASE_URL bằng địa chỉ localhost của máy bạn.
- **FORBIDDEN khi đăng ký/thao tác:** kiểm tra đang dùng đúng HTTPS origin; custom domain cần PUBLIC_APP_URL. Không bỏ CSRF/Origin để sửa tạm.
- **OCR_TIMEOUT/OCR_BUSY:** đợi lượt đang chạy, chọn ngôn ngữ chính, thử một ảnh rõ hoặc PDF có lớp chữ. OCR nâng cao có thể cần gói đủ CPU/RAM; không tự nâng gói có phí.
- **Không có kết quả thanh toán thử:** giữ PROVIDER_WORKER_ENABLED=true, xem runtime logs. Không gọi simulate/replay bằng tài khoản thường.
- **DB hết hạn/quota hết:** xem Render Dashboard; ứng dụng không tự mua gói hoặc tạo lại DB làm mất dữ liệu.

## Đối chiếu và kiểm thử

Kết quả thực tế của đợt chuẩn bị cloud được ghi trong IMPLEMENTATION_REPORT.md và submission/evidence/cloud-readiness.json. Phân biệt: kiểm tra schema/build/launcher tại máy với Docker build trên Linux và URL HTTPS thực tế. Chỉ ghi đã deploy khi service Live và kiểm tra được URL do Render cấp.

Nguồn chính thức, đối chiếu ngày 18/10/2026:

- https://render.com/docs/deploy-to-render
- https://render.com/docs/blueprint-spec
- https://render.com/docs/free
- https://render.com/docs/private-network
- https://render.com/docs/environment-variables
- https://render.com/docs/docker

## Chatbot Gemini tùy chọn

Trong Environment của service hiện có, đặt `GEMINI_ENABLED=true`, `GEMINI_API_KEY` bằng khóa mới của project và `GEMINI_MODEL=gemini-3.8-flash`; timeout mặc định 25 giây. Sau đó deploy latest commit. Khóa chỉ lưu ở Render, không đặt trong render.yaml hoặc NEXT_PUBLIC_*. Không có khóa thì Tra cứu trực tiếp vẫn hoạt động. Hướng dẫn và các kiểm thử thật: [GEMINI_GUIDE.md](GEMINI_GUIDE.md).
