"""Local, evidence-preserving document understanding; proposals never authorize writes.

OCR supplies text, multilingual label/section extraction supplies candidate fields.
Ambiguous values are withheld. Personal/medical content is never sent to a provider.
"""
import re
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation

KINDS = ("OUTPATIENT", "INPATIENT", "ACCIDENT", "EVACUATION")
ALIASES = {
    "OUTPATIENT": r"outpatient|ngoai tru|门诊|門診",
    "INPATIENT": r"inpatient|noi tru|住院",
    "ACCIDENT": r"accident|tai nan|意外(?:伤害)?",
    "EVACUATION": r"evacuation|van chuyen y te|医疗转运|紧急救援转运",
}


def fold(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.lower().replace("đ", "d")) if not unicodedata.combining(c))


def lines(pages):
    for page in pages:
        rows = [" ".join(row.split()) for row in page["text"].splitlines() if row.strip()]
        for i, row in enumerate(rows):
            yield page["page"], row, rows[i + 1] if i + 1 < len(rows) else ""


def labelled(pages, pattern):
    """Handle inline labels and PDF table cells emitted on the next line."""
    candidates = []
    for page, row, following in lines(pages):
        matches = [m for m in re.finditer(r"(?<![a-z])(?:" + pattern + r")(?![a-z])", fold(row)) if m.start() == 0 or row[:m.start()].rstrip().endswith("/")]
        if not matches:
            continue
        match = matches[-1]
        # The normalized alphabet is used only to find a label; the evidence is original.
        tail = row[match.end():].strip(" :：=\t")
        if tail.startswith("/"):
            continue  # A second untranslated label is not a value.
        value = tail or following
        if not tail and re.match(r"^(?:premium|period|territory|insurer|policy name|保费|保险期间|地域|承保机构|应付日期)\s*(?:[:：/]|$)", fold(value)):
            continue
        if value:
            candidates.append({"raw": value, "page": page, "quote": row if tail else row + "\n" + following})
    return candidates


def decimal_value(raw, zero=True):
    raw = raw.strip().replace(" ", "")
    if not re.fullmatch(r"\d[\d,.]*", raw):
        return None
    if "," in raw and "." in raw:
        # Policy amounts use a full stop decimal and comma thousands separator.
        if not re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d{1,2}", raw): return None
        raw = raw.replace(",", "")
    elif "," in raw:
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", raw): raw = raw.replace(",", "")
        elif re.fullmatch(r"\d+,\d{1,2}", raw): raw = raw.replace(",", ".")
        else: return None
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", raw): return None
    try:
        value = Decimal(raw)
        if value < 0 or (not zero and value == 0) or value >= Decimal("1000000000000") or value != value.quantize(Decimal(".01")): return None
        return format(value, ".2f")
    except InvalidOperation:
        return None


def dates(raw):
    found = []
    for m in re.finditer(r"(?<!\d)(\d{4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})(?:日)?(?!\d)", raw):
        try: found.append(date(*map(int, m.groups())).isoformat())
        except ValueError: pass
    if not found:
        for m in re.finditer(r"(?<!\d)(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})(?!\d)", raw):
            try: found.append(date(int(m[3]), int(m[2]), int(m[1])).isoformat())
            except ValueError: pass
    return found


def currency(raw):
    text = fold(raw)
    codes = [code for code, pattern in (("CNY", r"\bcny\b|\brmb\b|人民币"), ("VND", r"\bvnd\b|\bvndong\b|viet nam dong"), ("USD", r"\busd\b"), ("EUR", r"\beur\b"), ("GBP", r"\bgbp\b")) if re.search(pattern, text)]
    return codes[0] if len(codes) == 1 else None


def unique(candidates, convert):
    good = []
    for item in candidates:
        value = convert(item["raw"])
        if value is not None and value != "": good.append({"value": value, "page": item["page"], "quote": item["quote"]})
    return good[0] if good and len({str(v["value"]) for v in good}) == 1 else None


def number(raw):
    if re.search(r"-\s*(?:(?:CNY|RMB|VND)\s*)?\d", raw, re.I): return None
    raw = re.sub(r"(?<=\d)\s*([,.])\s*(?=\d)", r"\1", raw)
    matches = re.findall(r"(?<![\d.])\d[\d,.]*(?![\d.])", raw)
    return decimal_value(matches[0]) if len(matches) == 1 else None


