# Chức năng và cơ sở nghiên cứu của sản phẩm Demo

Tài liệu hiện trạng sản phẩm và phương pháp triển khai

> Bản nghiên cứu 1.0 này ghi hiện trạng trước đợt bàn giao A–Z cùng ngày. Chức năng mới và số kiểm thử hiện hành xem TEAM_HANDOFF.md, ACCEPTANCE_TESTS.md, IMPLEMENTATION_REPORT.md và docs/19_COMPETITION_HANDOFF_RESEARCH.md. Tệp Word đi kèm giữ nội dung của bản 1.0.

Ngày đối chiếu 18 tháng 10 năm 2026 · Phiên bản 1.0 · Ngôn ngữ tiếng Việt

## 1 Mục đích và kết luận chính

Demo hỗ trợ người dùng theo dõi khoản phí du học bằng CNY, quản lý sổ CNY và VND, lập kế hoạch thu chi, xem tác động của tỷ giá và tra cứu tài liệu bảo hiểm riêng. Chuỗi tác vụ chính là nhận thông báo thu phí → kiểm tra thông tin → lưu hóa đơn → đưa vào kế hoạch → xem khả năng thiếu tiền → ghi nhận khoản thực tế khi người dùng xác nhận.

Tài liệu này giải thích từng chức năng hiện có, vấn đề mà chức năng hướng tới, cơ sở từ tài liệu bên ngoài, phương pháp nghiên cứu và cách triển khai trong mã nguồn. Đối tượng đọc là thành viên nhóm, người kiểm thử và người đánh giá bản MVP. Tên hiển thị hiện tại của sản phẩm là Demo; một số tên thư mục, khóa kỹ thuật và bằng chứng cũ vẫn mang tên trước đây.

**Kết luận hiện trạng.** Phần tài khoản, lưu hóa đơn, OCR cục bộ, sổ thu chi, kế hoạch, dự phóng, tỷ giá tham chiếu và tìm đoạn tài liệu đã được triển khai và có bằng chứng kiểm thử kỹ thuật. Chuyển tiền và biên nhận thuộc sandbox nội bộ. App chưa giữ tiền, đồng bộ ngân hàng, kích hoạt bảo hiểm hoặc thực hiện giao dịch với nhà cung cấp bên ngoài.

**Cơ sở bài toán.** Tài liệu cuộc thi được lưu trên website Chiang Mai University nêu Topic C về nhu cầu tài chính của du học sinh và người dùng xuyên biên giới; Topic D đề cập hỗ trợ bảo hiểm. Đây là cơ sở định hướng phạm vi, không phải bằng chứng rằng nhu cầu đã được khảo sát trên du học sinh Việt Nam. Ảnh phân tích do người dùng cung cấp được dùng làm đầu vào thiết kế; không coi mọi thuật ngữ trong ảnh là yêu cầu chính thức của ban tổ chức. [01]

### Cách phân biệt các loại bằng chứng

| Loại | Ý nghĩa trong tài liệu |
| --- | --- |
| Nguồn bên ngoài | Căn cứ cho nguyên tắc, bài toán hoặc kỹ thuật; không tự chứng minh Demo hiệu quả |
| Mã nguồn hiện tại | Cho biết chức năng thực sự xử lý dữ liệu như thế nào |
| Kiểm thử đã lưu | Chứng minh một số trường hợp đã chạy đúng trong môi trường kiểm thử |
| Hiệu quả kỳ vọng | Lợi ích thiết kế hướng tới; cần nghiên cứu người dùng để xác nhận |

**Cách đọc.** Mục 2 trình bày phương pháp; mục 3 là danh mục 15 nhóm chức năng; mục 4–11 giải thích từng nhóm; mục 12–14 mô tả kiến trúc, đánh giá và nghiên cứu tiếp theo. Mục 15 có nguồn đánh số để kiểm tra lại từng nhận định.

<!-- PAGE -->

## 2 Phương pháp nghiên cứu và lập tài liệu

### 2.1 Câu hỏi nghiên cứu

Nghiên cứu tài liệu tập trung vào bốn câu hỏi: người dùng cần hoàn thành tác vụ gì; nguyên tắc hoặc sản phẩm nào có thể làm cơ sở thiết kế; Demo hiện thực hiện được phần nào; và bằng chứng nào đủ để kiểm tra độ đúng của phần đó. Phạm vi là nghiên cứu thiết kế và đánh giá kỹ thuật một nguyên mẫu, chưa phải nghiên cứu thị trường hay thử nghiệm tác động tài chính.

### 2.2 Quy trình thực hiện

**Bước 1 — Xác định vấn đề.** Đọc yêu cầu cuộc thi, tài liệu trong kit và phản hồi của chủ sản phẩm về việc khó hiểu giao diện. Phản hồi trong cuộc trò chuyện là dữ liệu định tính của một người, không đại diện cho toàn bộ du học sinh.

**Bước 2 — Nghiên cứu tài liệu thứ cấp.** Tra cứu trực tuyến tài liệu chính thức của CFPB, World Bank, Nielsen Norman Group, Wise, PocketSmith, các dự án OCR, OWASP, Stripe và các bài nghiên cứu liên quan. Ưu tiên nguồn gốc, tài liệu nhà phát triển và bài báo của tác giả. Lần đối chiếu nguồn cho tài liệu này thực hiện ngày 18/10/2026. Đây là tổng quan có mục tiêu, chưa phải tổng quan hệ thống có quy trình PRISMA hoặc đánh giá toàn bộ tài liệu liên quan.

**Bước 3 — So sánh chức năng.** Đối chiếu cách các sản phẩm trình bày số dư nguyên tệ, dự phóng và xác nhận giao dịch. Chỉ so sánh tài liệu công khai; không tuyên bố đã dùng thử tài khoản trả phí, đo hiệu năng đối thủ hay tích hợp API của họ.

**Bước 4 — Kiểm tra hiện thực.** Đọc các route giao diện, API, mô hình dữ liệu, cấu hình công khai và mã kiểm thử. Mỗi nhóm chức năng có đường dẫn mã tương đối để nhóm truy vết trong thư mục dự án. Các nguồn bên ngoài được trích cho lập luận thiết kế; tính năng hiện có được xác nhận bằng code và bằng chứng nội bộ.

**Bước 5 — Đối chiếu kết quả đánh giá.** Đọc báo cáo pytest, Playwright, kiểm tra HTTP và phép thử OCR đã lưu. Không chạy lại toàn bộ bộ kiểm thử khi chỉ biên soạn tài liệu; các con số ở mục 13 là kết quả của những lần chạy được lưu ngày 18/10/2026.

### 2.3 Khung phương pháp và giới hạn

Có thể tổ chức hoạt động theo hướng Design Science Research: xác định vấn đề, đặt mục tiêu, xây dựng tạo tác, minh họa, đánh giá và truyền đạt kết quả. Tài liệu dùng khung của Peffers và cộng sự để sắp xếp bằng chứng, không tuyên bố dự án đã hoàn thành một nghiên cứu học thuật DSRM đầy đủ. [16]

Chưa có phỏng vấn theo mẫu, khảo sát định lượng, thử nghiệm A/B, kiểm thử khả dụng độc lập hoặc đo thời gian nhập tay so với OCR. Vì vậy không kết luận rằng Demo đã giảm một tỷ lệ cụ thể về chi phí, thời gian, sai sót hoặc lo âu tài chính.

