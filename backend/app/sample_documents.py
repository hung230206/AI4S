"""Team-authored, non-personal documents for the public demo pack."""
import io
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image, ImageDraw, ImageFont


def china_sample_pack():
    from .config import ROOT
    folder = ROOT / "fixtures/china_upload_samples"
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for path in sorted(folder.iterdir()):
            if path.is_file(): archive.writestr(path.name, path.read_bytes())
    return stream.getvalue()


def claim_form_image():
    image = Image.new("RGB", (1200, 1696), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 40), "CLAIM FORM - FICTIONAL QA", font=ImageFont.load_default(size=36), fill="black")
    font = ImageFont.load_default(size=25)
    sections = [
        ("A. Test information", "Fictional insured person: Sample Student\nPolicy number: QA-CLAIM-2026\nSelf-authored software test only."),
        ("B. Reimbursement request", "Total amount claimed: VND 722.600\nNo bank details or actual medical information.\nThis is not an invoice to pay in CNY."),
        ("C. Supporting documents", "Keep hospital invoices and medical records.\nCheck dates, policy and currency before proceeding.\nThis checklist does not grant insurance benefits."),
        ("D. Review", "Read the original terms and verify all fields.\nDocuments are private to the test account.\nNo insurer submission or actual payout occurs."),
    ]
    for index, (heading, content) in enumerate(sections):
        top = 180 + index * 320
        draw.rectangle((60, top, 1140, top + 260), outline="black", width=2)
        draw.text((80, top + 20), heading, font=font, fill="blue")
        draw.multiline_text((80, top + 80), content, font=font, fill="black", spacing=18)
    draw.text((70, 1570), "SELF-AUTHORED TEST FIXTURE - NO REAL PERSON", font=font, fill="black")
    output = io.BytesIO(); image.save(output, format="PNG"); image.close()
    return output.getvalue()