def document_type(pages):
    # Only headings, not references inside the narrative, classify a document.
    text = fold("\n".join(p["text"][:1000] for p in pages[:2]))
    patterns = (("CLAIM_FORM", r"(?m)^\s*(?:claim\s+form\b|(?:giay|don)\s+yeu\s+cau\s+boi\s+thuong|理赔申请)"),
                ("DISCHARGE", r"(?m)^\s*(?:出院记录|discharge summary|giay ra vien)"),
                ("COST_BREAKDOWN", r"(?m)^\s*(?:住院费用明细|itemized hospital costs|bang ke chi phi)"),
                ("ACCIDENT_REPORT", r"(?m)^\s*(?:意外事故说明|accident statement|bien ban tai nan)"),
                ("MEDICAL_RECORD", r"(?m)^\s*(?:门急诊病历|medical encounter record|benh an|ho so kham)"))
    for kind, pattern in patterns:
        if re.search(pattern, text): return kind
    if re.search(r"(?m)^\s*(?:total paid\s*:|paid test expense|已支付|da thanh toan)", text): return "PAID_MEDICAL_BILL"
    return "INVOICE_OR_NOTICE"


def policy_suggestions(pages):
    fields, evidence, warnings = {}, {}, []
    def put(key, values, convert=lambda s: s[:150] if len(s) <= 150 else None):
        item = unique(values, convert)
        if item and key in fields and fields[key] != item["value"]:
            fields.pop(key); evidence.pop(key); warnings.append("CONFLICTING_" + key.upper())
        elif item: fields[key] = item["value"]; evidence[key] = item
        elif values: warnings.append("AMBIGUOUS_OR_UNREADABLE_" + key.upper())
    put("name", labelled(pages, r"policy name|product name|ten hop dong|ten san pham|产品名称|保险名称|保单名称"))
    if "name" not in fields:
        titles = [{"raw": row, "page": p, "quote": row} for p, row, _ in lines(pages) if re.fullmatch(r"[^.;:]{0,80}(?:health plan|insurance schedule|insurance policy|保险合同|综合保险)(?:\s*/\s*[^.;:]{2,80})?", row, re.I)]
        put("name", titles)
    put("insurer", labelled(pages, r"test issuer|insurer|insurance company|don vi bao hiem|cong ty bao hiem|承保机构|保险公司"))
    premiums = labelled(pages, r"(?<!due )premium(?!\s*(?:due|date))|phi bao hiem|币种及保费|保费(?!到期)")
    put("premium", premiums, number)
    put("currency", premiums, lambda raw: currency(raw) if currency(raw) in ("CNY", "VND") else None)
    put("premium_due", labelled(pages, r"premium due|han dong phi|应付日期|缴费截止日期|保费到期日"), lambda raw: dates(raw)[0] if len(dates(raw)) == 1 else None)
    periods = labelled(pages, r"period|thoi han bao hiem|保险期间|保障期间")
    put("starts_on", periods, lambda raw: dates(raw)[0] if len(dates(raw)) == 2 and dates(raw)[0] <= dates(raw)[1] else None)
    put("ends_on", periods, lambda raw: dates(raw)[1] if len(dates(raw)) == 2 and dates(raw)[0] <= dates(raw)[1] else None)
    put("starts_on", labelled(pages, r"starts on|start date|ngay bat dau|生效日期"), lambda raw: dates(raw)[0] if len(dates(raw)) == 1 else None)
    put("ends_on", labelled(pages, r"ends on|end date|ngay ket thuc|终止日期"), lambda raw: dates(raw)[0] if len(dates(raw)) == 1 else None)
    if fields.get("starts_on") and fields.get("ends_on") and fields["ends_on"] < fields["starts_on"]:
        for key in ("starts_on", "ends_on"): fields.pop(key); evidence.pop(key)
        warnings.append("CONFLICTING_PERIOD")
    def territory(raw):
        text = fold(raw).strip()
        if re.search(r"worldwide|\bworld\b|toan cau|全球", text): return "WORLD"
        if re.search(r"\bcn\b|mainland china|trung quoc|中国大陆", text) and not re.search(r"\bvn\b|viet nam|越南", text): return "CN"
        if re.search(r"\bvn\b|viet nam|越南", text) and not re.search(r"\bcn\b|china|中国", text): return "VN"
        return None
    put("territory", labelled(pages, r"territory|pham vi lanh tho|地域|保障地域"), territory)
    benefits = []
    for kind in KINDS:
        benefit = dict(kind=kind, status="UNKNOWN", limit=None, deductible=None, reimbursement_percent=None, waiting_days=None, source_page=None, evidence_quote="")
        candidates = []
        for page, row, following in lines(pages):
            norm = fold(row)
            if not re.match(r"^(?:" + ALIASES[kind] + r")(?:\b|\s|[:：])", norm): continue
            quote = row
            if not re.search(r"included|excluded|bao gom|loai tru|承保|不保|包含|不包含", norm):
                quote = row + "\n" + following; norm = fold(quote)
            excluded = bool(re.search(r"\bexcluded\b|not included|khong bao gom|loai tru|不承保|不包含|不保", norm))
            included = bool(re.search(r"\bincluded\b|bao gom|承保|包含", norm))
            if not (excluded or included) or len(quote) > 1200: continue
            value = {**benefit, "status": "EXCLUDED" if excluded else "INCLUDED", "source_page": page, "evidence_quote": quote}
            if not excluded:
                for key, pattern in (("limit", r"(?:limit|han muc|保额|限额)\s*[:：]?\s*(?:CNY|RMB|VND|人民币)?\s*([\d,.]+)"), ("deductible", r"(?:deductible|khau tru|免赔额)\s*[:：]?\s*(?:CNY|RMB|VND|人民币)?\s*([\d,.]+)")):
                    matches = re.findall(pattern, fold(quote), re.I)
                    if len(set(matches)) == 1: value[key] = decimal_value(matches[0])
                if fields.get("currency") and currency(quote) and currency(quote) != fields["currency"]:
                    value["limit"] = value["deductible"] = None
                    warnings.append("BENEFIT_CURRENCY_MISMATCH_" + kind)
                for key, pattern, maximum in (("reimbursement_percent", r"(?:reimbursement|ty le chi tra|赔付比例|报销比例)\s*[:：]?\s*(\d{1,3})\s*%", 100), ("waiting_days", r"(?:waiting(?: period)?|thoi gian cho|等待期)\s*[:：]?\s*(\d{1,3})\s*(?:days?|ngay|天)", 365)):
                    matches = re.findall(pattern, fold(quote), re.I)
                    if len(set(matches)) == 1 and int(matches[0]) <= maximum: value[key] = int(matches[0])
            if not any({k: v for k, v in old.items() if k not in ("evidence_quote", "source_page")} == {k: v for k, v in value.items() if k not in ("evidence_quote", "source_page")} for old in candidates): candidates.append(value)
        if len(candidates) == 1: benefit = candidates[0]
        elif candidates: warnings.append("CONFLICTING_" + kind)
        benefits.append(benefit)
    required = ("name", "insurer", "currency", "premium", "premium_due", "starts_on", "ends_on", "territory")
    return {"fields": fields, "evidence": evidence, "benefits": benefits, "missing_fields": [k for k in required if k not in fields], "warnings": warnings, "method": "LOCAL_EVIDENCE_EXTRACTION_V1", "external_processing": False, "review_required": True}