<!-- PAGE -->

## 3 Danh mục chức năng hiện tại

Các mã F01–F15 là nhóm chức năng để truy vết tài liệu, không phải 15 màn hình tách biệt. Một số nhóm dùng chung màn hình hoặc API.

| Mã | Chức năng | Vấn đề hướng tới | Trạng thái |
| --- | --- | --- | --- |
| F01 | Tổng quan và hướng dẫn | Không biết bắt đầu từ đâu | UI và quy tắc hoạt động |
| F02 | Tài khoản và phiên đăng nhập | Dữ liệu riêng bị lẫn giữa người thử | Lưu và phân quyền thật |
| F03 | Quản lý hóa đơn CNY | Thông tin khoản phí phân tán | Lưu dữ liệu thật |
| F04 | Đọc ảnh và PDF bằng OCR | Phải nhập lại thông báo thu phí | OCR chạy cục bộ |
| F05 | Sổ tiền CNY và VND | Dễ nhầm số dư giữa hai tiền tệ | Sổ khai báo thật |
| F06 | Thu chi thực tế và CSV | Không biết số dư thay đổi vì đâu | Ghi sổ thật |
| F07 | Kế hoạch và liên kết hóa đơn | Quên khoản sắp đến hạn, ghi trùng | Lập lịch thật |
| F08 | Dự phóng và thiếu hụt | Tổng tháng không cho thấy ngày thiếu tiền | Tính theo lịch đã nhập |
| F09 | Tỷ giá và lịch sử | Không biết nguồn và ngày quy đổi | API Frankfurter thật |
| F10 | Kịch bản tác động tỷ giá | Chưa hình dung khoản phí vượt ngân sách | Tính toán thật |
| F11 | Lưu và tìm tài liệu bảo hiểm | Khó tìm lại điều khoản và nguồn | Trích xuất và tìm đoạn thật |
| F12 | Trợ lý du học | Khó nối thông tin với bước tiếp theo | Quy tắc đọc dữ liệu |
| F13 | Báo giá và xác nhận giao dịch | Dễ nhầm xem giá với đã thanh toán | Giá tham chiếu hoặc mẫu; thanh toán giả lập |
| F14 | Lịch sử và biên nhận | Không theo dõi được trạng thái xử lý | Nhật ký sandbox thật |
| F15 | Vận hành và callback | Khó thử lỗi, sự kiện trùng và xử lý bất đồng bộ | Nhà cung cấp MOCK nội bộ |

**“Thật” trong bảng** nghĩa là dữ liệu được xử lý và lưu trong hệ thống đang chạy. Nó không có nghĩa là khoản tiền được ngân hàng xác minh, tài liệu được đơn vị phát hành xác thực hoặc giao dịch đã đi qua hệ thống tài chính bên ngoài.

### Mối quan hệ giữa các nhóm

Hóa đơn chưa làm giảm số dư sổ. Đưa hóa đơn vào kế hoạch chỉ tạo khoản dự kiến. Xác nhận đã chi mới tạo khoản thực tế trong sổ. Thanh toán sandbox là nhánh kiểm thử riêng và không tự ghi chi. Các đường tách này tránh đưa cùng một khoản vào phép tính nhiều lần và giữ quyền xác nhận ở người dùng.

<!-- PAGE -->

## 4 Trải nghiệm ban đầu và tài khoản

### F01 Tổng quan và hướng dẫn theo tác vụ

**Vấn đề và căn cứ.** Chủ sản phẩm phản hồi rằng giao diện khiến họ không biết sử dụng. Đây là bằng chứng trực tiếp cho trường hợp của chủ sản phẩm. Các nguyên tắc về nhận biết lựa chọn, hiển thị trạng thái, ngăn lỗi và trợ giúp theo tác vụ của Nielsen Norman Group là cơ sở thiết kế bổ sung. [04]

**Phương pháp.** Phân tích tác vụ, rà soát theo heuristic và kiểm tra bàn phím cùng kích thước màn hình. Chưa thực hiện nghiên cứu khả dụng với một mẫu người dùng độc lập.

**Triển khai.** Trang đầu đưa ra hai lựa chọn là xử lý khoản phí và đọc tài liệu. Popup giới thiệu xuất hiện theo tài khoản trên trình duyệt, có thể bỏ qua và mở lại bằng nút Hướng dẫn. Nội dung trợ giúp phụ thuộc đường dẫn hiện tại. Có chỉ báo bước xử lý, liên kết hành động và cảnh báo dựa trên dữ liệu. Dialog xử lý Tab, Shift+Tab, Escape và trả tiêu điểm về nút mở; giao diện mobile dùng bố cục thích ứng.

**Kiểm tra và giới hạn.** Mở tài khoản mới, đóng/mở hướng dẫn và điều hướng hoàn toàn bằng bàn phím. Đây là UI theo ngữ cảnh và quy tắc, chưa phải giao diện do mô hình AI tự sinh. Hiệu quả giúp người mới hiểu nhanh hơn vẫn cần đo.

**Mã đối chiếu.** frontend/src/components/user-guide.tsx; task-dashboard.tsx; shell.tsx; frontend/tests/onboarding.spec.ts.

### F02 Tài khoản cá nhân và quản lý phiên

**Vấn đề và căn cứ.** Người thử cần không gian riêng cho hóa đơn, sổ và tài liệu. OWASP khuyến nghị kiểm tra quyền trên từng yêu cầu và quản lý phiên ở máy chủ; đây là cơ sở bảo vệ truy cập, không phải chứng nhận bảo mật cho Demo. [05][06]

**Phương pháp.** Phân tích ranh giới tin cậy và kiểm thử các trường hợp đăng nhập sai, truy cập dữ liệu người khác, thiếu CSRF và phiên đã thu hồi.

**Triển khai.** Đăng ký bằng email, tên và mật khẩu; mật khẩu băm Argon2id. Phiên opaque nằm trong cookie HttpOnly; cơ sở dữ liệu lưu hash token và thời hạn. Có kiểm tra Origin/CSRF cho thao tác ghi, giới hạn thử đăng nhập, sửa tên, đổi mật khẩu và đăng xuất. Đổi mật khẩu thu hồi các phiên cũ. Tài khoản cá nhân bắt đầu với dữ liệu trống; tài khoản mẫu dùng dữ liệu chung.

**Kiểm tra và giới hạn.** Tạo hai tài khoản, lưu dữ liệu ở tài khoản A rồi kiểm tra B không xem được qua API. Chưa có xác minh email, khôi phục mật khẩu hoặc MFA. Bản LAN dùng HTTP phục vụ thử nghiệm; không coi đây là cấu hình triển khai công khai hoàn chỉnh.

**Mã đối chiếu.** backend/app/accounts.py; security.py; frontend/src/components/auth-screen.tsx; frontend/src/app/account/page.tsx.

<!-- PAGE -->

## 5 Hóa đơn và nhận dạng chứng từ

### F03 Quản lý khoản phí bằng CNY

**Vấn đề và căn cứ.** Số tiền, bên nhận và hạn thanh toán cần được gom vào một bản ghi để có thể theo dõi và lập kế hoạch. Topic C tạo bối cảnh học phí và tài chính xuyên biên giới; việc dùng một bản ghi hóa đơn là lựa chọn thiết kế của Demo, chưa phải giải pháp được khảo sát xác nhận trên một quần thể sinh viên. [01]

