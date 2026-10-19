"""Self-authored China-style test documents; no real issuer, patient or identifiers.

Run with the bundled document Python runtime (reportlab/pypdf/Pillow).
Research mapping and upload instructions are included in the generated archive.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
from decimal import Decimal
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab import rl_config
from pypdf import PdfReader
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
rl_config.invariant = 1  # Reproducible bytes: rerendering a guide must not change tested PDF hashes.
OUT = ROOT / "output/pdf/Demo_Upload_China_2026_10_20"
TMP = ROOT / "tmp/pdfs/research-upload-samples"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
FONT = Path(os.environ.get("DEMO_CJK_FONT", "C:/Windows/Fonts/simsun.ttc"))
pdfmetrics.registerFont(TTFont("CN", str(FONT), subfontIndex=0))
NAVY = colors.HexColor("#233b52")
RED = colors.HexColor("#993b38")
LINE = colors.HexColor("#b8c1c9")
WIDTH = A4[0] - 88
styles = {
    "body": ParagraphStyle("body", fontName="CN", fontSize=10, leading=16, wordWrap="CJK", spaceAfter=7),
    "small": ParagraphStyle("small", fontName="CN", fontSize=8, leading=12, wordWrap="CJK"),
    "title": ParagraphStyle("title", fontName="CN", fontSize=19, leading=26, textColor=NAVY, spaceAfter=8),
    "sub": ParagraphStyle("sub", fontName="CN", fontSize=11, leading=17, textColor=NAVY, spaceAfter=12),
    "section": ParagraphStyle("section", fontName="CN", fontSize=11, leading=17, textColor=NAVY, spaceBefore=10, spaceAfter=7),
    "total": ParagraphStyle("total", fontName="CN", fontSize=17, leading=24, textColor=NAVY),
}


def p(text, kind="body"):
    return Paragraph(escape(text).replace("\n", "<br/>"), styles[kind])


def table(rows, widths=None, header=False):
    values = [[p(str(cell), "small" if header else "body") for cell in row] for row in rows]
    t = Table(values, colWidths=widths or [WIDTH / len(rows[0])] * len(rows[0]), hAlign="LEFT")
    commands = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf0f3"))]
    t.setStyle(TableStyle(commands))
    return t


def section(title, body):
    return [p(title, "section"), p(body)]


def chrome(canvas, doc):
    canvas.saveState()
    canvas.setFont("CN", 9)
    canvas.setFillColor(RED)
    canvas.drawString(44, A4[1] - 31, "测试样本 / SAMPLE - NOT VALID / 仅用于 Demo 上传测试")
    canvas.setStrokeColor(LINE)
    canvas.line(44, A4[1] - 41, A4[0] - 44, A4[1] - 41)
    canvas.line(44, 43, A4[0] - 44, 43)
    canvas.setFont("CN", 7.5)
    canvas.setFillColor(NAVY)
    canvas.drawString(44, 29, "虚构机构及人员，无公章、无付款二维码。 Fictional entities; no official seal or payment code.")
    canvas.drawRightString(A4[0] - 44, 17, f"DEMO-CHINA-2026 | {doc.page}")
    canvas.restoreState()


def build(filename, title, subtitle, story, expected_pages=1, final=True):
    path = (OUT if final else TMP) / filename
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=44, rightMargin=44,
                            topMargin=58, bottomMargin=58, title=title, author="Demo - fictional test documents")
    doc.build([p(title, "title"), p(subtitle, "sub"), *story], onFirstPage=chrome, onLaterPages=chrome)
    reader = PdfReader(path)
    assert len(reader.pages) == expected_pages, (filename, len(reader.pages))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "SAMPLE - NOT VALID" in text and "测试样本" in text, filename
    return path


def render(pdf, target):
    poppler = shutil.which("pdftoppm")
    if not poppler:
        raise RuntimeError("pdftoppm is required for rendered visual verification")
    subprocess.run([poppler, "-r", "150", "-png", str(pdf), str(target)], check=True, capture_output=True)
    return sorted(target.parent.glob(target.name + "-*.png"))


student = "TEST STUDENT LI / 李同学（测试）"
school = "Demo International University (fictional)"
hospital = "Demo Teaching Hospital (fictional)"
insurer = "Demo Study Insurance (fictional)"
case = "DEMO-CASE-CN-20261011"
policy_no = "DEMO-POL-CN-2026-001"
manifest = []
for no, category, title, amount, fee_type in [
    ("01", "Hoc_phi", "学费缴费通知 / Tuition fee notice", "20000.00", "TUITION"),
    ("02", "Tien_ky_tuc_xa", "住宿费缴费通知 / Accommodation fee notice", "6000.00", "ACCOMMODATION"),
    ("03", "Phi_bao_hiem", "保险费缴费通知 / Insurance premium notice", "800.00", "ANNUAL_HEALTH_INSURANCE_PREMIUM"),
]:
    inv = f"DEMO-CN-{no}-2026"
    story = [table([["学生 / Student", student], ["学号 / Student reference", "DEMO-STU-2026-001"],
                    ["学年 / Academic year", "2026-2027"], ["项目 / Item", title.split(" / ")[0]]], [160, WIDTH - 160]), Spacer(1, 17),
             p(f"Invoice number: {inv}"), p(f"Issuer: {school if no != '03' else insurer}"),
             p(f"Beneficiary: {school if no != '03' else insurer}"),
             p("Due date: 2026-12-20"), Spacer(1, 10), p(f"Total due: CNY {amount}", "total"), Spacer(1, 14),
             *section("缴费说明 / Payment instructions", "This is an unpaid test fee notice, not a tax invoice or payment receipt. Review the recipient and amount before trying the sandbox payment. No real bank details or payment channel is provided."),
             *section("备注 / Notes", "All amounts and institutions in this file are test data. The fee-category structure follows Chinese university student guidance; it is not a quotation from any real school."),
             p("References: S1, S2. See NGUON_NGHIEN_CUU.md in the sample pack.", "small")]
    pdf = build(f"{no}_{category}.pdf", title, "国际学生费用管理 / International student account - UNPAID TEST NOTICE", story, final=False)
    png = render(pdf, TMP / f"{no}_render")[0]
    name = f"{no}_{category}_CNY.png"
    shutil.copyfile(png, OUT / name)
    manifest.append({"file": name, "upload_to": "/invoices/new", "language": "zh", "invoice_number": inv,
                     "institution_name": school if no != "03" else insurer, "beneficiary_name": school if no != "03" else insurer,
                     "amount_cny": amount, "due_date": "2026-12-20", "fee_type": fee_type})

benefit_quotes = {
    "OUTPATIENT": "OUTPATIENT: INCLUDED; limit CNY 5000.00; deductible CNY 100.00; reimbursement 80%; waiting 0 days.",
    "INPATIENT": "INPATIENT: INCLUDED; limit CNY 100000.00; deductible CNY 0.00; reimbursement 100%; waiting 0 days.",
    "ACCIDENT": "ACCIDENT: INCLUDED; limit CNY 20000.00; deductible CNY 0.00; reimbursement 100%; waiting 0 days.",
    "EVACUATION": "EVACUATION: EXCLUDED; no evacuation benefit is included in this test plan.",
}
policy_story = [table([["保单号 / Policy reference", policy_no], ["被保险人 / Insured", student], ["承保机构 / Test issuer", insurer],
                       ["保险期间 / Period", "2026-09-01 to 2027-08-31 (inclusive)"], ["地域 / Territory", "Mainland China (CN)"],
                       ["币种及保费 / Premium", "CNY 800.00 / year"], ["应付日期 / Premium due", "2026-12-20"]], [175, WIDTH - 175]),
                *section("重要说明 / Important", "This is a self-authored TEST_FIXTURE, not an issued policy or a real insurer's terms. The dates, limits, percentages and exclusions are invented for testing. Paying in Demo does not activate cover."),
                *section("保障责任 / Benefits", "Page 2 contains exact English benefit statements for source-based review. Use those lines when adding a reviewed policy in Demo."),
                *section("续保 / Renewal", "No automatic renewal is promised in this test plan. A new application and acceptance are required when the test period ends."),
                p("Structural references: S2, S3. Test benefit amounts are not taken from those sources.", "small"),
                PageBreak(), p("保障表及理赔材料 / Benefits and claim documents", "title"),
                p("The following four statements are the authoritative terms of this fictional test fixture only.")]
for kind, quote in benefit_quotes.items():
    policy_story += [p(kind, "section"), p(quote)]
policy_story += section("费用及材料 / Costs and supporting documents", "Only documented, reviewed expenses may be considered in this fictional workflow. Keep the hospital bill, medical record and claim form. For inpatient cases also keep the discharge summary and itemized statement. For an accident, keep the accident statement. Identity and bank records stay outside Demo.")
policy_story += section("范围限制 / Limits", "Cosmetic procedures and treatment outside mainland China are excluded in this test plan. Missing evidence requires further review. No statement here guarantees claim approval.")
policy_path = build("04_Hop_dong_bao_hiem.pdf", "留学生综合保险 / Student insurance schedule", "TEST POLICY SCHEDULE AND TERMS - NOT ISSUED COVER", policy_story, expected_pages=2)
manifest.append({"file": policy_path.name, "upload_to": "/assistant", "document_kind": "TEST_FIXTURE", "references": ["S2", "S3"]})

charges = [("诊察费 / Consultation", "1", "80.00", "80.00"), ("检查费 / Imaging", "1", "120.00", "120.00"),
           ("治疗费 / Treatment", "1", "200.00", "200.00"), ("药品费 / Medicines", "1", "180.00", "180.00"),
           ("床位费 / Bed", "3", "100.00", "300.00"), ("护理费 / Nursing", "1", "100.00", "100.00")]
assert sum(Decimal(row[3]) for row in charges) == Decimal("980.00")
assert all(Decimal(q) * Decimal(u) == Decimal(a) for _, q, u, a in charges)
common = [["患者 / Patient", student], ["就诊机构 / Hospital", hospital], ["病例编号 / Case reference", case],
          ["就诊日期 / Treatment dates", "2026-10-11 to 2026-10-14"]]
bill = build("05_Hoa_don_vien_phi.pdf", "医疗住院收费凭证 / Hospital billing sample", "PAID TEST EXPENSE - NOT A FISCAL OR TAX INVOICE", [
    table(common + [["票据编号 / Bill reference", "DEMO-BILL-CN-20261014-001"], ["开具日期 / Issue date", "2026-10-14"]], [175, WIDTH - 175]), Spacer(1, 14),
    table([["费用项目 / Category", "金额 CNY / Amount"], *[[r[0], r[3]] for r in charges]], [WIDTH - 130, 130], header=True), Spacer(1, 14),
    p("Total paid: CNY 980.00", "total"), p("个人支付 / Patient paid: CNY 980.00. Other payer: CNY 0.00."),
    p("No verifiable fiscal code, official seal or tax verification QR code is provided. Reference S4 supplies field/layout inspiration only.", "small")])
record = build("06_Benh_an_kham_benh.pdf", "门急诊病历 / Medical encounter record", "FICTIONAL CLINICAL RECORD - NOT MEDICAL ADVICE", [table(common, [175, WIDTH - 175]),
    *section("科室及时间 / Department and time", "Emergency / 2026-10-11 14:30. Record reference: DEMO-MR-20261011-001."),
    *section("主诉 / Presenting complaint", "A fictional student reports ankle pain after falling on campus at 13:40 on 2026-10-11."),
    *section("现病史及检查 / History and examination", "Synthetic training narrative: a fall on a wet campus walkway, local pain and swelling. This document describes no real patient or examination."),
    *section("诊断 / Test diagnosis", "Ankle injury (fictional case for document-workflow testing)."),
    *section("处理及去向 / Recorded disposition", "Synthetic observation and supportive care were recorded. Transferred to the test inpatient department on 2026-10-11; discharge recorded on 2026-10-14."),
    *section("记录者 / Recorded by", "Demo Clinician A (fictional, no signature or professional credential)."),
    p("Reference S5: field headings only; all clinical narrative is newly authored test content.", "small")])
claim = build("07_Don_yeu_cau_boi_thuong.pdf", "CLAIM FORM / 理赔申请书", "APPLICATION FOR TEST CLAIM PREPARATION ONLY", [
    table([["申请人 / Applicant", student], ["保单号 / Policy reference", policy_no], ["案件编号 / Case reference", case],
           ["事故日期 / Incident date", "2026-10-11"], ["类型 / Claim type", "Inpatient medical expense following a campus accident"],
           ["申请金额 / Amount requested", "CNY 980.00"], ["申请日期 / Application date", "2026-10-20"]], [175, WIDTH - 175]),
    *section("事故经过 / Circumstances", "The test student fell on a wet campus walkway and received care from 2026-10-11 to 2026-10-14. The hospital bill and itemized statement both total CNY 980.00."),
    *section("随附材料 / Attachments", "Hospital bill; medical record; discharge summary; itemized costs; accident statement. All are fictional samples included in this pack."),
    *section("身份及收款资料 / Identity and payment details", "Not included. Keep identity and bank documents outside Demo. No actual account number, passport number, signature or phone number is supplied."),
    *section("声明 / Declaration", "Unsigned test application. Preparing or exporting this form in Demo does not submit it to an insurer or approve a payment."),
    p("References S3 and S6: document categories only; this is not the provider's official form.", "small")])
discharge = build("08_Giay_ra_vien.pdf", "出院记录 / Discharge summary", "FICTIONAL INPATIENT SUMMARY", [
    table(common + [["入院时间 / Admission", "2026-10-11 16:00"], ["出院时间 / Discharge", "2026-10-14 10:00"], ["住院参考号 / Stay reference", "DEMO-IP-20261011-001"]], [175, WIDTH - 175]),
    *section("入院情况 / Admission summary", "Synthetic case: ankle pain and reduced mobility after a campus fall. This narrative was created solely for software testing."),
    *section("诊疗经过 / Course", "Test observation and supportive care were recorded between the stated admission and discharge dates. No real clinical decision is represented."),
    *section("出院诊断及情况 / Discharge diagnosis and condition", "Fictional ankle injury; discharged in stable condition in the test scenario."),
    *section("出院说明 / Discharge note", "This sample is not an instruction to any patient. Actual treatment and follow-up must come from the treating clinician."),
    *section("记录者 / Recorded by", "Demo Clinician A (fictional, unsigned). Test hospital bill: CNY 980.00."),
    p("Reference S5: discharge-record field structure only.", "small")])
cost = build("09_Bang_ke_chi_phi.pdf", "住院费用明细 / Itemized hospital costs", "DETAIL OF THE SAME FICTIONAL CNY 980.00 HOSPITAL BILL", [
    table(common + [["关联票据 / Related bill", "DEMO-BILL-CN-20261014-001"]], [175, WIDTH - 175]), Spacer(1, 17),
    table([["项目 / Item", "数量 / Qty", "单价 / Unit", "金额 / CNY"], *charges], [WIDTH - 225, 65, 80, 80], header=True), Spacer(1, 17),
    p("Total: CNY 980.00", "total"),
    *section("对账 / Reconciliation", "6 charge lines. Each quantity multiplied by its unit price equals its line amount. The sum equals the bill and claim request. No deductible, insurer reimbursement or transfer has been applied."),
    p("Reference S4: itemized cost field structure only. Prices are fictional test values.", "small")])
accident = build("10_Bien_ban_tai_nan.pdf", "意外事故说明 / Accident statement", "SELF-REPORTED TEST STATEMENT - NOT A POLICE CERTIFICATE", [
    table([["陈述人 / Reporting student", student], ["事件编号 / Incident reference", case], ["时间 / Time", "2026-10-11 13:40"],
           ["地点 / Place", "Demo International University - campus walkway (fictional)"]], [175, WIDTH - 175]),
    *section("经过 / Account", "In this fictional scenario, the student slipped on a wet campus walkway, fell and reported ankle pain. Care began at the fictional hospital at 14:30 that day."),
    *section("性质 / Nature", "Self-reported campus fall. No vehicle or traffic event is described. No police conclusion, fault determination or insurer acceptance is represented."),
    *section("材料关联 / Related documents", f"Hospital case {case}. Admission 2026-10-11; discharge 2026-10-14. Hospital costs CNY 980.00."),
    *section("签名及日期 / Signature and date", "Unsigned sample / 2026-10-20. Names of witnesses and personal contact details are intentionally absent."),
    p("References S3 and S6: accident-material category. This self-authored statement cannot replace an authority's certificate where required.", "small")])
for path, code in [(bill, "INVOICE"), (record, "MEDICAL_RECORD"), (claim, "CLAIM_FORM"), (discharge, "DISCHARGE"), (cost, "COST_BREAKDOWN"), (accident, "ACCIDENT_REPORT")]:
    manifest.append({"file": path.name, "upload_to": "/insurance/claims/{id}", "item_code": code, "amount_cny": "980.00", "case_reference": case})

source_text = """# Nguồn nghiên cứu và phạm vi áp dụng