def claim_suggestions(pages):
    fields, evidence = {}, {}
    patterns = {"amount": (r"amount requested|total paid|total|chi phi yeu cau|tong tien|申请金额|合计", number),
                "incident_date": (r"incident date|treatment dates|ngay xay ra|ngay kham|事故日期|就诊日期", lambda raw: dates(raw)[0] if dates(raw) else None),
                "policy_reference": (r"policy reference|policy no\.?|保单号", lambda raw: raw[:100]),
                "case_reference": (r"case reference|病例编号|案件编号|事件编号", lambda raw: raw[:100])}
    for key, (pattern, convert) in patterns.items():
        item = unique(labelled(pages, pattern), convert)
        if item: fields[key] = item["value"]; evidence[key] = item
    text = "\n".join(p["text"] for p in pages)
    code = currency(text)
    if code: fields["currency"] = code
    claim_type = unique(labelled(pages, r"claim type|loai ho so|类型"), lambda raw: "INPATIENT" if re.search(r"inpatient|noi tru|住院", fold(raw)) else "OUTPATIENT" if re.search(r"outpatient|ngoai tru|门诊", fold(raw)) else "ACCIDENT" if re.search(r"accident|tai nan|意外", fold(raw)) else None)
    if claim_type: fields["benefit_kind"] = claim_type["value"]; evidence["benefit_kind"] = claim_type
    return {"document_type": document_type(pages), "fields": fields, "evidence": evidence, "method": "LOCAL_EVIDENCE_EXTRACTION_V1", "external_processing": False, "review_required": True}