**Phương pháp.** Phân rã dữ liệu của tác vụ và kiểm thử nghiệp vụ: tiền tệ, độ chính xác, ngày đến hạn, sở hữu và trạng thái có được sửa hay không.

**Triển khai.** Cho phép tạo, tìm, xem, cập nhật và hủy hiệu lực hóa đơn theo điều kiện trạng thái. Trường dữ liệu gồm mã hóa đơn, đơn vị, bên nhận, loại khoản phí, số CNY và hạn. Backend kiểm tra số tiền dương, tối đa hai chữ số thập phân và quyền chủ sở hữu; chặn sửa ở trạng thái giao dịch không phù hợp. Hóa đơn do người dùng nhập được phân biệt với dữ liệu mẫu.

**Kiểm tra và giới hạn.** Lưu hóa đơn rồi tải lại trang; thử số tiền sai định dạng và truy cập khác chủ sở hữu. Bản ghi không chứng minh trường học hay công ty bảo hiểm đã phát hành hóa đơn. Chưa có kết nối hệ thống học phí hoặc xác minh tài khoản bên nhận. Hóa đơn hiện dùng CNY, không tự chuyển hóa đơn USD thành CNY.

**Mã đối chiếu.** backend/app/billing.py; schemas.py; frontend/src/app/invoices/.

### F04 OCR ảnh và PDF có bước đối chiếu

**Vấn đề và căn cứ.** Hướng tới giảm việc gõ lại các trường của thông báo thu phí. Tesseract.js hỗ trợ nhận dạng chữ qua worker; tessdata_fast cung cấp mô hình LSTM đã huấn luyện. Tính năng này dùng mô hình có sẵn, nhóm chưa huấn luyện mô hình mới. [07][08]

**Phương pháp.** Xây pipeline rồi kiểm tra khớp chính xác từng trường trên ba ảnh in sạch tự soạn bằng Anh, Việt và Trung giản thể. Đây là smoke test kỹ thuật; chưa đo lợi ích so với nhập tay hoặc độ chính xác trên ảnh thực tế đa dạng.

**Triển khai.** Backend nhận ảnh/PDF/TXT/MD. PDF có chữ được trích xuất; trang quét được render bằng pypdfium2 rồi chạy Tesseract.js 6.0.1 trong Node worker. Chọn eng, vie hoặc chi_sim; model lưu cục bộ. Parser theo nhãn và quy tắc tìm mã, đơn vị, bên nhận, tiền và ngày; gắn dòng/trang nguồn. Tệp tối đa 5 MB, OCR tối đa 5 trang, ảnh 16 megapixel, tối đa hai worker và timeout 75 giây. Phải đối chiếu và xác nhận trước khi lưu; giữ bản gốc riêng cho chủ sở hữu. [09]

**Kiểm tra và giới hạn.** Tải ảnh rõ chữ, sửa trường sai và thử lưu khi chưa xác nhận. OCR có thể sai trên ảnh mờ, chữ viết tay hoặc bố cục lạ. Nội dung không gửi API OCR ngoài; khi bạn bè truy cập LAN, OCR chạy trên máy chủ đang chạy app.

**Mã đối chiếu.** backend/app/ocr.py; scripts/ocr_runner.cjs; scripts/setup_ocr.py; scripts/benchmark_local_ocr.py.

<!-- PAGE -->

## 6 Sổ nguyên tệ và khoản đã phát sinh

### F05 Sổ tiền CNY và VND

**Vấn đề và căn cứ.** Cộng trực tiếp số CNY với VND tạo ra tổng không có ý nghĩa. Wise mô tả các balance riêng theo tiền tệ; PocketSmith phân biệt số dư nguyên tệ với giá trị quy đổi. Demo tham khảo cách tổ chức này cho sổ cá nhân, không sử dụng hạ tầng giữ tiền của họ. [10][11]

**Phương pháp.** So sánh mô hình dữ liệu từ tài liệu sản phẩm, sau đó kiểm thử các bất biến tiền tệ và chủ sở hữu. Không đo hoặc so sánh độ hài lòng với các sản phẩm tham khảo.

**Triển khai.** Người dùng khai báo tên sổ, tiền tệ, số dư đầu và ngày bắt đầu. FinanceWallet thuộc một người dùng; khoản ghi sổ phải dùng đúng tiền tệ của sổ. Backend dùng Decimal, CNY hai chữ số và VND số nguyên. Dự phóng và số dư vẫn giữ nguyên tệ; phần quy VND chỉ được tính khi có tỷ giá đủ điều kiện và được gắn nguồn.

**Kiểm tra và giới hạn.** Tạo một sổ 1.000 CNY và một sổ 4.000.000 VND, kiểm tra không hiển thị tổng thành “4.001.000” cùng đơn vị. Đây là số dư tự khai báo, không phải ví lưu ký, tài khoản ngân hàng hoặc kế toán kép hoàn chỉnh. App không xác minh số tiền ngoài đời.

**Mã đối chiếu.** backend/app/finance.py, các hàm money, balance và wallet_out; backend/app/models.py; frontend/src/components/finance-hub.tsx.

### F06 Ghi nhận thu chi thực tế và xuất CSV

**Vấn đề và căn cứ.** Cần biết số dư thay đổi do khoản nào và sửa ghi nhận sai mà vẫn truy lại được. Công cụ ngân sách của CFPB dựa trên số dư đầu, các khoản thu và các khoản chi; Demo áp dụng quan hệ này cho nhật ký theo ngày. [03]

**Phương pháp.** Kiểm thử phép tính và các tình huống gửi lại yêu cầu, hủy ghi nhận, sai tiền tệ và truy cập khác chủ. Đây là đánh giá độ đúng của sổ, không chứng minh dữ liệu nhập phản ánh đầy đủ đời thực.

**Triển khai.** FinanceEntry ghi INCOME hoặc EXPENSE, số tiền, nhóm, ngày và sổ. Số dư bằng số dư đầu cộng thu trừ chi có trạng thái POSTED. Hủy chuyển thành VOID, không xóa dấu vết. Mỗi lần ghi có khóa chống lặp và hash nội dung; backend khóa theo người dùng. CSV xuất từ dữ liệu đang theo dõi và xử lý ô có nguy cơ bị phần mềm bảng tính coi là công thức.

**Kiểm tra và giới hạn.** Sổ 1.000 CNY, ghi chi 200 còn 800; hủy thì trở lại 1.000. Gửi lại cùng yêu cầu không được ghi thành hai khoản. CSV phục vụ đối chiếu cá nhân, chưa phải sao kê ngân hàng hoặc chứng từ kế toán được chứng nhận.

**Mã đối chiếu.** backend/app/finance.py, create_entry, replay_entry và void_entry; frontend/src/components/finance-hub.tsx.

<!-- PAGE -->

## 7 Kế hoạch và dự phóng dòng tiền

### F07 Kế hoạch thu chi và đưa hóa đơn vào ngân sách

**Vấn đề và căn cứ.** Khoản phải trả trong tương lai cần tách khỏi khoản đã phát sinh. Cách lập ngân sách dòng tiền của CFPB chú ý thời điểm thu/chi; hệ thống dùng lịch để biến ngày đến hạn thành sự kiện có thể theo dõi. [03]

**Phương pháp.** Mô hình hóa sự kiện theo ngày và kiểm thử ranh giới lịch: tháng ngắn, ngày cuối tháng, khoản quá hạn, xác nhận lặp và hủy khoản đã ghi.

