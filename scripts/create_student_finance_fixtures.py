"""Self-authored English fixtures for real OCR testing, never actual fee documents."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root = Path(__file__).resolve().parents[1] / ".local" / "qa-documents"
root.mkdir(parents=True, exist_ok=True)
image = Image.new("RGB", (1700, 1100), "white")
draw = ImageDraw.Draw(image)
font = ImageFont.load_default(size=43)
text = "STUDENT FEE NOTICE\nInvoice number: STUDENT-OCR-2026\nIssuer: QA University\nBeneficiary: QA Education\nTotal due: CNY 800.00\nDue date: 2026-12-20\n\nSelf-authored software test fixture.\nNot an actual invoice or payment request."
draw.multiline_text((85, 65), text, font=font, fill="black", spacing=30)
image.save(root / "invoice-ocr.png")
image.save(root / "invoice-scanned.pdf", "PDF", resolution=150)
policy = Image.new("RGB", (1700, 850), "white")
draw = ImageDraw.Draw(policy)
draw.multiline_text((80, 60), "QA POLICY - SELF AUTHORED TEST TEXT\n\nClaims require hospital invoices and a claim form.\nExclusions: elective cosmetic treatment.\n\nThis is not a real insurance policy.", font=font, fill="black", spacing=32)
policy.save(root / "policy-scanned.pdf", "PDF", resolution=150)
print("Self-authored OCR fixtures created in .local/qa-documents")