Ngày tham khảo: 20/10/2026. Tất cả 10 tệp là tài liệu tự soạn dùng để test, không phải bản gốc tải từ các đơn vị dưới đây.
Các nguồn chỉ làm cơ sở chọn loại giấy tờ, nhóm thông tin và cách trình bày. Không sao chép logo, con dấu, mã xác thực hoặc nội dung hợp đồng hoàn chỉnh.
Không xác nhận hiệu lực pháp lý hiện tại của các văn bản cũ; đây là nghiên cứu bố cục chứng từ, không phải bộ luật đưa vào RAG.

## S1 - Các nhóm phí du học
Jiangsu University of Science and Technology, trang dịch vụ đóng phí cho sinh viên quốc tế. Dùng để chọn nhóm học phí, chỗ ở và bảo hiểm; không dùng mức học phí thực của trường.
https://admission.just.edu.cn/10238/list.htm
Trang tìm kiếm có chỉ mục nhưng công cụ mở trang trực tiếp không truy cập được trong lần kiểm tra này.

## S2 - Thông báo mua bảo hiểm cho sinh viên quốc tế
Shanghai Jiao Tong University, thông báo 2025 và hướng dẫn mua bảo hiểm/nhận biên nhận. Tham khảo cấu trúc thời hạn, phí năm và quy trình giữ chứng từ. Mức 800 CNY cũng xuất hiện ở nguồn, nhưng hồ sơ mẫu không thuộc sản phẩm đó; mọi quyền lợi và mức chi trả trong mẫu do người tạo tự đặt.
https://isc.sjtu.edu.cn/kindeditor/Upload/file/20250826/20250826031349_9371.pdf