**Triển khai.** FinancePlan có thu/chi, lịch một lần hoặc hằng tháng và sổ tiền. Đưa hóa đơn vào kế hoạch yêu cầu sổ CNY; máy chủ lấy số tiền và hạn từ hóa đơn. Bản kế hoạch là ảnh chụp tại lúc thêm, không tự đồng bộ khi sửa hóa đơn. Một hóa đơn không tạo nhiều kế hoạch trùng. Khi người dùng chọn đã thu/chi và xác nhận, backend tạo khoản thực tế cho đúng kỳ; chỉ mục duy nhất ngăn ghi hai lần. Kỳ đã ghi được loại khỏi phần dự kiến. Hủy ghi nhận làm kỳ đó trở lại dự kiến; dừng kế hoạch không xóa khoản thực tế.

**Kiểm tra và giới hạn.** Thêm hóa đơn vào kế hoạch hai lần; xác nhận một kỳ rồi kiểm tra số dư và dự phóng không tính trùng. Chưa có email/SMS nhắc hạn; cảnh báo xuất hiện trong app. Lưu hóa đơn và thanh toán sandbox không tự ghi chi.

**Mã đối chiếu.** backend/app/finance.py, invoice_plan, occurrence_dates, settle_plan và stop_plan; migration 9f40f776cbf8.

### F08 Dự phóng 30 60 90 ngày và cảnh báo thiếu hụt

**Vấn đề và căn cứ.** Có đủ tiền tính theo tổng tháng vẫn có thể thiếu ở ngày phải trả trước khi nhận trợ cấp. CFPB cung cấp cơ sở trực tiếp cho việc theo dõi thời điểm dòng tiền; Demo chuyển nguyên tắc đó sang tính theo ngày. [03]

**Phương pháp.** Mô phỏng xác định dựa trên lịch, không huấn luyện mô hình. So sánh kết quả với các tình huống tính tay, thử chu kỳ tháng và kiểm tra việc loại khoản đã ghi nhận.

**Triển khai.** Với mỗi sổ, lấy số dư hiện tại rồi cộng các khoản thu dự kiến và trừ khoản chi dự kiến theo ngày. Tạo đường số dư, số dư cuối kỳ, mức thấp nhất và ngày đầu bị âm. Khoản quá hạn chưa ghi được đưa vào ngày đầu kèm nhãn. Tháng thiếu ngày gốc được chặn về ngày cuối tháng. Cảnh báo và liên kết hành động được tạo từ kết quả tính toán.

**Ví dụ kiểm tra.** Có 800 CNY và kế hoạch chi 900 CNY ngày mai thì số dư dự phóng là âm 100 CNY. Số dư thực tế vẫn 800 cho đến khi ghi nhận đã chi. Trợ cấp đến sau ngày trả không xóa việc từng thiếu tiền ở ngày trước.

**Giới hạn và mã.** Không suy ra chi phí chưa nhập, không dự đoán thị trường và không tự điều chuyển giữa sổ. Xem backend/app/finance.py, forecast; frontend/src/components/finance-hub.tsx và finance-advice.tsx.

<!-- PAGE -->

## 8 Tỷ giá tham chiếu và tác động ngân sách

### F09 Tỷ giá CNY VND và lịch sử

**Vấn đề và căn cứ.** Giá quy đổi thiếu nguồn hoặc ngày quan sát dễ bị hiểu như mức giá đang thực hiện được. World Bank chỉ ra phí chuyển tiền và chênh lệch tỷ giá là các thành phần khác nhau của chi phí; Frankfurter công bố API tỷ giá tham chiếu cập nhật theo ngày. [02][12]

**Phương pháp.** Đọc hợp đồng API, kiểm tra phản hồi thực và thử các tình huống mất kết nối, dữ liệu không hợp lệ, cache và quá tuổi cho phép. Dữ liệu FX thật là đầu vào của phép tính; bộ kiểm thử cũng dùng dữ liệu kiểm soát để tái lập lỗi.

**Triển khai.** Backend gọi /v2/rate/CNY/VND và /v2/rates cho chuỗi lịch sử gần đây. Chỉ gửi mã tiền tệ và ngày, không gửi hóa đơn hoặc thông tin người dùng. Kiểm tra cặp tiền, ngày, tỷ giá hữu hạn dương và kích thước phản hồi. Lưu FxObservation với nguồn, ngày quan sát và thời gian tải; mặc định cache 6 giờ, tuổi dữ liệu tối đa 7 ngày. Khi tải lại lỗi nhưng còn cache hợp lệ thì đánh dấu stale; khi không còn dữ liệu hợp lệ thì báo không có tỷ giá, không bịa số thay thế.

**Kiểm tra và giới hạn.** Mở màn tỷ giá, kiểm tra nguồn/ngày và đồ thị; thử lỗi upstream trong test backend. Đây không phải luồng giá từng giây, báo giá ngân hàng hoặc API đổi tiền. Tần suất và khả năng sẵn có phụ thuộc nguồn công khai.

**Mã đối chiếu.** backend/app/fx.py; config.py; frontend/src/app/rates/page.tsx.

### F10 Phân tích khoản phí theo ngân sách VND

**Vấn đề và căn cứ.** Người dùng cần thấy khoản CNY tương ứng bao nhiêu VND và tác động nếu tỷ giá thay đổi. Tách tham chiếu khỏi chi phí giao dịch thực phù hợp với cách World Bank phân biệt các thành phần chi phí. Mức ±5% là tham số minh họa do nhóm chọn, không phải kết luận nghiên cứu về biên độ thị trường. [02]

**Phương pháp.** Phân tích độ nhạy xác định; kiểm thử Decimal, làm tròn VND và các trường hợp ngân sách đủ/thiếu. Không dùng mô hình xác suất hoặc học máy.

**Triển khai.** Nhập số CNY hoặc chọn hóa đơn, thêm ngân sách VND tùy chọn. Với số tiền A, tỷ giá R và mức thay đổi s, chi phí là làm tròn A × R × (1 + s); s lần lượt bằng −0,05; 0; 0,05. Phần còn lại bằng ngân sách trừ chi phí. Ngưỡng tỷ giá để vừa ngân sách bằng ngân sách chia A. Backend tính, frontend trình bày.

**Kiểm tra và giới hạn.** Ví dụ minh họa R = 3.800 và A = 800 cho 3.040.000 VND; đây là số giả định để kiểm tra công thức, không phải tỷ giá hiện tại. Kết quả chưa gồm phí nhà cung cấp, không đưa xác suất xảy ra hay khuyến nghị thời điểm đổi tiền.

**Mã đối chiếu.** backend/app/finance.py, fx_analysis; frontend/src/app/rates/page.tsx.

<!-- PAGE -->

## 9 Tài liệu bảo hiểm và trợ lý du học

### F11 Kho tài liệu riêng và tra cứu đoạn gốc

**Vấn đề và căn cứ.** Cần tìm đoạn liên quan và kiểm tra ngữ cảnh trong tài liệu dài. Bài RAG của Lewis và cộng sự là cơ sở để phân biệt truy xuất với sinh câu trả lời. Demo hiện có truy xuất trích đoạn, chưa có thành phần sinh hoặc embedding nên không gọi đây là RAG đầy đủ. [13]

