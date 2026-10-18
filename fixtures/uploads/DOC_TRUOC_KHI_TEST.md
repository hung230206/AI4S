# Bộ dữ liệu tải lên thử sản phẩm Demo

Tất cả nội dung, trường học, bên nhận, số tiền và điều khoản đều là dữ liệu tự soạn để kiểm thử. Không phải hóa đơn hoặc hợp đồng bảo hiểm thật. Không chuyển tiền theo các tệp này.

## Bắt đầu

1. Giải nén ZIP. Không tải nguyên ZIP, file hướng dẫn hoặc KET_QUA_MONG_DOI.json vào app.
2. Mở app và Tạo tài khoản riêng để tránh lẫn dữ liệu chung.
3. Muốn thử ảnh/PDF hóa đơn: Hóa đơn → Thêm hóa đơn → Nhập từ ảnh hoặc PDF → chọn tệp và ngôn ngữ → Đọc và điền thông tin.
4. Đối chiếu 5 trường được điền với bảng dưới, sửa nếu sai, tích xác nhận đã đối chiếu rồi Lưu hóa đơn.
5. Muốn thử bảo hiểm: Tài liệu bảo hiểm → chọn tệp, ngôn ngữ và Loại nguồn tài liệu = Dữ liệu mẫu tự soạn → tải lên; sau đó dùng các từ khóa bên dưới và kiểm tra trang nguồn.
6. Tên hóa đơn khác nhau cho từng tệp. Nếu tải lại cùng tệp, app có thể báo đã nhập hoặc mã trùng; dùng hóa đơn đã lưu hoặc một tài khoản mới.

## 01_Hoa_don

| Tệp | Ngôn ngữ | Tiền CNY | Hạn thanh toán | Kỳ vọng |
| --- | --- | --- | --- | --- |
| 01_en_800.png | Tiếng Anh | 800.00 | 2026-11-01 | 5/5 trường; LOCAL_TESSERACT |
| 02_vi_1200.jpg | Tiếng Việt và Anh | 1200.00 | 2026-11-08 | 5/5 trường; LOCAL_TESSERACT |
| 03_zh_5000.png | Tiếng Trung và Anh | 5000.00 | 2026-11-15 | 5/5 trường; LOCAL_TESSERACT |
| 04_scan_en_950.pdf | Tiếng Anh | 950.00 | 2026-10-28 | 5/5 trường; LOCAL_TESSERACT |
| 05_text_vi_1500.pdf | Tiếng Việt và Anh | 1500.00 | 2026-11-04 | 5/5 trường; TEXT_EXTRACT |
| 06_en_675.txt | Tiếng Anh | 675.50 | 2026-11-11 | 5/5 trường; TEXT_EXTRACT |
| 07_vi_2400.md | Tiếng Việt và Anh | 2400.00 | 2026-11-22 | 5/5 trường; TEXT_EXTRACT |

Ba tệp đầu thử OCR ảnh. 04_scan_en_950.pdf thử OCR PDF không có lớp chữ. 05_text_vi_1500.pdf thử PDF có lớp chữ, không cần OCR. TXT/MD thử phân tích văn bản thuần. Với mọi tệp, tiền tệ cần là CNY. File JSON liệt kê chính xác mã, đơn vị và bên nhận.

## 02_Bao_hiem

| Tệp | Ngôn ngữ | Tìm thử | Kết quả cần thấy |
| --- | --- | --- | --- |
| 01_policy_vi_text.pdf | Tiếng Việt và Anh | Hồ sơ bồi thường | Hóa đơn viện phí và giấy ra viện ở trang 2 |
| 01_policy_vi_text.pdf | Tiếng Việt và Anh | loại trừ | Phẫu thuật thẩm mỹ ở trang 3 |
| 01_policy_vi_text.pdf | Tiếng Việt và Anh | thời hạn | Ngày 31/10/2027 ở trang 1; có thể có đoạn khớp khác |
| 02_policy_en_scan.pdf | Tiếng Anh | claims / exclusions | hospital invoices ở trang 1 / elective cosmetic ở trang 2 |
| 03_policy_zh.png | Tiếng Trung và Anh | 理赔 | Đoạn có 理赔 ở trang 1 |
| 04_policy_vi.txt | Tiếng Việt và Anh | hồ sơ bồi thường | Hóa đơn viện phí ở trang 1 |

Câu hỏi không có đáp án: nhập XYZNOANSWER2026 trong tìm kiếm để kiểm tra không có đoạn khớp. Với câu hỏi tự nhiên, tìm theo từ khóa có thể trả đoạn liên quan nhưng không đủ trả lời; cần đọc đoạn nguồn. Các tệp có nội dung trùng chủ đề nên có thể xuất hiện nhiều kết quả. Chọn đúng tài liệu hoặc đối chiếu tên tệp.

## 03_Thu_loi

| Tệp | Cách thử | Kỳ vọng |
| --- | --- | --- |
| 01_non_cny_usd.txt | Nhập hóa đơn | Không tự điền số CNY; cảnh báo chưa xác định được CNY. Không tự đổi 200 USD thành 200 CNY |
| 02_blank.pdf | Nhập hóa đơn hoặc tài liệu | Báo không đọc được chữ; không tạo hóa đơn |
| 03_invalid.pdf | Nhập hóa đơn hoặc tài liệu | Báo PDF lỗi hoặc không đúng định dạng |
| 04_unsupported.csv | Chọn trong mục hóa đơn | Bộ chọn có thể ẩn CSV; nếu chọn được thì bị từ chối định dạng. CSV không phải tệp nhập ngân sách |

## Một luồng đầy đủ dễ thử

Tải 01_en_800.png → lưu hóa đơn 800 CNY → vào Ngân sách & thu chi tạo sổ CNY có số dư 1000 → mở hóa đơn và Đưa vào kế hoạch chi → xem Dự phóng: còn 200 CNY sau khoản này. Trước khi xác nhận đã chi, số dư thực tế vẫn 1000. Khi xác nhận kỳ kế hoạch đã chi, số dư còn 200 và dự phóng không trừ thêm 800 lần nữa.

Đây là số liệu test. Chỉ xác nhận đã chi để thử ghi sổ, không phải chứng nhận khoản chi ngoài đời. Thanh toán sandbox không tự ghi chi. Chưa có nhập hàng loạt sổ/thu chi từ Excel hoặc CSV.

## Lưu ý dữ liệu mẫu

Các hạn thanh toán được tạo tương đối so với 18/10/2026. Sau các ngày trong bảng, hãy sửa hạn khi lưu nếu muốn thử luồng thanh toán còn hạn. OCR có thể đọc sai; kết quả tự động thực tế của bộ tệp sẽ được ghi trong KET_QUA_KIEM_TRA.json sau khi chạy xác minh.

## Chạy bản hiện tại từ A đến Z

Mở /test-lab trong app để theo dõi sáu bước. Chọn Thành công tự động hoặc Bị từ chối tự động ở bước thanh toán trước khi tích đồng ý; không cần mã vận hành. Chỉ MANUAL mới cần người vận hành. Có thể tải hồ sơ ZIP ở trang giao dịch.

Với PDF gốc tải từ website trường, chọn Tài liệu tham khảo công khai và điền URL nguồn; đó không phải hợp đồng cá nhân được xác thực.
