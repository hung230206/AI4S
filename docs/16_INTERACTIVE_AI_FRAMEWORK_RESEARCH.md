# Đánh giá hướng Interactive AI Framework cho Bảo An

Ngày kiểm tra nguồn: 18/10/2026, Asia/Bangkok.

Đầu vào là ảnh người dùng gửi về multi-currency ledger, Adaptive UI, OCR/RAG, dự báo thu chi, giám sát tỷ giá và bounded autonomy. Các chỉ số trích dẫn 1–10 trong ảnh không kèm danh mục tài liệu, nên chưa thể xác thực các tài liệu gốc đó. Báo cáo này dùng những nguồn độc lập được liên kết bên dưới. Đây là nghiên cứu và đề xuất; không xác nhận các module đề xuất đã được triển khai.

## Kết luận đề xuất

Hướng phát triển có giá trị nếu tập trung vào **chuẩn bị khoản phí và ngân sách cho du học sinh Việt Nam tại Trung Quốc**: đọc thông báo thu phí, kiểm tra dữ liệu, lập kế hoạch CNY/VND, chỉ ra thiếu hụt và hỗ trợ hiểu tài liệu. Nên triển khai theo từng workflow rõ ràng thay vì khởi đầu bằng một agent tự điều khiển mọi chức năng.

Đề xuất định vị: **Bảo An giúp du học sinh chuyển thông báo thu phí và tài liệu bảo hiểm thành kế hoạch tài chính có nguồn, có thể kiểm tra và do người dùng quyết định.**

Đây là lựa chọn thiết kế của dự án, không phải kết luận đã được kiểm chứng qua nghiên cứu người dùng hay thử nghiệm thị trường. Chưa có bằng chứng để gọi việc kết hợp các module này là một đóng góp nghiên cứu mới.

## Sản phẩm và tài liệu đối chiếu