**Phương pháp.** Thiết kế pipeline trích xuất → chia đoạn → tìm kiếm → dẫn nguồn. Kiểm thử có từ khóa, không có chứng cứ, nhiều tài liệu, PDF quét và phân quyền. Chưa đo recall trên một tập chính sách đại diện.

**Triển khai.** Nhận PDF, ảnh, TXT và MD, tối đa 5 MB. PDF có chữ tối đa 50 trang; OCR ảnh/PDF quét tối đa 5 trang. Lưu tệp gốc cùng văn bản từng trang và chủ sở hữu; hỗ trợ xem, tải và xóa. Tìm kiếm chuẩn hóa văn bản, dùng từ khóa, nhóm đồng nghĩa Việt–Anh–Trung và cụm ký tự CJK. Xếp theo số thuật ngữ khớp, trả tối đa 5 đoạn cùng tên tệp, trang và nội dung gốc. Không có kết quả thì thông báo thiếu thông tin.

**Kiểm tra và giới hạn.** Tải tài liệu có điều khoản đã biết, tìm từ khóa rồi mở đúng trang để đối chiếu; hỏi nội dung không có trong tài liệu. Khớp từ không bảo đảm hiểu đúng pháp lý, ngữ nghĩa hay ngoại lệ. App chưa xác nhận quyền lợi, tính phí bảo hiểm hoặc nộp hồ sơ bồi thường.

**Mã đối chiếu.** backend/app/documents.py; ocr.py; frontend/src/app/assistant/page.tsx.

### F12 Trợ lý du học đọc dữ liệu và hướng dẫn bước tiếp theo

**Vấn đề và căn cứ.** Người dùng cần nối câu hỏi về hóa đơn, ngân sách, tỷ giá và tài liệu với một hành động cụ thể. Tài liệu về agent của Anthropic nhấn mạnh việc chọn mức phức tạp phù hợp; đây là tham khảo kiến trúc, không chứng minh Demo là agent LLM. Nguyên tắc trợ giúp theo ngữ cảnh hỗ trợ cách trình bày liên kết hành động. [14][04]

**Phương pháp.** Định tuyến ý định theo từ khóa; kiểm thử câu hỏi thuộc các nhóm và đặc biệt yêu cầu chuyển tiền để bảo đảm trợ lý không thực hiện thao tác tài chính.

**Triển khai.** Endpoint assistant chọn nhánh tỷ giá, hóa đơn, dự phóng hoặc chứng cứ bảo hiểm. Phản hồi dựa trên dữ liệu của tài khoản, có nguồn/trang hoặc liên kết tới màn thao tác. Câu hỏi về thanh toán dẫn người dùng về kiểm tra hóa đơn. Trường executed_actions luôn là danh sách rỗng. Việc ghi sổ, đổi thông tin hoặc xác nhận thanh toán cần thao tác riêng của người dùng.

**Kiểm tra và giới hạn.** Hỏi ngân sách 30 ngày sau khi có sổ và kế hoạch; hỏi điều khoản sau khi tải tài liệu; yêu cầu “chuyển tiền giúp tôi” phải chỉ nhận hướng dẫn. Không gọi OpenAI/Gemini/Claude, chưa hội thoại suy luận tự do và không học từ lịch sử chat. OCR mới là thành phần dùng mô hình neural có sẵn.

**Mã đối chiếu.** backend/app/finance.py, assistant; frontend/src/app/copilot/page.tsx.

<!-- PAGE -->

## 10 Báo giá và xác nhận thanh toán sandbox

### F13 Xem giá trị VND và chủ động xác nhận

**Vấn đề và căn cứ.** Người dùng có thể nhầm việc xem chi phí với đã phát sinh giao dịch, hoặc vô tình gửi lặp khi mạng chậm. Cơ sở thiết kế gồm minh bạch các thành phần chi phí của World Bank, ngăn lỗi và quyền kiểm soát người dùng của Nielsen Norman Group, cùng mẫu idempotency được mô tả trong tài liệu Stripe. Stripe chỉ là nguồn tham khảo kỹ thuật, chưa được tích hợp. [02][04][15]

**Phương pháp.** Mô hình hóa trạng thái giao dịch và các bất biến: đúng hóa đơn, đúng chủ sở hữu, số tiền do máy chủ tính, đúng báo giá còn hạn và có xác nhận. Kiểm thử gửi lại, gửi đồng thời, báo giá hết hạn, số tiền bị sửa và hủy trước xử lý.

**Triển khai báo giá.** Với hóa đơn người dùng nhập, máy chủ lấy Frankfurter và tính giá trị tham chiếu; phí cấu hình dịch vụ mặc định bằng 0 không đồng nghĩa ngân hàng chuyển miễn phí. Với hóa đơn mẫu SYNTHETIC, tỷ giá và phí cố định phục vụ tình huống demo tái lập. Báo giá ghi nguồn, chi tiết quy đổi/phí/tổng và thời điểm hết hạn; mặc định thời hạn 600 giây. Không coi nó là cam kết của nhà cung cấp.

**Triển khai xác nhận.** Giao diện yêu cầu tích đồng ý, hiển thị rõ sandbox và dùng khóa idempotency cho tạo/xác nhận. Backend kiểm tra lại báo giá, tổng tiền mong đợi, consent, quyền chủ và trạng thái. Không lấy số tiền hiển thị ở trình duyệt làm nguồn tin cuối cùng. Nhấn xem giá cho hóa đơn cá nhân chưa tạo giao dịch; với dữ liệu mẫu có thể tạo bản ghi chờ xác nhận để phục vụ demo. Cả hai vẫn cần xác nhận riêng để chuyển sang xử lý.

**Trạng thái chính.** AWAITING_CONFIRMATION là chờ xác nhận; PROCESSING là đã gửi ý định thử; SUCCEEDED và FAILED là kết quả mô phỏng; CANCELLED là hủy trước xử lý; EXPIRED là hết hạn chờ xác nhận. Sự kiện hợp lệ từ provider MOCK mới quyết định kết quả xử lý. Trợ lý không tự xác nhận hoặc tự đặt thành công.

**Cách kiểm tra.** Tạo hóa đơn còn hạn → lấy giá → thử xác nhận khi chưa đồng ý → tích đồng ý và xác nhận → xem trạng thái đang xử lý. Thử tải lại hoặc gửi lặp mà không tạo nhiều giao dịch hoạt động cho cùng hóa đơn. Dùng chức năng vận hành F15 để phát thành công/thất bại.

**Giới hạn.** Không có ngân hàng hoặc cổng thanh toán thật; chưa có nhà cung cấp sandbox bên ngoài. Không chuyển tiền, mua bảo hiểm, đối soát tổ chức tài chính hay kiểm tra người nhận trong thế giới thực. Giá tham chiếu thật không biến nhánh thanh toán thành giao dịch thật.

**Mã đối chiếu.** frontend/src/app/checkout/[invoiceId]/page.tsx; backend/app/main.py, các route quotes/orders/confirm; services.py, breakdown và replay; models.py.

<!-- PAGE -->

## 11 Lịch sử và công cụ vận hành

### F14 Lịch sử trạng thái và biên nhận mô phỏng

**Vấn đề và căn cứ.** Sau xác nhận, người dùng cần biết giao dịch đang chờ, thất bại hay thành công, thay vì bấm gửi lại vì không rõ trạng thái. Nguyên tắc hiển thị trạng thái và hỗ trợ phục hồi lỗi là cơ sở UI; tài liệu webhook Stripe cho thấy cần xử lý sự kiện trùng và bất đồng bộ. [04][17]

