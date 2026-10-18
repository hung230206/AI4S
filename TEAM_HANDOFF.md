# Bàn giao sản phẩm Demo

## Bắt đầu từ đâu

Trên máy đang chạy, mở **http://localhost:3000/test-lab**. Bạn cùng Wi-Fi dùng địa chỉ LAN của máy chủ, hiện được cấu hình là **http://192.168.1.14:3000/test-lab**. Trang này có bộ tệp tải lên, hướng dẫn sáu bước, trạng thái sẵn sàng của OCR/provider, tiến độ từ dữ liệu tài khoản và nút xuất hồ sơ ZIP.

Tạo tài khoản riêng cho mỗi người thử. Nhánh **Thành công tự động · sandbox** và **Bị từ chối tự động · sandbox** không cần mã vận hành. Mã vận hành chỉ dành cho người kiểm thử nâng cao ở chế độ MANUAL; không gửi mã đó cho cả nhóm hoặc ghi vào video.

## Chạy trên máy khác

Có thể lấy source từ GitHub thay cho ZIP:

```sh
git clone https://github.com/hung230206/AI4S.git
cd AI4S
```

Nếu dùng ZIP, giải nén `Demo_Team_Handoff.zip`, vào thư mục `Demo` chứa tệp này. Cần Python 3.11, Node.js 22 trở lên kèm npm và PostgreSQL 16 trở lên hoặc Docker Desktop. Máy triển khai hiện tại chạy Windows, Python 3.11, Node 24 và PostgreSQL 18. Cần internet để cài dependencies, tải model OCR lần đầu và lấy dữ liệu FX mới.

Windows PowerShell:

```powershell
py -3.11 scripts/team.py setup --lan
py -3.11 scripts/team.py start --production --lan
```

Chế độ `--production` biên dịch trước bằng tùy chọn Webpack được Next.js hỗ trợ rồi phục vụ UI đã build; bước build có thể mất vài phút ở máy mới. Log build/API/web nằm trong `.local/run/`. Bỏ `--production` khi cần sửa code hoặc mở bảng vận hành UI nâng cao.

Giữ cửa sổ chạy mở; Ctrl+C dừng những tiến trình do launcher này tạo. Nếu cổng 3000/8000 đã được dùng, launcher sẽ dừng và báo để người dùng chủ động xử lý, không tự tắt chương trình khác. PostgreSQL chạy độc lập nên không bị dừng theo launcher.

Trong cửa sổ PowerShell thứ hai:

```powershell
py -3.11 scripts/team.py doctor
```

`setup` tạo `.env` với bí mật ngẫu nhiên khi chưa có, giữ nguyên tệp và bản ghi hiện hữu, cài dependencies khóa phiên bản, chạy migration/seed và tải ba model OCR. Không reset DB. Có thể dùng `--skip-install --database existing` khi đã cài đủ và đang dùng DB cấu hình sẵn. `--database native` yêu cầu PostgreSQL cài ở Windows; `--database docker` yêu cầu Docker; `--database existing` giữ việc khởi động DB cho người vận hành.

Unix:

```sh
python3 scripts/team.py setup
python3 scripts/team.py start --production
# terminal thứ hai
python3 scripts/team.py doctor
```

Để mở LAN trên Unix, cấu hình `FRONTEND_EXTRA_ORIGINS=http://IP_MAY_CHU:3000` trong `.env` và `LAN_ALLOWED_HOSTS=IP_MAY_CHU` trong `frontend/.env.local`, sau đó dùng `start --lan`. Unix và Docker phải được xác minh trên môi trường đích; xem kết quả thực tế trong IMPLEMENTATION_REPORT.md, không suy từ kiểm thử Windows rằng mọi hệ điều hành đã chạy thành công.

