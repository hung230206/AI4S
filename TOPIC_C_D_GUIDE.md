> Local update, 20 October 2026: the default download now contains ten current China samples. Upload policy PDF 04 to fill its fields and benefit citations automatically, then review and save. There is no consumer JSON import. A claim form can also fill a draft case; attachments provide text-comparison warnings. See [DOCUMENT_ASSIST_UPGRADE.md](docs/DOCUMENT_ASSIST_UPGRADE.md) for current behaviour and limits. Earlier descriptions below are historical where they differ.

# Cập nhật OCR và luồng demo — 20/10/2026

- OCR chạy nền: sau khi đồng ý xử lý tệp, app hiển thị đang chờ/đang đọc. Có thể tải lại trang Thêm hóa đơn để xem tiếp kết quả. Không bấm tải nhiều lần khi tác vụ đang chạy.
- Ảnh giấy yêu cầu bồi thường bằng VND không phải hóa đơn cần thanh toán bằng CNY. App nhận diện biểu mẫu, không điền số tiền vào hóa đơn và cho chọn **Đưa vào hồ sơ bồi thường**. Chọn hồ sơ đang chuẩn bị hoặc tạo hồ sơ từ hợp đồng đã đối chiếu, rồi xác nhận đính kèm. Không cần upload lại. Đồng tiền và số tiền trong hồ sơ vẫn cần tự đối chiếu.
- Tại **Bảo hiểm & hồ sơ → Tải bộ tệp test C + D**, ZIP có thêm `claim-form-ocr.png` và `OCR-README.txt`. Ảnh này tự soạn, không có dữ liệu thật. Upload ảnh đó tại **Thêm hóa đơn** để thử nhận diện nhầm loại tài liệu và chuyển sang hồ sơ. Hợp đồng mẫu dùng CNY; ảnh minh họa dùng VND để kiểm tra cảnh báo, không tự đổi tiền. Dùng `claim-claim-form.txt` cho bộ hồ sơ CNY mẫu tương ứng.
- Khi thử thanh toán, phương thức mặc định là **Thành công tự động · sandbox**. Kiểm tra báo giá, tích đồng ý rồi xác nhận; không cần tài khoản vận hành. Biên nhận luôn ghi không chuyển tiền thật.
- Nếu chỉ cần hoàn thành demo, chọn **Dùng tỷ giá demo để tiếp tục** thay vì gọi tỷ giá tham chiếu. App ghi rõ `DEMO_RATE`, không dùng tỷ giá demo thay thế âm thầm.
- Sau thành công, trang giao dịch có bước tiếp theo tới Ngân sách hoặc Hồ sơ bồi thường. Hợp đồng liên quan được chọn sẵn nếu giao dịch xuất phát từ dự trù phí bảo hiểm. Thanh toán demo không kích hoạt hợp đồng, không trừ số dư sổ tiền và không gửi hồ sơ ra ngoài.

Chi tiết kỹ thuật và giới hạn: [OCR_AND_COMPLETE_DEMO_FLOW.md](docs/OCR_AND_COMPLETE_DEMO_FLOW.md).

---

## Managed Topic D RAG (19 October 2026)

User Q&A: `/knowledge`. Administrator CRUD/publication: `/admin/rag` with a server-provisioned account. See [RAG_GUIDE.md](RAG_GUIDE.md) for the complete admin-to-student test flow and [research/method](docs/22_TOPIC_D_MANAGED_RAG.md). Credentials are in an ignored private local file, never in this repository. Gemini still requires binary session consent; the source library can be searched locally without a model.

# Test luồng C + D

## Quyền AI mới (19/10/2026)

Gemini mặc định tắt; chỉ bật khi người dùng tự cấp quyền theo phiên. Bản miễn phí không gửi dữ liệu ngân sách/hợp đồng cá nhân hoặc hồ sơ bồi thường. Để hỏi từ `demo-policy.txt`, chọn nhóm đoạn tài liệu mẫu trong Cài đặt quyền Gemini. Tra cứu trực tiếp vẫn dùng tài liệu/tài khoản riêng ở máy chủ. Xem PRIVACY_GUIDE.md.


Bản online: https://ai4s-demo.onrender.com/insurance . Gemini đã được cấu hình và kiểm tra gọi thật trên Render.