**Phương pháp.** Kiểm thử toàn bộ luồng trên trình duyệt, gồm thành công, thất bại, hủy, gửi lặp và xuất dữ liệu. Đối chiếu trạng thái trên màn hình với bản ghi và sự kiện ở backend.

**Triển khai.** Lịch sử liệt kê các giao dịch theo người dùng; trang chi tiết có trạng thái, dòng sự kiện và dấu nhận trùng không xử lý lại. Có xuất CSV lịch sử và nhật ký JSON cho luồng mô phỏng. Chỉ giao dịch thành công được cấp biên nhận; biên nhận có nhãn rõ “SIMULATED TRANSACTION — NO REAL FUNDS MOVED”, xem được và dùng chế độ in của trình duyệt.

**Kiểm tra và giới hạn.** Thử một giao dịch thất bại và một giao dịch thành công; chỉ trường hợp thành công có biên nhận. Phát lại sự kiện không được tạo thêm biên nhận hoặc đổi kết quả đã kết thúc. Đây là nhật ký thật của một phép mô phỏng, không phải bằng chứng thanh toán ngân hàng, hóa đơn thuế hoặc giấy chứng nhận bảo hiểm.

**Mã đối chiếu.** frontend/src/app/history/page.tsx; payments/[id]/page.tsx; receipts/[id]/page.tsx; backend/app/main.py; webhooks.py.

### F15 Vận hành thử và xác minh sự kiện provider

**Vấn đề và căn cứ.** Nhóm cần chủ động tạo tình huống thành công/thất bại và kiểm tra sự kiện giả mạo, đến muộn hoặc bị gửi lại. Tài liệu Stripe mô tả việc xác minh webhook và chống sự kiện trùng. Demo triển khai giao thức HMAC riêng cho MOCK, không sử dụng SDK hoặc chữ ký Stripe. [17]

**Phương pháp.** Kiểm thử đối kháng ở API: chữ ký sai, timestamp cũ, số tiền/tiền tệ sai, event ID dùng lại, event đến sau trạng thái kết thúc và cạnh tranh đồng thời.

**Triển khai.** Phiên vận hành chỉ có trong DEMO_MODE, xác thực mã ở máy chủ và kiểm tra role. MockPaymentProvider lưu sự kiện vào hàng đợi trong DB; worker chuyển qua route webhook nội bộ bằng ASGI. Chữ ký HMAC SHA-256 phủ timestamp và raw body; dung sai timestamp 5 phút. Backend khóa/deduplicate theo event ID, đối chiếu payment ID, số tiền và tiền tệ, rồi kiểm tra trạng thái trước khi cập nhật. Nhật ký không xuất bí mật xác thực.

**Kiểm tra và giới hạn.** Mở màn Vận hành thử trên máy chủ, dùng mã cục bộ để phát sự kiện; mã sai phải bị từ chối. Không chia sẻ mã qua tài liệu thử nghiệm. Endpoint và log chạy thật nhưng không gọi API thanh toán ra ngoài; khả năng xử lý hệ thống phân tán quy mô lớn chưa được đánh giá.

**Mã đối chiếu.** backend/app/providers.py; webhooks.py; security.py; frontend/src/app/operator/page.tsx.

<!-- PAGE -->

## 12 Kiến trúc và cách triển khai chung

### 12.1 Các thành phần

Giao diện dùng Next.js, React và TypeScript. Trình duyệt gọi /api/v1 trên cùng origin; Next.js chuyển tiếp tới FastAPI. Backend dùng Pydantic để kiểm tra đầu vào, SQLAlchemy để truy cập PostgreSQL và Alembic quản lý thay đổi schema. Hợp đồng API được lưu tại contracts/openapi-mvp.json; phiên bản đối chiếu có 45 path và 18 bảng ORM. Đây là số lượng đường dẫn, không phải số chức năng hay số phép thử.

OCR là tiến trình Node riêng được Python gọi với tệp cục bộ; PDF/ảnh được chuẩn hóa trước khi nhận dạng. Worker thanh toán nội bộ hoạt động khác worker OCR: nó phát lại sự kiện MOCK qua API nội bộ. Các phần tính số tiền và điều kiện nghiệp vụ nằm ở backend.

### 12.2 Dữ liệu đi ra ngoài ở đâu

| Thành phần | Dịch vụ bên ngoài | Dữ liệu gửi | Cách dùng |
| --- | --- | --- | --- |
| Tỷ giá | Frankfurter | Cặp tiền và khoảng ngày | API trong lúc chạy, có cache |
| Mô hình OCR | Kho tessdata_fast | Yêu cầu tải tệp model công khai | Khi cài đặt, không gửi chứng từ |
| OCR chứng từ | Không | Không gửi OCR ra dịch vụ ngoài | Chạy ở máy chủ ứng dụng |
| Trợ lý | Không gọi LLM | Không gửi chat tới LLM | Quy tắc và dữ liệu nội bộ |
| Thanh toán | Không có provider ngoài | Không gửi lệnh ngân hàng | MOCK trong ứng dụng |

Mã model OCR được cố định tại commit 87416418657359cb625c412a48b6e1d6d41c29bd và ghi hash trong manifest. Bản thân máy chủ vẫn lưu dữ liệu của người dùng; “không gửi API ngoài” không có nghĩa tệp chỉ nằm trên điện thoại hoặc trình duyệt của họ.

### 12.3 Nguyên tắc xuyên suốt

**Quyền và phiên.** API kiểm tra người dùng và sở hữu tài nguyên, không dựa vào việc ẩn nút trên UI. Cookie và CSRF hỗ trợ bảo vệ thao tác ghi; quyền vận hành không lấy từ tham số phía client. [05][06]

**Tiền và chống lặp.** Dùng Decimal ở server; số vẽ biểu đồ có thể chuyển sang Number nhưng không dùng làm số tiền quyết toán. Transaction, khóa và unique constraint bảo vệ các lần ghi quan trọng. Mẫu idempotency tham khảo tài liệu API thanh toán, còn triển khai hiện tại nằm trong code Demo. [15]

**Giới hạn tự động hóa.** OCR đề xuất dữ liệu, trợ lý đọc và tính; người dùng xác nhận việc lưu, ghi sổ và thử thanh toán. Nhãn nguồn phân biệt dữ liệu người nhập, chứng từ, FX công khai và ví dụ tổng hợp. Đây là cơ chế kiểm soát trong ứng dụng, chưa phải đánh giá tuân thủ quy định tài chính.

<!-- PAGE -->

## 13 Kết quả đánh giá kỹ thuật hiện có

Các kết quả dưới đây được đọc từ bằng chứng đã lưu ngày 18/10/2026. Việc biên soạn tài liệu không tạo ra một lần chạy lại toàn bộ hệ thống. Lỗi ngoài phạm vi các ca thử vẫn có thể tồn tại.