## S3 - Nhóm tài liệu phục vụ bảo hiểm du học
Hohai University, trang hướng dẫn y tế: liên kết tài liệu bảo hiểm, đơn yêu cầu và bản tường trình tai nạn; liệt kê hồ sơ khám, hóa đơn, giấy ra viện và bảng kê.
https://cie.hhu.edu.cn/16190/listm.htm
Đọc được trang hướng dẫn; các PDF mẫu đính kèm bị giới hạn truy cập ngoài trường. Không tuyên bố đã đọc các PDF bị chặn đó.

## S4 - Bố cục chứng từ thu phí y tế
Guangdong Department of Finance đăng thông báo triển khai chứng từ thu phí y tế điện tử và các mẫu hóa đơn/bảng kê. Dùng làm cơ sở cho tên chứng từ, nhóm phí và đối chiếu tổng; không làm bản sao hóa đơn thuế điện tử.
https://czt.gd.gov.cn/czpw/content/post_2644253.html
https://czt.gansu.gov.cn/czt/c107536/201908/791023/files/1302331ac3f14602800414fab74b7f6e.pdf
Nội dung có chỉ mục tìm kiếm; truy cập toàn văn bị lỗi/chặn. Không tái tạo các chi tiết bảo an của mẫu gốc.

## S5 - Nhóm thông tin bệnh án và giấy ra viện
National Health Commission, 病历书写基本规范, 2010. Tham khảo tiêu đề về thông tin người bệnh, ngày khám, lý do khám, diễn biến, chẩn đoán và xuất viện. Không sử dụng bản thử nghiệm 2002 làm nguồn chính. Toàn bộ tình huống lâm sàng trong mẫu là hư cấu.
https://www.nhc.gov.cn/wjw/gfxwj/201002/79d42b9c8b3f47ee91000d31de116784.shtml
Nội dung đọc từ chỉ mục tìm kiếm; mở lại toàn trang bị HTTP 412.