Mở **Bảo hiểm & hồ sơ** (`/insurance`). Tạo tài khoản riêng để dữ liệu không lẫn với người khác.

1. Bấm **Tải bộ tệp test C + D**, giải nén ZIP.
2. Bấm **Thêm hợp đồng**. Tải `demo-policy.txt`, chọn **Dữ liệu mẫu tự soạn**, rồi **Tải lên và đọc tài liệu**.
3. Đọc hợp đồng và điền tên, phí, thời hạn cùng quyền lợi vào biểu mẫu. Kiểm tra số trang và câu điều khoản, tích xác nhận rồi lưu. Không cần tải tệp JSON.
4. Vào **Ngân sách & thu chi**, tạo sổ CNY có **1.000 CNY**. Quay lại hợp đồng → **Dự trù phí vào ngân sách** → chọn sổ → xác nhận. Dự phóng còn **200 CNY**; số dư hiện tại vẫn **1.000 CNY**.
5. Sang **Kiểm tra quyền lợi**, bấm so sánh. Ngoại trú khớp hạn mức **2.000 CNY**, vận chuyển y tế có khoảng trống. Đổi hạn mức ngoại trú thành **4.000 CNY** sẽ thấy thiếu hạn mức. Đổi ngày/lãnh thổ để thử trường hợp khác. Đây là so sánh dữ liệu bạn nhập, không phải quyết định bảo hiểm.
6. Trong hợp đồng, bấm **Tạo dự trù phí để thử sandbox** và đọc xác nhận. Khoản phí này do bạn tạo trong app, không phải hóa đơn nhà bảo hiểm. Mở **Xem giá trị VND**, lấy tỷ giá, kiểm tra tổng, chọn sandbox thành công, tích đồng ý rồi chạy thử. Biên nhận có dòng **NO REAL FUNDS MOVED**. Kế hoạch phí không bị tạo thêm lần nữa khi mở từ hóa đơn.
7. Sang **Hồ sơ bồi thường**, chọn hợp đồng, nhập tên hồ sơ và chi phí **500 CNY**, ngày sự kiện hôm nay rồi tạo.
8. Đính kèm `claim-invoice.txt`, `claim-medical-record.txt`, `claim-claim-form.txt` vào đúng ba mục. Các mục định danh/tài khoản chỉ tích đã chuẩn bị ngoài app, không tải giấy tờ thật lên.
9. Đối chiếu checklist → **đánh dấu đủ checklist** → tích xác nhận → cập nhật. Bấm **Xuất bộ hồ sơ ZIP** để kiểm tra checklist, nguồn hợp đồng, tệp đính kèm và nhật ký.
10. Nếu cần sửa, dùng **Sửa thông tin hồ sơ**, gỡ tệp sai hoặc quay lại chuẩn bị. Sau khi sửa cần xác nhận checklist lại. Nút **Ghi nhận tôi đã gửi ngoài ứng dụng** chỉ lưu lời xác nhận của bạn và mã/kênh tiếp nhận; ứng dụng không gửi hồ sơ tới công ty bảo hiểm.

Tệp test đều tự soạn, ngày được tạo lúc tải. Không dùng làm hợp đồng, hóa đơn hoặc chứng từ y tế thật. Các tệp đính kèm hồ sơ bồi thường không được gửi sang Gemini.

**Dùng được:** lưu và sửa hợp đồng, trích dẫn trang nguồn, kiểm tra quyền lợi, lập kế hoạch phí, dự phóng ngân sách, sandbox thanh toán, checklist/chứng từ/ZIP, nhắc việc khi mở trang, trợ lý đọc dữ liệu có giới hạn, tiếng Việt/Anh/Trung và sáng/tối.

**Chưa phát triển:** chuyển/đổi tiền thật; mua hoặc kích hoạt bảo hiểm; gửi hồ sơ qua API nhà bảo hiểm; xác thực hợp đồng/chứng từ; xét duyệt và chi trả bồi thường; email/SMS nhắc việc; theo dõi tỷ giá trong ngày. Gemini cần cấu hình riêng trên máy chủ; nếu thiếu khóa hoặc API lỗi vẫn có tra cứu trực tiếp.