| Hệ thống / nguồn | Điều nguồn xác nhận | Điều có thể học cho Bảo An |
|---|---|---|
| [Wise Platform — multi-currency accounts](https://docs.wise.com/guides/product/accounts) | Một profile có các balance theo tiền tệ; tài liệu yêu cầu kiểm tra eligibility và đồng tiền được hỗ trợ | Tách số dư theo nguyên tệ, dữ liệu tài khoản và định giá quy đổi; không đánh đồng sổ theo dõi với tài khoản giữ tiền thật |
| [Wise — fees](https://wise.com/help/articles/2893489/fees-for-holding-receiving-and-spending-money) | Giữ tiền và chuyển đổi/chi tiêu khác tiền tệ có các cơ chế phí khác nhau | Hiển thị nguyên tệ, tỷ giá và phí riêng; không hứa xóa phí chuyển đổi chỉ nhờ ledger |
| [Airwallex — wallets and funds flow](https://www.airwallex.com/docs/connected-accounts/about/wallets-and-funds-flow) | Wallet có balance riêng theo tiền tệ; chuyển nội bộ và thanh toán ra hệ thống bên ngoài là các luồng khác nhau | Phân biệt ghi sổ, điều chuyển nội bộ và chuyển tiền tới bên nhận |
| [PocketSmith — multi-currency](https://www.pocketsmith.com/tour/multi-currency/) | Theo dõi số dư nguyên tệ và quy đổi về đồng cơ sở | Thiết kế sổ tài chính cá nhân CNY/VND và tổng quan ngân sách |
| [PocketSmith — forecasting](https://learn.pocketsmith.com/getting-started/5Ju1xR1kdaMUx8dV2FfcXo/getting-started-step-four---view-and-analyse-the-data-using-pocketsmiths-reporting-and-forecasting-features-/7xFdk3sDCGpFwqQNeaAPbV) | Dự phóng từ số dư hiện tại và các sự kiện thu/chi theo ngân sách | Làm dự phóng có giải thích từ lịch thu/chi trước khi dùng mô hình học máy |
| [PaddleOCR — multilingual recognition](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html) | Có cấu hình/model nhận dạng tiếng Trung và tiếng Việt | Thử đọc ảnh/PDF quét, chọn model theo tài liệu và kiểm tra lại trường tiền/ngày |
| [Tesseract](https://github.com/tesseract-ocr/tesseract), [language data](https://github.com/tesseract-ocr/tessdata_fast) | OCR mã nguồn mở, có dữ liệu ngôn ngữ và giấy phép Apache 2.0 | Một lựa chọn chạy cục bộ để so sánh với PaddleOCR; chưa benchmark trên máy này |
| [Lewis et al., RAG](https://arxiv.org/abs/2005.11401) | Kết hợp truy xuất tri thức với mô hình sinh văn bản | Tách bước lấy nội dung khỏi bước tìm đoạn và sinh câu trả lời |
| [Frankfurter](https://frankfurter.dev/) | API miễn phí không cần key, dữ liệu tham chiếu chủ yếu theo ngày; không dành cho live trading | Dùng dữ liệu hiện có cho lập kế hoạch và cảnh báo theo ngày, gắn ngày nguồn rõ ràng |
| [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Phân biệt workflow cố định với agent tự điều phối; đề cao tính đơn giản, ground truth, checkpoints và kiểm thử | Bắt đầu bằng chuỗi tác vụ có kiểm soát; mọi hành động tài chính vẫn do backend kiểm tra và người dùng quyết định |

Các nguồn xác nhận tính năng/kiến trúc của chính hệ thống đó. Chúng không chứng minh Bảo An sẽ giảm phí, tăng độ chính xác hoặc đủ điều kiện cung cấp dịch vụ giữ/chuyển tiền.

## Những điểm phải sửa trong mô tả ở ảnh

### Ledger khác ví giữ tiền thật

Ledger lưu sự kiện và số tiền theo từng đồng tiền. Nó không tự tạo một tài khoản ngân hàng, giữ hộ tiền hoặc thực thi chuyển tiền. MVP có thể làm sổ cá nhân với số dư người dùng khai báo, thu/chi nhập tay và dữ liệu nhập từ tệp, nhưng phải ghi nguồn dữ liệu và thời điểm đối soát.

Không cộng trực tiếp CNY với VND. Giữ số tiền nguyên tệ làm dữ liệu gốc; tổng VND chỉ là một góc nhìn định giá theo ngày/tỷ giá cụ thể. Một lần đổi tiền được khai báo phải có hai vế tiền tệ và phí, không được ghi nhận nhầm là cả thu nhập lẫn chi phí tiêu dùng.

Wallet/provider thật là một tích hợp riêng. [Airwallex sandbox](https://www.airwallex.com/docs/developer-tools/sandbox-environment) yêu cầu tạo tài khoản; tài liệu nói Connected Account APIs cần liên hệ Sales. Không có cơ sở từ việc xem tài liệu để khẳng định tài khoản của người dùng hoặc hành lang Việt Nam–Trung Quốc đủ điều kiện.

### Không thể hứa “loại bỏ chi phí chuyển đổi”

Theo dõi nguyên tệ có thể tránh những bước quy đổi chỉ để hiển thị và giúp người dùng thấy tác động của phí. Việc đổi hoặc chuyển tiền thật vẫn phụ thuộc dịch vụ thanh toán và báo giá của họ. Chưa có tích hợp/provider comparison để chứng minh mức tiết kiệm. Cách mô tả phù hợp hơn: **minh bạch chi phí, hỗ trợ lựa chọn và hạn chế quy đổi không cần thiết khi khả năng dịch vụ cho phép**.

### OCR và RAG là hai phần khác nhau

- OCR: đọc chữ từ ảnh hoặc trang PDF quét.
- Trích xuất có cấu trúc: tìm mã hóa đơn, số tiền, tiền tệ, đơn vị và hạn thanh toán từ văn bản.
- Retrieval: tìm đoạn liên quan trong văn bản đã lưu.
- RAG: dùng đoạn đã truy xuất để hỗ trợ một mô hình sinh câu trả lời.

Luồng đề xuất: tệp gốc → đọc text/OCR → gợi ý trường dữ liệu → người dùng đối chiếu/sửa → lưu hóa đơn. Với chính sách: văn bản có nguồn → tìm đoạn → trả trích dẫn; chỉ thêm sinh câu trả lời sau khi có mô hình và đánh giá độ bám nguồn. OCR confidence không phải bảo đảm số tiền đúng.

### Theo dõi theo ngày khác tỷ giá thời gian thực

App đang dùng Frankfurter, lưu observation date và cache. Tăng tần suất gọi nguồn này không tạo ra dữ liệu intraday mới. Có thể xây cảnh báo khi xuất hiện quan sát mới hoặc khi giá trị tham chiếu vượt ngân sách. Muốn quảng bá realtime phải có nguồn tương ứng, thời điểm cập nhật, quyền sử dụng và đánh giá độ trễ.

### Dự phóng thu chi không đòi hỏi dự đoán tỷ giá

Một MVP hữu ích có thể tính từ số dư khai báo, trợ cấp/học bổng dự kiến, học phí, bảo hiểm, tiền nhà và sinh hoạt định kỳ. Phải phân biệt khoản đã xác nhận với khoản người dùng lên kế hoạch. Khi chưa có lịch sử, không tuyên bố mô hình đã học thói quen của người dùng.

Mô phỏng tác động của tỷ giá tăng/giảm là phân tích kịch bản, không phải lời dự đoán tỷ giá hoặc thời điểm nên đổi tiền.

## So với mã ứng dụng hiện tại

Kiểm tra `backend/app/fx.py`, `backend/app/documents.py`, `MVP_SCOPE.md` và các tài liệu triển khai hiện có.

| Thành phần | Hiện có | Khoảng trống |
|---|---|---|
| Tài khoản / hóa đơn | Tài khoản riêng, nhập/sửa/tìm/lưu trữ hóa đơn CNY | Chưa đọc ảnh để điền form tự động |
| Multi-currency ledger | Lưu số tiền CNY và snapshot quy đổi VND của hóa đơn/giao dịch | Chưa có tài khoản theo dõi tiền, sổ thu/chi, số dư và ngân sách đa tiền tệ |
| Adaptive UI | Hai lối vào theo nhu cầu, trạng thái và hướng dẫn theo trang | Chưa có AI điều phối bước tiếp theo; giao diện hiện chủ yếu là quy tắc lập trình |
| OCR/RAG | PDF có chữ/TXT/MD, tìm kiếm từ khóa/từ đồng nghĩa, trích đoạn gốc kèm trang | Chưa OCR ảnh/PDF quét, chưa semantic retrieval hoặc mô hình sinh câu trả lời |
| Dòng tiền | Hóa đơn và lịch sử thanh toán thử | Chưa có lịch thu nhập, chi định kỳ, dự phóng hoặc đối chiếu dự phóng/thực tế |
| Tỷ giá | Frankfurter theo ngày, cache và API lịch sử | Chưa có bảng biến động/ngưỡng ngân sách/thông báo; không có feed realtime |
| Kiểm soát giao dịch | Đồng ý thủ công gắn đúng báo giá, backend tính tiền, idempotency, sự kiện ký số và nhật ký | Chưa có agent tài chính; provider thực vẫn chưa kết nối |

## Thứ tự phát triển đề xuất

1. **Đọc hóa đơn và màn hình kiểm tra.** Nhận ảnh/PDF, trích trường có nguồn đối chiếu, đánh dấu thiếu/khó đọc; người dùng xác nhận trước khi tạo hồ sơ. Đây là điểm giảm thao tác rõ nhất so với form hiện tại.
2. **Ngân sách du học CNY/VND.** Sổ theo dõi số dư và thu/chi, lịch khoản phải trả, dự phóng 30 ngày dựa trên các khoản đã khai báo. Ghi rõ dữ liệu nhập tay hay nhập tệp và lần xác nhận gần nhất.
3. **Tác động tỷ giá tới ngân sách.** Biểu đồ lịch sử và chênh lệch chi phí VND so với mốc người dùng chọn; cảnh báo thiếu hụt dùng dữ liệu tham chiếu theo ngày. Không tự quyết định mua ngoại tệ.
4. **Tra cứu bảo hiểm sâu hơn.** OCR tài liệu quét và tìm kiếm ngữ nghĩa có đánh giá; nếu thêm sinh câu trả lời, mọi nhận định quan trọng phải gắn nguồn, cho phép mở trang gốc và không kết luận quyền lợi khi thiếu chứng cứ.
5. **Tích hợp provider sandbox.** Chỉ chọn sau khi có tài khoản, xác nhận API/quyền truy cập và luồng thanh toán phù hợp. Tích hợp thật không nằm trong kết quả nghiên cứu này.

AI được đề xuất đọc, phân loại, tìm, giải thích và tạo bản nháp. AI không được tự sửa số tiền đã xác nhận, đổi bên nhận, tự đồng ý thanh toán hay đánh dấu thành công từ lời trả lời của mô hình. Backend giữ quyền kiểm tra dữ liệu và trạng thái; người dùng giữ quyền quyết định hành động tài chính.

## Luồng demo mục tiêu để đánh giá

Người dùng tải thông báo thu phí → kiểm tra các trường được nhận dạng với bản gốc → lưu khoản phải trả → nhập số dư và lịch thu/chi → xem phần thiếu hụt đến hạn cùng tác động tỷ giá → mở điều khoản liên quan trong chính sách → nếu muốn, chuyển sang giao dịch sandbox có xác nhận riêng.

Chỉ tuyên bố đạt sau khi đo trên bộ tài liệu đại diện: độ chính xác trường số tiền/tiền tệ/ngày, tỷ lệ phải sửa, thời gian hoàn thành so với nhập tay, độ đúng nguồn trích dẫn, phát hiện tài liệu không có câu trả lời, độ đúng phép tính/sổ thu chi và mức hiểu của người thử về trạng thái thanh toán. Không có kết quả benchmark OCR/RAG mới trong lượt nghiên cứu này.

## Đoạn giới thiệu đề xuất

> Bảo An hỗ trợ du học sinh Việt Nam tại Trung Quốc quản lý khoản phí và ngân sách theo nguyên tệ. Hệ thống hướng tới việc đọc thông báo thu phí, cho người dùng kiểm tra dữ liệu, lập kế hoạch thu chi CNY/VND và theo dõi tác động của tỷ giá tham chiếu. Trợ lý tra cứu tài liệu bảo hiểm kèm nguồn và hướng dẫn bước tiếp theo theo từng tình huống. Các đề xuất của AI có thể được kiểm tra và chỉnh sửa; hành động thanh toán cần xác nhận riêng và chỉ được ghi nhận theo trạng thái do máy chủ xác minh.

Đoạn này mô tả hướng phát triển. Khi dùng để giới thiệu bản đang chạy, chỉ nêu những chức năng đã triển khai trong bảng hiện trạng ở trên.
