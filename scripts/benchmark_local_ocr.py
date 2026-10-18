"""Small reproducible smoke set, not a production OCR accuracy benchmark."""
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.ocr import extract_file, suggestions

root = Path(__file__).resolve().parents[1]
font_path = Path("C:/Windows/Fonts/msyh.ttc")
if not font_path.exists():
    raise SystemExit("Provide a Chinese/Vietnamese-capable test font before running this optional benchmark")
font = ImageFont.truetype(str(font_path), 42)
cases = {
    "en": ("Invoice number: EN-OCR-2026\nIssuer: QA University\nBeneficiary: QA Insurance\nTotal due: CNY 800.00\nDue date: 2026-12-20", {"invoice_number": "EN-OCR-2026", "institution_name": "QA University", "beneficiary_name": "QA Insurance", "amount_cny": "800.00", "due_date": "2026-12-20"}),
    "vi": ("Mã hóa đơn: VI-OCR-2026\nĐơn vị phát hành: Đại học kiểm thử\nBên nhận: Bảo hiểm kiểm thử\nSố tiền: CNY 800.00\nHạn thanh toán: 20/12/2026", {"invoice_number": "VI-OCR-2026", "institution_name": "Đại học kiểm thử", "beneficiary_name": "Bảo hiểm kiểm thử", "amount_cny": "800.00", "due_date": "2026-12-20"}),
    "zh": ("发票号码：ZH-OCR-2026\n学校：测试大学\n收款单位：测试保险\n应付金额：CNY 800.00\n缴费截止日期：2026年12月20日", {"invoice_number": "ZH-OCR-2026", "institution_name": "测试大学", "beneficiary_name": "测试保险", "amount_cny": "800.00", "due_date": "2026-12-20"}),
}
output = {"fixture_provenance": "Self-authored clean printed images; not real invoices", "limitation": "Three synthetic samples do not establish production accuracy on photos, handwriting, complex layouts or all languages", "cases": {}}
folder = root / ".local/qa-documents"; folder.mkdir(parents=True, exist_ok=True)
for language, (text, expected) in cases.items():
    font = ImageFont.truetype(str(font_path if language == "zh" else Path("C:/Windows/Fonts/arial.ttf")), 42)
    image = Image.new("RGB", (1700, 850), "white")
    ImageDraw.Draw(image).multiline_text((75, 65), text, font=font, fill="black", spacing=35)
    path = folder / f"invoice-{language}.png"; image.save(path)
    started = time.monotonic(); pages, mime, method = extract_file(path.read_bytes(), path.name, language)
    fields = suggestions(pages)["fields"]
    checks = {key: fields.get(key, {}).get("value") == value for key, value in expected.items()}
    output["cases"][language] = {"method": method, "seconds": round(time.monotonic() - started, 2), "checks": checks, "matched_fields": sum(checks.values()), "total_fields": len(checks), "extracted": {key: value["value"] for key, value in fields.items()}}
    print(f"{language}: {sum(checks.values())}/{len(checks)} exact fields; {output['cases'][language]['seconds']}s")
(root / "submission/evidence/local-ocr-smoke.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