| Hạng mục | Kết quả được lưu | Diễn giải đúng |
| --- | --- | --- |
| Backend pytest | 101 passed trong 66,13 giây | Các ca backend trong suite đạt |
| Trình duyệt Playwright | 13 passed, 0 unexpected, 0 skipped; khoảng 100,94 giây | Các luồng tự động qua giao diện đạt |
| Kiểm tra HTTP thực | 8 mục kiểm tra đạt qua proxy frontend | Luồng OCR, sổ, FX, tài liệu và phiên đã được gọi |
| OCR mẫu tiếng Anh | 5/5 trường; 0,67 giây | Một ảnh in sạch tự soạn |
| OCR mẫu tiếng Việt | 5/5 trường; 0,75 giây | Một ảnh in sạch tự soạn |
| OCR mẫu Trung giản thể | 5/5 trường; 1,05 giây | Một ảnh in sạch tự soạn |
| Frontend và migration | Lint, build và Alembic check đạt trong báo cáo | Kiểm tra mã, biên dịch và schema |

### 13.1 Các tình huống có bằng chứng

Kiểm tra HTTP đã lưu bao gồm OCR ảnh Trung, chặn lưu khi chưa đối chiếu và tải lại đúng byte tệp gốc; dự phóng thiếu hụt theo nguyên tệ; gửi lặp ghi sổ không tính hai lần; hủy ghi nhận khôi phục số dư và kỳ kế hoạch; lấy tỷ giá/lịch sử thật; OCR tài liệu bảo hiểm và dẫn trang; trợ lý không thực hiện thanh toán; và phiên đăng xuất bị từ chối ở lần gọi sau.

Kiểm thử trình duyệt bao gồm hướng dẫn, tài khoản, hóa đơn, tài liệu, ngân sách và luồng thanh toán mô phỏng. Bộ backend kiểm tra cả đầu vào sai, quyền sở hữu, trạng thái và callback. Một cảnh báo Starlette/httpx đã được ghi trong báo cáo; đó không phải ca test thất bại.

### 13.2 Cách đọc phép thử OCR

“5/5” là năm trường của một mẫu khớp giá trị kỳ vọng, không phải độ chính xác 100% trên hóa đơn thực tế. Ba ảnh do script tạo có chữ in rõ và nhãn phù hợp với parser; chưa bao phủ ảnh điện thoại, bóng đổ, xoay nghiêng, nhiều cột hoặc viết tay. Thời gian phụ thuộc máy và cấu hình ngôn ngữ; chưa có phân bố p50/p95. Chưa đo CER, WER hoặc chi phí sửa thủ công.

### 13.3 Tệp bằng chứng để tái kiểm tra

submission/evidence/backend-junit.xml; browser-results.json; student-finance-live-http.json; local-ocr-smoke.json; student-finance-verification.txt. Các tên tệp sau dấu chấm phẩy đều nằm trong cùng thư mục submission/evidence/. IMPLEMENTATION_REPORT.md ghi bối cảnh và lệnh; scripts/check_student_finance_live.py và scripts/benchmark_local_ocr.py cho phép tái lập các phép thử tương ứng sau khi chuẩn bị môi trường.

<!-- PAGE -->

## 14 Những kết luận còn cần nghiên cứu

### 14.1 Khoảng trống bằng chứng

Nguồn CFPB và World Bank hỗ trợ bài toán dòng tiền và minh bạch chi phí nói chung; chúng không đo trực tiếp nhu cầu của du học sinh Việt Nam tại Trung Quốc. Tài liệu sản phẩm đối chiếu cho thấy các mẫu chức năng tồn tại, không chứng minh cách làm của Demo tốt hơn. Số test đạt chứng minh các trường hợp kỹ thuật đã kiểm tra, không chứng minh hiệu quả tài chính hay mức độ an toàn production.

Các phát biểu như “giảm nhập liệu”, “dễ hiểu hơn”, “giúp tránh thiếu tiền” và “tìm điều khoản nhanh hơn” hiện là mục tiêu thiết kế. Muốn chuyển thành kết luận thực nghiệm phải có phép đo phù hợp. Demo chưa có bằng chứng để tuyên bố loại bỏ phí đổi tiền, tối ưu lợi nhuận, dự đoán chính xác chi tiêu hoặc tự hiểu hợp đồng bảo hiểm.

### 14.2 Thiết kế nghiên cứu tiếp theo được đề xuất

**Nghiên cứu nhu cầu.** Tuyển có chủ đích khoảng 6–10 người có trải nghiệm đóng học phí, nhận trợ cấp hoặc giữ CNY/VND. Phỏng vấn theo kịch bản về lần thanh toán gần nhất, thông tin cần kiểm tra và cách xử lý thiếu tiền. Ghi chủ đề, trường hợp phản ví dụ và điều kiện tuyển; không dùng mẫu nhỏ để suy tỷ lệ cho toàn bộ sinh viên. Đây là đề xuất, chưa tuyển người hay thu dữ liệu.

**Thử nghiệm khả dụng.** Cho người mới thực hiện tạo hóa đơn, đọc OCR, lập kế hoạch, đọc cảnh báo và tìm điều khoản mà không được người hướng dẫn bấm hộ. Ghi tỷ lệ hoàn thành, lỗi nghiêm trọng, số lần cần trợ giúp, thời gian và khả năng phân biệt tiền thật với sandbox. So sánh nhập tay/OCR trên cùng độ khó, đảo thứ tự để giảm hiệu ứng học; xin phép trước khi ghi hình.

**Đánh giá OCR và trích xuất.** Xây bộ tài liệu đa bố cục có quyền sử dụng, gán nhãn thủ công cho tiền, tiền tệ và ngày. Tách bộ tinh chỉnh quy tắc khỏi bộ kiểm tra. Báo độ đúng từng trường, tỷ lệ cần sửa, tỷ lệ bỏ trống và thời gian. Tài liệu thực phải ẩn thông tin nhạy cảm; không tải lên dịch vụ ngoài khi chưa có sự đồng ý.

**Đánh giá truy xuất.** Tạo câu hỏi có đáp án và câu hỏi không có trong tài liệu, kèm trang chuẩn. Đo tỷ lệ tìm đúng đoạn trong top 5 và tỷ lệ báo thiếu chứng cứ đúng. Một đoạn chứa từ khóa nhưng sai ngữ cảnh phải tính là không đạt cho tác vụ đó.

**Đánh giá vận hành.** Bổ sung thử tải, sao lưu/khôi phục, HTTPS, kiểm tra phân quyền độc lập và giám sát lỗi. Nếu kết nối provider thật, đánh giá theo tài liệu, điều kiện tài khoản và môi trường của provider đó; không suy từ thành công của MOCK sang kết luận chuyển tiền thật đã an toàn.

### 14.3 Phạm vi có thể trình bày ở thời điểm hiện tại

Có thể trình bày Demo là MVP quản lý khoản phí và tài chính du học có OCR cục bộ, dự phóng theo lịch, dữ liệu FX công khai và tra cứu chứng cứ, kèm bộ mô phỏng thanh toán có xác nhận. Chưa nên giới thiệu là ví giữ tiền, hệ thống đổi tiền thời gian thực, chatbot LLM hoặc công cụ ra quyết định quyền lợi bảo hiểm.

<!-- PAGE -->

## 15 Nguồn tham khảo và phạm vi sử dụng

Tất cả URL bên dưới được đối chiếu trực tuyến ngày 18/10/2026. Nguồn sản phẩm dùng để tham khảo thiết kế; nguồn kỹ thuật dùng cho nguyên tắc triển khai. Không có quan hệ hợp tác hay chứng nhận từ các tổ chức được dẫn. Nội dung nguồn có thể thay đổi sau ngày truy cập.

### Nguồn về bài toán và trải nghiệm