## S6 - Checklist hồ sơ chi trả bảo hiểm du học
lxbx.net, hướng dẫn chuẩn bị hồ sơ: hóa đơn, hồ sơ khám, bảng kê, giấy ra viện và tài liệu tai nạn tùy trường hợp.
https://www.lxbx.net/storage/website/20240402/Q420240402144639403992859232.pdf
Đã đọc PDF. Dùng để chọn nhóm chứng từ, không đưa lời khuyên y tế hoặc kết luận chi trả vào mẫu.

## Những dữ liệu được tự đặt
Tên trường, bệnh viện, doanh nghiệp; tên sinh viên; mã hồ sơ; số tiền 20.000/6.000/980 CNY; ngày điều trị; quyền lợi, mức khấu trừ và tỷ lệ hoàn trả của hợp đồng là dữ liệu thử. Không có giấy tờ định danh, tài khoản ngân hàng, chữ ký, QR thanh toán hoặc con dấu thật.
"""
(OUT / "NGUON_NGHIEN_CUU.md").write_text(source_text, encoding="utf-8")
readme = """# Bộ mẫu upload Trung Quốc - mỗi loại một tệp

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
"""
(OUT / "DOC_TRUOC_KHI_UPLOAD.md").write_text(readme, encoding="utf-8")
code_labels = {"INVOICE": "Hóa đơn viện phí", "MEDICAL_RECORD": "Bệnh án / hồ sơ khám", "CLAIM_FORM": "Đơn yêu cầu bồi thường", "DISCHARGE": "Giấy ra viện", "COST_BREAKDOWN": "Bảng kê chi phí", "ACCIDENT_REPORT": "Biên bản tai nạn"}
rows = "".join(f'<tr><td><a href="{escape(item["file"])}">{escape(item["file"])}</a></td><td>{escape("Thêm hóa đơn" if item["upload_to"] == "/invoices/new" else "Tài liệu bảo hiểm" if item["upload_to"] == "/assistant" else "Trong hồ sơ yêu cầu chi trả: " + code_labels[item["item_code"]])}</td></tr>' for item in manifest)
guide_html = '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Hướng dẫn upload tài liệu mẫu</title><style>body{max-width:980px;margin:35px auto;padding:0 20px;font:16px/1.7 system-ui;color:#203345}h1{font-size:27px}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border:1px solid #ccd5dc}th{background:#edf2f5}a{color:#156e63}.note{padding:15px;background:#fff1dc;border-radius:8px}code{background:#edf2f5}</style><h1>10 tài liệu mẫu để upload</h1><p class="note">Tất cả là dữ liệu hư cấu, ghi SAMPLE - NOT VALID. Không dùng làm hóa đơn, hợp đồng hoặc hồ sơ chi trả thật.</p><p>Chọn từng tệp theo bảng. Không upload cả ZIP vào ô hóa đơn. Ba ảnh đầu: chọn ngôn ngữ OCR Tiếng Trung rồi đối chiếu trước khi lưu.</p><table><tr><th>Tệp (bấm để xem)</th><th>Upload ở đâu?</th></tr>''' + rows + '''</table><h2>Thử nhanh</h2><ol><li>Upload ảnh 01, 02 hoặc 03 ở Thêm hóa đơn → kiểm tra dữ liệu → lưu → xem VND → tick đồng ý và thử thanh toán demo → xem biên nhận.</li><li>Vào Bảo hiểm → Thêm hợp đồng. Tải PDF 04 với loại tài liệu mẫu. App tự điền thông tin chính và quyền lợi từ PDF, kèm số trang và câu trích dẫn để đối chiếu. Kiểm tra rồi tick xác nhận và lưu.</li><li>Tạo hồ sơ Nội trú: ngày sự kiện <code>2026-10-11</code>, số tiền <code>980.00 CNY</code>; thêm 05, 06, 07, 08, 09 vào đúng mục. Nếu test Tai nạn: dùng 05, 06, 07, 10.</li><li>Định danh và tài khoản ngân hàng giữ bên ngoài. Kiểm tra checklist và xuất bộ hồ sơ; app chưa gửi tới nhà bảo hiểm.</li></ol><p>Hóa đơn viện phí 05 là khoản đã chi, không đưa vào luồng đóng phí lần nữa. Bộ chứng từ y tế có cùng mã ca, ngày điều trị và tổng 980 CNY.</p><p><a href="DOC_TRUOC_KHI_UPLOAD.md">Hướng dẫn chi tiết</a> · <a href="NGUON_NGHIEN_CUU.md">Nguồn nghiên cứu và phần tự đặt</a></p></html>'''
(OUT / "MO_HUONG_DAN.html").write_text(guide_html, encoding="utf-8")
review = {"name": "Demo Student Plan 2026", "insurer": insurer, "notes": "Self-authored test policy. Not issued cover or insurer approval.",
          "currency": "CNY", "premium": "800.00", "premium_due": "2026-12-20", "starts_on": "2026-09-01", "ends_on": "2027-08-31", "territory": "CN", "benefits": []}
for kind, limit, deductible, percent in [("OUTPATIENT", "5000.00", "100.00", 80), ("INPATIENT", "100000.00", "0.00", 100), ("ACCIDENT", "20000.00", "0.00", 100), ("EVACUATION", None, None, None)]:
    review["benefits"].append({"kind": kind, "status": "EXCLUDED" if kind == "EVACUATION" else "INCLUDED", "limit": limit,
                               "deductible": deductible, "reimbursement_percent": percent, "waiting_days": None if kind == "EVACUATION" else 0,
                               "source_page": 2, "evidence_quote": benefit_quotes[kind]})
(OUT / "REVIEW_FIELDS.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "UPLOAD_MAP.json").write_text(json.dumps({"invoices": manifest[:3], "claim": {"incident_date": "2026-10-11", "amount": "980.00", "currency": "CNY"}, "uploads": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
all_text = " ".join(PdfReader(policy_path).pages[1].extract_text().split())
assert all(quote in all_text for quote in benefit_quotes.values()), "Policy evidence quote must match extracted page text"
assert len(list(OUT.glob("*.pdf"))) == 7 and len(list(OUT.glob("*.png"))) == 3
previews = []
for pdf in sorted(OUT.glob("*.pdf")):
    previews.extend(render(pdf, TMP / pdf.stem))
contact = Image.new("RGB", (1200, 430 * 3), "#dce2e7")
d = ImageDraw.Draw(contact)
for i, file in enumerate([*sorted(OUT.glob("*.png")), *previews]):
    with Image.open(file) as im:
        tile = ImageOps.contain(im.convert("RGB"), (275, 385))
        x = (i % 4) * 300 + (300 - tile.width) // 2
        y = (i // 4) * 430 + 25
        contact.paste(tile, (x, y))
        d.text(((i % 4) * 300 + 8, (i // 4) * 430 + 7), file.stem[:34], fill="black")
contact.save(TMP / "contact-sheet.png")
print(json.dumps({"output": str(OUT), "upload_files": len(manifest), "pdf_count": 7, "image_count": 3, "policy_evidence_matches": True}, ensure_ascii=False))