Khi IP Wi-Fi đổi trên Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/configure_lan.ps1
# Hoặc truyền chính xác: -Address 192.168.1.14
```

Khởi động lại API/frontend để nạp cấu hình. Thiết bị bạn bè phải cùng mạng, không bị guest/client isolation, và Windows cho phép Node trên mạng Private. Không cần cho cổng PostgreSQL hoặc backend truy cập trực tiếp từ LAN.

## Luồng nghiệm thu

Đọc **ACCEPTANCE_TESTS.md** hoặc làm theo trang Test A–Z:

1. Tải `01_en_800.png`, upload ở Hóa đơn, chọn tiếng Anh, kiểm tra 5 trường và xác nhận trước khi lưu.
2. Tạo sổ CNY 1.000, đưa hóa đơn 800 vào kế hoạch, kiểm tra dự phóng còn 200.
3. Xem giá trị VND; nguồn Frankfurter phải có ngày, không dùng mức cố định của dữ liệu SYNTHETIC cho hóa đơn cá nhân.
4. Upload PDF bảo hiểm mẫu hoặc bản gốc công khai, khai báo đúng loại nguồn, tìm đoạn có số trang.
5. Chọn phương thức SUCCESS, đồng ý đúng báo giá và xem kết quả tự động; chỉ webhook đã xác minh mới cấp biên nhận.
6. Xác nhận riêng việc ghi chi trong sổ, rồi tải hồ sơ kiểm thử ZIP. ZIP gồm nguồn gốc đã upload, bản ghi hóa đơn, báo giá, consent, sự kiện/nhật ký và sổ/kế hoạch liên quan. Hồ sơ có thể chứa tài liệu riêng; kiểm tra trước khi chia sẻ.

Chọn DECLINED với hóa đơn khác để kiểm tra thất bại, không có biên nhận, rồi tạo báo giá mới và thử lại. Thay phương thức phải tích đồng ý lại. Mặc định hóa đơn cá nhân chọn SUCCESS; workspace dữ liệu mẫu giữ MANUAL để các kịch bản kỹ thuật cũ vẫn tái lập được.

## Tài liệu gốc để upload

Trang Test A–Z dẫn tới PDF công khai do BFSU đăng và hướng dẫn của SJTU. Có thể tải PDF BFSU ngay từ website trường hoặc dùng:

```powershell
py -3.11 scripts/team.py fetch-reference
```

Unix dùng `python3`. Tệp nằm ở `.local/public-reference/bfsu-2025.pdf`; metadata đi kèm giữ URL, kích thước và SHA-256. Tải vào Tài liệu bảo hiểm, chọn **Tài liệu tham khảo công khai**, ngôn ngữ **Tiếng Trung và Anh**, điền URL gốc. Thử tìm `hospital` hoặc `理赔`, kiểm tra trang nguồn và tải bản gốc đối chiếu. Bản 2025 có thể không còn áp dụng cho một cá nhân/kỳ hiện tại. App không xác minh tư cách được bảo hiểm hoặc quyết định bồi thường. PDF dạng bảng dày có thể mất hàng chục giây; hãy chờ kết quả trước khi gửi thêm. Nếu gặp OCR_TIMEOUT khi máy bận, thử lại riêng tài liệu hoặc dùng bản PDF có lớp chữ. Chưa kiểm thử tải nhiều người đồng thời.

Public reference không được nhét vào source ZIP như tài sản của nhóm. Gói có công cụ tải từ nguồn và các mẫu tự soạn được phép chia sẻ. Các hóa đơn mẫu là dữ liệu tổng hợp, không phải thông báo thật của BFSU/SJTU. Người dùng có thể tải ảnh/chứng từ của mình vào app và đối chiếu thủ công.

## Chạy kiểm thử

Windows từ thư mục Demo:

```powershell
Push-Location backend
.venv/Scripts/python.exe -m pytest -q --junitxml=../submission/evidence/backend-junit.xml
.venv/Scripts/alembic.exe check
Pop-Location
Push-Location frontend
npm run lint
npm run build -- --webpack
npx playwright test
Pop-Location
backend/.venv/Scripts/python.exe scripts/check_acceptance_live.py --public-reference .local/public-reference/bfsu-2025.pdf
```

Unix thay executable backend bằng `.venv/bin/python` khi đang trong backend, hoặc `backend/.venv/bin/python` từ gốc. Playwright mặc định dùng Chrome; cài Chrome hoặc chạy `npx playwright install chromium` rồi cấu hình channel phù hợp. Cần API/frontend đang chạy cho browser/live tests. Full suite 15 ca có bảng vận hành nên chạy với `team.py start --lan` ở development. Khi dùng `--production`, kiểm tra hành trình người dùng bằng `npx playwright test tests/acceptance.spec.ts`; UI vận hành nâng cao được tắt có chủ đích. Bộ pytest chỉ được phép dùng database có tên kết thúc `_test`; không trỏ TEST_DATABASE_URL vào DB dữ liệu demo.

Để ghi lại hai luồng nghiệm thu bằng video Playwright trên Windows:

```powershell
Push-Location frontend
npx playwright install ffmpeg
$env:ACCEPTANCE_VIDEO='1'
npx playwright test tests/acceptance.spec.ts
Remove-Item Env:ACCEPTANCE_VIDEO
Pop-Location
```

Video chỉ được sao chép vào `submission/evidence/` khi test tương ứng đạt; trace lỗi ở `frontend/test-results` không được đóng gói. Các video là thao tác tự động trên trình duyệt với tài khoản QA, không phải nghiên cứu khả dụng hoặc giao dịch tiền thật.

## Đóng gói và cấu trúc mã

```powershell
py -3.11 scripts/team.py package
```

Kết quả `output/Demo_Team_Handoff.zip` có manifest SHA-256 theo từng tệp. Không kèm `.env`, tài khoản/DB, model tải cục bộ, venv, node_modules, cache, log/trace riêng hoặc PDF công khai đã tải. Đồng đội tự sinh bí mật và cài dependencies. Không ghi mã vận hành vào README.

Các điểm sửa chính: `backend/app/journey.py` cho tiến độ, dữ liệu mẫu và evidence ZIP; `providers.py`, `webhooks.py`, `main.py` cho giao dịch; `ocr.py` và `scripts/ocr_runner.cjs` cho OCR; `finance.py` cho sổ/dự phóng; `documents.py` cho kho chứng cứ. Giao diện Test A–Z ở `frontend/src/app/test-lab/page.tsx`. Migration đầu mới là `20261018_self_service`, tiếp theo `20261018_document_kind`; luôn nâng tới head.

Có thể chạy bản cách ly trên cổng khác bằng `team.py start --production --frontend-port 3101 --api-port 8101`, rồi `team.py doctor --url http://localhost:3101`. Launcher truyền đúng API proxy và Origin cho hai tiến trình, không sửa cổng của ứng dụng khác.

## Docker và giới hạn hiện tại

Tùy chọn chạy full stack:

```sh
python3 scripts/bootstrap.py
docker compose -f compose.yaml -f compose.app.yaml up --build
```

Backend image chứa Node, dependencies OCR và model; API không mở port trực tiếp ra LAN. Frontend dùng bản build production, chuyển tiếp API qua service `api`. Công cụ vận hành UI nâng cao bị tắt ở production frontend; các phương thức thử tự động vẫn qua API bật DEMO_MODE. Cấu hình Docker đã được cung cấp để team triển khai, nhưng chỉ ghi là đã chạy thành công nếu có bằng chứng chạy Docker trong báo cáo.

Hiện không có tài khoản ngân hàng/provider live, custody, đối soát trường học, xác minh email, quên mật khẩu, MFA, LLM sinh trả lời, embedding hay dự báo học máy. OCR dùng mô hình neural thật; FX dùng API thật theo ngày; trợ lý và dự phóng là quy tắc/phép tính. Hệ thống không chuyển tiền hoặc kích hoạt bảo hiểm. Đây là các hạng mục cần đánh giá khi chuyển từ MVP cuộc thi sang dịch vụ vận hành công khai.