**[01] Tài liệu cuộc thi International Track**

Tệp PDF 4 trang được lưu tại website Chiang Mai University. Trang thứ hai của tệp nêu các Topic A–F; trang thứ ba có danh mục hồ sơ và bằng chứng sandbox. Dùng cho bối cảnh Topic C/D và phạm vi nguyên mẫu; không dùng để suy ra kết quả nghiên cứu người dùng.

https://www.pol.cmu.ac.th/public/blog/attachment/download/7a51866a-4cee-42b5-9187-fa4e1f4df411

**[02] World Bank Remittance Prices Worldwide Methodology**

Mô tả sự khác nhau giữa phí chuyển, tỷ giá và margin cũng như giới hạn của dữ liệu tại một thời điểm. Áp dụng ở F09, F10 và F13; không lấy một mức phí toàn cầu làm phí của hành lang Việt Nam–Trung Quốc.

https://remittanceprices.worldbank.org/methodology

**[03] CFPB Creating a cash flow budget**

Công cụ lập ngân sách theo thời điểm dòng tiền, với số dư đầu, khoản thu và khoản chi. Dùng cho F06–F08; việc chuyển từ tuần sang ngày là thiết kế của Demo. Nguồn không nghiên cứu riêng sinh viên Việt Nam.

https://www.consumerfinance.gov/documents/10038/cfpb_creating-cash-flow-budget_tool_2021-08.pdf

**[04] Jakob Nielsen 10 Usability Heuristics for User Interface Design**

Nguồn Nielsen Norman Group về trạng thái hệ thống, quyền kiểm soát, ngăn lỗi, nhận biết lựa chọn và trợ giúp. Dùng cho F01, F12–F14; chưa có phép đo cho thấy Demo đã cải thiện usability bao nhiêu.

https://www.nngroup.com/articles/ten-usability-heuristics/

### Nguồn về truy cập an toàn

**[05] OWASP Authorization Cheat Sheet**

Cơ sở cho kiểm tra quyền và sở hữu trên từng yêu cầu ở F02 và kiến trúc chung.

https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

**[06] OWASP Session Management Cheat Sheet**

Cơ sở cho vòng đời phiên, token và cookie. Không được coi là kết quả audit độc lập.

https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

<!-- PAGE -->

## 15 Nguồn tham khảo tiếp theo

### Nguồn về OCR và mô hình tiền tệ

**[07] Tesseract.js API tại phiên bản 6.0.1 và hướng dẫn cài cục bộ**

Tài liệu createWorker, recognize và đường dẫn model. Dùng cho F04. Bản API khớp phiên bản runtime; trang cài đặt ở nhánh master có thể cập nhật độc lập.

https://github.com/naptha/tesseract.js/blob/v6.0.1/docs/api.md

https://github.com/naptha/tesseract.js/blob/master/docs/local-installation.md

**[08] Tesseract tessdata_fast**

Kho mô hình LSTM đã huấn luyện và giấy phép Apache 2.0. Dự án tải eng, vie, chi_sim tại commit cố định, không tự huấn luyện. URL sau dẫn chính phiên bản được cấu hình trong script.

https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd

**[09] pypdfium2 Documentation**

Tài liệu thư viện render PDF trước OCR. Đây là thành phần xử lý trang, không phải mô hình OCR.

https://pypdfium2.readthedocs.io/en/stable/

**[10] Wise Platform Multi currency accounts**

Mô tả quan hệ tài khoản và các balance theo tiền tệ. Tham khảo F05, không có tích hợp Wise và không suy điều kiện mở tài khoản từ tài liệu.

https://docs.wise.com/guides/product/accounts

**[11] PocketSmith Multi currency**

Nguồn sản phẩm chính thức về số dư nguyên tệ và đồng cơ sở. Tham khảo cách trình bày F05; không sử dụng bank feed hoặc công nghệ nội bộ PocketSmith.

https://www.pocketsmith.com/tour/multi-currency/

**[12] Frankfurter Exchange rate and currency data API**

Nguồn API tỷ giá miễn phí không cần key, quan sát theo ngày và hướng dẫn cache. App dùng các route v2 ở thời điểm đối chiếu; không dùng dữ liệu này như giá thực thi chuyển tiền.

https://frankfurter.dev/

https://api.frankfurter.dev/v2/rate/CNY/VND

<!-- PAGE -->

## 15 Nguồn nghiên cứu và bằng chứng nội bộ

### Nguồn về truy xuất và xử lý giao dịch

**[13] Lewis và cộng sự 2020 Retrieval Augmented Generation for Knowledge Intensive NLP Tasks**

Bài nghiên cứu về kết hợp truy xuất với sinh ngôn ngữ, arXiv 2005.11401. Dùng để phân biệt khái niệm RAG với tìm trích đoạn đang có ở F11; không tuyên bố Demo tái hiện mô hình trong bài.

https://arxiv.org/abs/2005.11401

**[14] Anthropic 2024 Building effective agents**

Bài kỹ thuật của nhà phát triển về mức phức tạp và phân biệt workflow với agent. Tham khảo F12 và ranh giới tự động hóa; không có tích hợp Anthropic trong app.

https://www.anthropic.com/engineering/building-effective-agents

**[15] Stripe API Idempotent requests**

Nguồn chính thức về khóa idempotency và retry. Tham khảo F06/F13 và nguyên tắc ghi không lặp; chưa kết nối Stripe.

https://docs.stripe.com/api/idempotent_requests

**[16] Peffers Tuunanen Rothenberger và Chatterjee 2007**

A Design Science Research Methodology for Information Systems Research. Journal of Management Information Systems 24(3), 45–77. DOI 10.2753/MIS0742-1222240302. Khung tổ chức nghiên cứu thiết kế ở mục 2; không dùng để khẳng định hoàn thành đánh giá thực địa.

https://www.jmis-web.org/articles/765

**[17] Stripe Webhooks**

Nguồn về xác minh, sự kiện trùng và xử lý bất đồng bộ. Tham khảo F14/F15; thuật toán chữ ký hiện tại là giao thức MOCK riêng.

https://docs.stripe.com/webhooks

### Bằng chứng nội bộ của Demo

**Tài liệu.** IMPLEMENTATION_REPORT.md ghi tiến độ và kiểm thử; STUDENT_FINANCE_GUIDE.md hướng dẫn các luồng; docs/17_CHALLENGE_IMPLEMENTATION.md mô tả triển khai mở rộng. docs/16_INTERACTIVE_AI_FRAMEWORK_RESEARCH.md là nghiên cứu hướng phát triển trước đó, không dùng thay cho hiện trạng đã đối chiếu trong tài liệu này.

**Mã và kiểm thử.** backend/app/ và frontend/src/ là căn cứ hiện thực; contracts/openapi-mvp.json là hợp đồng API; backend/tests/ và frontend/tests/ chứa ca thử. scripts/benchmark_local_ocr.py tạo ba mẫu tự soạn; scripts/check_student_finance_live.py gọi luồng qua HTTP. Các JSON/XML bằng chứng ở submission/evidence/ có thể đọc để kiểm tra lại số liệu mục 13.

**Thư mục gốc để tìm các tệp trên.** C:/Users/hungt/Documents/ChatGPT/Fintech hackathon/Insurance_Crossborder_Payment_Codex_Kit/. Tài liệu không chứa API key, mật khẩu, mã vận hành hay token đăng nhập.
