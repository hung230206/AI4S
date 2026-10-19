# Bộ mẫu upload Trung Quốc - mỗi loại một tệp

10 tệp để upload, dùng chung sinh viên TEST STUDENT LI (tên hư cấu). Tất cả ghi SAMPLE - NOT VALID. Đây là chứng từ tự soạn dựa trên nghiên cứu bố cục thực tế, không phải hợp đồng/hóa đơn hợp lệ.

## Upload ở đâu?

| Tệp | Mục trên web | Dữ liệu cần thấy |
|---|---|---|
| 01_Hoc_phi_CNY.png | Khoản cần đóng → Thêm hóa đơn | CNY 20000.00; hạn 2026-12-20; TUITION |
| 02_Tien_ky_tuc_xa_CNY.png | Khoản cần đóng → Thêm hóa đơn | CNY 6000.00; hạn 2026-12-20; ACCOMMODATION |
| 03_Phi_bao_hiem_CNY.png | Khoản cần đóng → Thêm hóa đơn | CNY 800.00; hạn 2026-12-20; phí bảo hiểm |
| 04_Hop_dong_bao_hiem.pdf | Bảo hiểm → Thêm hợp đồng | Chọn nguồn Dữ liệu mẫu tự soạn; PDF có 2 trang |
| 05_Hoa_don_vien_phi.pdf | Hồ sơ yêu cầu chi trả → Hóa đơn viện phí | Đã chi CNY 980.00; không phải khoản đang chờ đóng |
| 06_Benh_an_kham_benh.pdf | Hồ sơ → Bệnh án / hồ sơ khám | Khám ngày 2026-10-11 |
| 07_Don_yeu_cau_boi_thuong.pdf | Hồ sơ → Đơn yêu cầu bồi thường | Yêu cầu CNY 980.00 |
| 08_Giay_ra_vien.pdf | Hồ sơ loại Nội trú → Giấy ra viện | Nhập viện 11/10, ra viện 14/10/2026 |
| 09_Bang_ke_chi_phi.pdf | Hồ sơ loại Nội trú → Bảng kê chi phí | 6 dòng cộng đúng CNY 980.00 |
| 10_Bien_ban_tai_nan.pdf | Hồ sơ loại Tai nạn → Biên bản tai nạn | Bản tự tường trình; không phải xác nhận công an |

Giấy tờ định danh và ngân hàng được app đánh dấu giữ bên ngoài: không tạo mẫu để upload cho hai mục này.

## Thử từ A tới Z

1. Dùng tài khoản test riêng. Upload một trong 3 ảnh thông báo thu phí. Chọn ngôn ngữ Tiếng Trung, đợi OCR, đối chiếu các trường với ảnh, kiểm tra loại phí được gợi ý và tick đã kiểm tra rồi lưu. OCR có thể không điền đủ mọi trường; sửa tay theo ảnh trước khi xác nhận.
2. Mở hóa đơn → xem số tiền VND → dùng tỷ giá demo nếu muốn thử độc lập API tỷ giá → tick đồng ý → chạy thanh toán sandbox tự động → xem biên nhận. Không có tiền thật được chuyển.
3. Vào Bảo hiểm → Thêm hợp đồng. Chọn tệp 04, đánh dấu đây là tài liệu mẫu rồi tải lên. App tự điền tên, phí, ngày hiệu lực và 4 nhóm quyền lợi kèm câu trích dẫn trang 2. Mở phần căn cứ tự điền để đối chiếu và bổ sung nếu còn thiếu. Kiểm tra lại, tick xác nhận rồi lưu; không cần tải tệp JSON.
4. Ở tab Hồ sơ bồi thường, chọn hợp đồng rồi dùng ô Điền từ chứng từ y tế để tải tệp 07. Kiểm tra ngày 2026-10-11, số tiền 980.00 CNY và loại Nội trú được điền sẵn, tick đã kiểm tra rồi tạo hồ sơ; thêm tệp 05, 06, 07, 08, 09 vào đúng mục. Chỉ tick định danh/ngân hàng đã chuẩn bị bên ngoài khi thao tác test đó là có chủ ý; không upload giấy tờ thật.
5. Sau khi đính kèm PDF, app đối chiếu số tiền, ngày và nhóm tài liệu, báo khác biệt nếu có. Đối chiếu văn bản không xác thực chứng từ hoặc quyết định quyền lợi. Kiểm tra checklist rồi tải bộ hồ sơ. Đây là chuẩn bị/xuất hồ sơ, chưa gửi tới nhà bảo hiểm. Nếu muốn test nhánh Tai nạn, tạo hồ sơ Tai nạn và thêm 05, 06, 07, 10; mục đính kèm của app phụ thuộc loại hồ sơ.

Không upload toàn bộ ZIP vào ô hóa đơn. Giải nén và chọn từng tệp đúng mục. Không cần tạo lại hợp đồng nếu đang test tiếp cùng một hồ sơ.

## Câu hỏi thử với tài liệu mẫu

- Hợp đồng mẫu có bảo vệ ngoài Trung Quốc không? Trích dẫn trang.
- Tôi có được tự động gia hạn hợp đồng mẫu này không?
- Quyền lợi vận chuyển y tế có được bao gồm không?
- Hồ sơ nội trú của tôi cần những nhóm chứng từ nào theo hợp đồng mẫu?

Trợ lý dùng trích đoạn tài liệu tùy quyền và chế độ xử lý; không biến tài liệu mẫu thành quy định chung hoặc chứng cứ bảo hiểm có thật.

Xem NGUON_NGHIEN_CUU.md để biết từng nguồn và phần nào là dữ liệu tự đặt. Kết quả kiểm thử kỹ thuật được lưu trong báo cáo triển khai của dự án.
