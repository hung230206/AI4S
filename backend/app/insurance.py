"""Topic C + D: cited portfolio, explicit coverage comparisons and claim preparation.

No underwriting, claim adjudication, insurer submission or movement of real funds.
All amounts use Decimal; account locks and request hashes protect repeat writes.
"""
import hashlib
import io
import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Literal
from uuid import UUID
from zipfile import ZipFile, ZIP_DEFLATED
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import Field, field_validator, model_validator
from sqlalchemy import select, func
from sqlalchemy.orm import defer
from .file_consent import require_file_consent
from .db import get_db
from .models import InsurancePolicy, InsuranceClaim, ClaimAttachment, FinancePlan, PolicyDocument, Invoice, now
from .schemas import Strict
from .security import student, lock_user, ApiError
from .services import audit, digest, iso
from .documents import own as own_document
from .finance import today, money, display, own_wallet, plan_out, wallet_out

router = APIRouter(prefix="/api/v1/insurance", tags=["Insurance portfolio and claim preparation"])
BenefitKind = Literal["OUTPATIENT", "INPATIENT", "ACCIDENT", "EVACUATION"]
NOTICE = "REVIEWED_USER_SUMMARY — not proof of issued cover, claim eligibility or insurer approval."
CLAIM_GUIDE = "https://www.lxbx.net/storage/website/20240402/Q420240402144639403992859232.pdf"
MONEY_PATTERN = r"^\d{1,12}(\.\d{1,2})?$"


class BenefitInput(Strict):
    kind: BenefitKind
    status: Literal["INCLUDED", "EXCLUDED", "UNKNOWN"]
    limit: str | None = Field(default=None, pattern=MONEY_PATTERN)
    deductible: str | None = Field(default=None, pattern=MONEY_PATTERN)
    reimbursement_percent: int | None = Field(default=None, ge=0, le=100, strict=True)
    waiting_days: int | None = Field(default=None, ge=0, le=365, strict=True)
    source_page: int | None = Field(default=None, ge=1, le=50, strict=True)
    evidence_quote: str = Field(default="", max_length=1200)


class PolicyInput(Strict):
    document_id: UUID
    name: str = Field(min_length=2, max_length=150)
    insurer: str = Field(min_length=2, max_length=150)
    currency: Literal["CNY", "VND"] = "CNY"
    premium: str = Field(pattern=MONEY_PATTERN)
    premium_due: date
    starts_on: date
    ends_on: date
    territory: Literal["CN", "VN", "WORLD"] = "CN"
    benefits: list[BenefitInput] = Field(min_length=1, max_length=4)
    notes: str = Field(default="", max_length=2000)
    reviewed: bool = Field(strict=True)
    request_key: str = Field(min_length=8, max_length=128)
    revision: int | None = Field(default=None, ge=1, strict=True)

    @field_validator("name", "insurer")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Required field is blank")
        return value.strip()

    @model_validator(mode="after")
    def dates_and_kinds(self):
        if self.ends_on < self.starts_on or len({b.kind for b in self.benefits}) != len(self.benefits):
            raise ValueError("Invalid dates or repeated benefit")
        return self


def own_policy(db, policy_id, user):
    obj = db.scalar(select(InsurancePolicy).where(InsurancePolicy.id == policy_id, InsurancePolicy.user_id == user.id))
    if not obj:
        raise ApiError("POLICY_NOT_FOUND", "Không tìm thấy hợp đồng trong tài khoản.", 404)
    return obj


def policy_out(policy, db):
    document = db.get(PolicyDocument, policy.document_id, options=[defer(PolicyDocument.original_bytes), defer(PolicyDocument.pages)])
    plan = db.get(FinancePlan, policy.finance_plan_id) if policy.finance_plan_id else None
    invoice = db.get(Invoice, policy.premium_invoice_id) if policy.premium_invoice_id else None
    return {"id": str(policy.id), "document_id": str(policy.document_id), "name": policy.name, "insurer": policy.insurer,
            "currency": policy.currency, "premium": display(policy.premium, policy.currency), "premium_due": str(policy.premium_due),
            "starts_on": str(policy.starts_on), "ends_on": str(policy.ends_on), "territory": policy.territory,
            "benefits": policy.benefits, "notes": policy.notes, "active": policy.active, "revision": policy.revision,
            "reviewed_at": iso(policy.reviewed_at), "document_kind": document.document_kind, "document_title": document.title,
            "document_sha256": document.sha256,
            "premium_invoice_id": str(policy.premium_invoice_id) if policy.premium_invoice_id else None, "finance_plan_id": str(policy.finance_plan_id) if policy.finance_plan_id else None,
            "plan_needs_review": bool(plan and (not plan.active or policy.plan_revision != policy.revision or plan.amount != policy.premium or plan.due_date != policy.premium_due)),
            "premium_estimate_needs_review": bool(invoice and (invoice.amount_cny != policy.premium or invoice.due_date != policy.premium_due or invoice.status != "OPEN")), "notice": NOTICE}


def reviewed_values(body, user, db):
    if not body.reviewed:
        raise ApiError("POLICY_REVIEW_REQUIRED", "Hãy đối chiếu với tài liệu gốc và xác nhận trước khi lưu.", 422)
    doc = own_document(db, body.document_id, user)
    benefits = []
    for benefit in body.benefits:
        value = benefit.model_dump()
        quote = " ".join(benefit.evidence_quote.split())
        if benefit.status != "UNKNOWN" or quote:
            page = next((p for p in doc.pages if p["page"] == benefit.source_page), None)
            if len(quote) < 12 or not page or quote not in " ".join(page["text"].split()):
                raise ApiError("POLICY_CITATION_INVALID", "Trích dẫn cần ít nhất 12 ký tự và khớp đúng trang tài liệu gốc.", 422)
        value["evidence_quote"] = quote
        for field in ("limit", "deductible"):
            if value[field] is not None:
                value[field] = display(money(value[field], body.currency, False), body.currency)
        if benefit.status != "INCLUDED" and any(value[k] is not None for k in ("limit", "deductible", "reimbursement_percent", "waiting_days")):
            raise ApiError("POLICY_BENEFIT_INVALID", "Quyền lợi chưa rõ hoặc loại trừ phải để trống các thông số tính toán.", 422)
        benefits.append(value)
    return {**body.model_dump(exclude={"request_key", "revision", "reviewed", "benefits", "premium"}),
            "premium": money(body.premium, body.currency, False), "benefits": benefits}


def repeat(db, cls, user, key, payload):
    previous = db.scalar(select(cls).where(cls.user_id == user.id, cls.request_key == key))
    if previous and previous.request_hash != digest(payload):
        raise ApiError("IDEMPOTENCY_CONFLICT", "Mã yêu cầu đã dùng cho nội dung khác.", 409)
    return previous


@router.get("/policies")
def policies(user=Depends(student), db=Depends(get_db, scope="function")):
    return {"items": [policy_out(p, db) for p in db.scalars(select(InsurancePolicy).where(InsurancePolicy.user_id == user.id).order_by(InsurancePolicy.created_at.desc()))]}


@router.post("/policies")
def create_policy(body: PolicyInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    payload = body.model_dump(mode="json")
    old = repeat(db, InsurancePolicy, user, body.request_key, payload)
    if old:
        return policy_out(old, db)
    values = reviewed_values(body, user, db)
    if db.scalar(select(func.count()).select_from(InsurancePolicy).where(InsurancePolicy.user_id == user.id)) >= 40:
        raise ApiError("POLICY_LIMIT", "Tối đa 40 hợp đồng trong tài khoản.", 409)
    policy = InsurancePolicy(user_id=user.id, request_key=body.request_key, request_hash=digest(payload), **values)
    db.add(policy); db.flush()
    audit(db, user, "INSURANCE_POLICY_HUMAN_REVIEWED", policy_id=str(policy.id), document_id=str(policy.document_id))
    return policy_out(policy, db)


@router.post("/policies/{policy_id}/update")
def update_policy(policy_id: UUID, body: PolicyInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    policy = own_policy(db, policy_id, user)
    if body.revision != policy.revision:
        raise ApiError("STALE_REVISION", "Dữ liệu đã thay đổi. Tải lại trước khi sửa.", 409)
    values = reviewed_values(body, user, db)
    for key, value in values.items():
        setattr(policy, key, value)
    policy.revision += 1
    policy.reviewed_at = now()
    audit(db, user, "INSURANCE_POLICY_UPDATED", policy_id=str(policy.id), revision=policy.revision)
    return policy_out(policy, db)


class RevisionInput(Strict):
    revision: int = Field(ge=1, strict=True)


@router.post("/policies/{policy_id}/archive")
def archive_policy(policy_id: UUID, body: RevisionInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    policy = own_policy(db, policy_id, user)
    if policy.revision != body.revision:
        raise ApiError("STALE_REVISION", "Tải lại phiên bản hợp đồng mới nhất.", 409)
    policy.active = False; policy.revision += 1
    audit(db, user, "INSURANCE_POLICY_ARCHIVED", policy_id=str(policy.id))
    return policy_out(policy, db)


@router.post("/policies/{policy_id}/restore")
def restore_policy(policy_id: UUID, body: RevisionInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    policy = own_policy(db, policy_id, user)
    if policy.revision != body.revision: raise ApiError("STALE_REVISION", "Tải lại phiên bản hợp đồng mới nhất.", 409)
    policy.active = True; policy.revision += 1
    audit(db, user, "INSURANCE_POLICY_RESTORED", policy_id=str(policy.id))
    return policy_out(policy, db)


class PremiumPlanInput(RevisionInput):
    wallet_id: UUID
    reviewed: bool = Field(strict=True)


class PremiumInvoiceInput(RevisionInput):
    reviewed: bool = Field(strict=True)


@router.post("/policies/{policy_id}/premium-invoice")
def premium_invoice(policy_id: UUID, body: PremiumInvoiceInput, user=Depends(student), db=Depends(get_db, scope="function")):
    from .services import serialize
    lock_user(db, user)
    policy = own_policy(db, policy_id, user)
    if not body.reviewed or body.revision != policy.revision or not policy.active:
        raise ApiError("POLICY_REVIEW_REQUIRED", "Cần đối chiếu phiên bản hợp đồng hiện tại.", 409)
    if policy.currency != "CNY" or policy.premium <= 0:
        raise ApiError("POLICY_INVOICE_INVALID", "Luồng thanh toán thử hiện hỗ trợ khoản phí CNY lớn hơn 0.", 422)
    number = "POLICY-" + policy.id.hex
    invoice = db.get(Invoice, policy.premium_invoice_id) if policy.premium_invoice_id else None
    if invoice:
        return {"invoice": serialize(invoice), "reused": True, "notice": "USER-CREATED PREMIUM ESTIMATE — NOT AN INSURER-ISSUED INVOICE"}
    invoice = Invoice(student_id=user.id, invoice_number=number, institution_name=policy.insurer,
                      beneficiary_name=policy.insurer, fee_type="ANNUAL_HEALTH_INSURANCE_PREMIUM", amount_cny=policy.premium,
                      due_date=policy.premium_due, source_type="USER_ENTERED", is_real_beneficiary=False,
                      notes=f"USER-CREATED PREMIUM ESTIMATE — NOT AN INSURER-ISSUED INVOICE. Reviewed policy {policy.id}, revision {policy.revision}. Sandbox only.")
    db.add(invoice); db.flush(); db.refresh(invoice)
    policy.premium_invoice_id = invoice.id
    if policy.finance_plan_id and policy.plan_revision == policy.revision:
        existing_plan = db.get(FinancePlan, policy.finance_plan_id)
        if existing_plan.amount == invoice.amount_cny and existing_plan.due_date == invoice.due_date:
            existing_plan.invoice_id = invoice.id
    audit(db, user, "POLICY_PREMIUM_ESTIMATE_CREATED", policy_id=str(policy.id), invoice_id=str(invoice.id))
    return {"invoice": serialize(invoice), "reused": False, "notice": "USER-CREATED PREMIUM ESTIMATE — NOT AN INSURER-ISSUED INVOICE"}


@router.post("/policies/{policy_id}/plan")
def premium_plan(policy_id: UUID, body: PremiumPlanInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    policy = own_policy(db, policy_id, user)
    wallet = own_wallet(db, body.wallet_id, user)
    if not body.reviewed or policy.revision != body.revision or not policy.active:
        raise ApiError("POLICY_REVIEW_REQUIRED", "Kiểm tra phiên bản hợp đồng đang hoạt động trước khi lập kế hoạch.", 409)
    if policy.finance_plan_id:
        plan = db.get(FinancePlan, policy.finance_plan_id)
        if plan.wallet_id != wallet.id:
            raise ApiError("PLAN_ALREADY_EXISTS", "Phí này đã có kế hoạch ở một sổ khác.", 409)
        # Keep an existing financial snapshot intact. A changed policy is highlighted for review.
        return {"plan": plan_out(plan, wallet), "wallet": wallet_out(db, wallet), "reused": True, "needs_review": policy.plan_revision != policy.revision}
    if wallet.currency != policy.currency or wallet.opening_date > policy.premium_due or policy.premium <= 0:
        raise ApiError("POLICY_PLAN_INVALID", "Chọn sổ cùng tiền tệ, mở trước hạn phí; phí phải lớn hơn 0.", 422)
    existing_plan = db.scalar(select(FinancePlan).where(FinancePlan.invoice_id == policy.premium_invoice_id)) if policy.premium_invoice_id else None
    if existing_plan:
        if existing_plan.wallet_id != wallet.id or not existing_plan.active:
            raise ApiError("PLAN_ALREADY_EXISTS", "Khoản phí đã có kế hoạch ở sổ khác hoặc đã dừng; kiểm tra trong Ngân sách.", 409)
        policy.finance_plan_id = existing_plan.id; policy.plan_revision = policy.revision
        return {"plan": plan_out(existing_plan, wallet), "wallet": wallet_out(db, wallet), "reused": True, "needs_review": existing_plan.amount != policy.premium or existing_plan.due_date != policy.premium_due}
    plan = FinancePlan(user_id=user.id, wallet_id=wallet.id, title=policy.name + " · premium", kind="EXPENSE", amount=policy.premium,
                       category="INSURANCE", due_date=policy.premium_due, recurrence="NONE", invoice_id=policy.premium_invoice_id)
    db.add(plan); db.flush()
    policy.finance_plan_id = plan.id; policy.plan_revision = policy.revision
    audit(db, user, "INSURANCE_PREMIUM_PLANNED", policy_id=str(policy.id), plan_id=str(plan.id))
    return {"plan": plan_out(plan, wallet), "wallet": wallet_out(db, wallet), "reused": False, "needs_review": False}


class NeedInput(Strict):
    kind: BenefitKind
    minimum_limit: str = Field(pattern=MONEY_PATTERN)


class AnalysisInput(Strict):
    starts_on: date
    ends_on: date
    country: Literal["CN", "VN"] = "CN"
    currency: Literal["CNY", "VND"] = "CNY"
    needs: list[NeedInput] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def valid_period(self):
        if self.ends_on < self.starts_on or len({n.kind for n in self.needs}) != len(self.needs):
            raise ValueError("Invalid period or repeated need")
        return self


@router.post("/analysis")
def analysis(body: AnalysisInput, user=Depends(student), db=Depends(get_db, scope="function")):
    rows = list(db.scalars(select(InsurancePolicy).where(InsurancePolicy.user_id == user.id, InsurancePolicy.active == True)))
    results = []
    for need in body.needs:
        required = money(need.minimum_limit, body.currency, False)
        candidates = []
        for policy in rows:
            benefit = next((b for b in policy.benefits if b["kind"] == need.kind), None)
            reasons = []
            if policy.currency != body.currency: reasons.append("CURRENCY_MISMATCH")
            if policy.territory not in (body.country, "WORLD"): reasons.append("TERRITORY_MISMATCH")
            if policy.starts_on > body.starts_on or policy.ends_on < body.ends_on: reasons.append("PERIOD_GAP")
            if not benefit or benefit["status"] == "UNKNOWN": reasons.append("UNKNOWN_BENEFIT")
            elif benefit["status"] == "EXCLUDED": reasons.append("EXCLUDED_IN_SUMMARY")
            else:
                if benefit["limit"] is None: reasons.append("UNKNOWN_LIMIT")
                elif Decimal(benefit["limit"]) < required: reasons.append("LIMIT_GAP")
                if benefit["waiting_days"] is None: reasons.append("UNKNOWN_WAITING_PERIOD")
                elif policy.starts_on + timedelta(days=benefit["waiting_days"]) > body.starts_on: reasons.append("WAITING_PERIOD")
            candidates.append({"policy_id": str(policy.id), "name": policy.name, "revision": policy.revision,
                               "reasons": reasons, "benefit": benefit, "document_id": str(policy.document_id),
                               "document_kind": db.get(PolicyDocument, policy.document_id).document_kind})
        suitable = [p for p in candidates if not p["reasons"]]
        unknown = any(any(reason.startswith("UNKNOWN") or reason == "CURRENCY_MISMATCH" for reason in p["reasons"]) for p in candidates)
        status = "MEETS_ENTERED_REQUIREMENT" if suitable else "NEEDS_INFORMATION" if unknown else "GAP_IN_ENTERED_PORTFOLIO"
        results.append({"kind": need.kind, "minimum_limit": display(required, body.currency), "status": status,
                        "matching_policy_count": len(suitable), "possible_overlap": len(suitable) > 1, "policies": candidates})
    return {"as_of": str(today()), "requirements": body.model_dump(mode="json"), "results": results,
            "method": "EXPLICIT_REQUIREMENT_COMPARISON_V1", "notice": NOTICE,
            "limitations": ["Limits across policies are never added; coordination and exclusions need insurer review.",
                            "A matching summary is not a guarantee. Conditions, sublimits and prior claims are not adjudicated."]}


class ClaimInput(Strict):
    policy_id: UUID
    title: str = Field(min_length=2, max_length=150)
    benefit_kind: BenefitKind
    incident_date: date
    amount: str = Field(pattern=MONEY_PATTERN)
    description: str = Field(default="", max_length=2000)
    deadline: date | None = None
    request_key: str = Field(min_length=8, max_length=128)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 2: raise ValueError("Title cannot be blank")
        return value.strip()


def own_claim(db, claim_id, user):
    obj = db.scalar(select(InsuranceClaim).where(InsuranceClaim.id == claim_id, InsuranceClaim.user_id == user.id))
    if not obj: raise ApiError("CLAIM_NOT_FOUND", "Không tìm thấy hồ sơ trong tài khoản.", 404)
    return obj


def checklist_items(claim):
    codes = ["INVOICE", "MEDICAL_RECORD", "CLAIM_FORM", "IDENTITY_OFFLINE", "BANK_DETAILS_OFFLINE"]
    if claim.benefit_kind == "INPATIENT": codes += ["DISCHARGE", "COST_BREAKDOWN"]
    if claim.benefit_kind == "ACCIDENT": codes += ["ACCIDENT_REPORT"]
    return codes


def attachments(db, claim):
    return list(db.scalars(select(ClaimAttachment).options(defer(ClaimAttachment.original_bytes)).where(ClaimAttachment.claim_id == claim.id).order_by(ClaimAttachment.created_at)))


def attachment_out(item):
    return {"id": str(item.id), "item_code": item.item_code, "filename": item.filename,
            "byte_size": item.byte_size, "sha256": item.sha256, "created_at": iso(item.created_at)}


def claim_out(claim, db):
    files = attachments(db, claim)
    checklist = [{"code": code, "prepared_externally": bool(claim.checklist.get(code, False)),
                  "complete": bool(claim.checklist.get(code, False) or any(f.item_code == code for f in files)),
                  "attachment_count": sum(f.item_code == code for f in files), "offline_only": code.endswith("_OFFLINE")}
                 for code in checklist_items(claim)]
    snapshot = claim.policy_snapshot
    warnings = []
    if not snapshot["starts_on"] <= str(claim.incident_date) <= snapshot["ends_on"]: warnings.append("INCIDENT_OUTSIDE_ENTERED_PERIOD")
    benefit = next((b for b in snapshot["benefits"] if b["kind"] == claim.benefit_kind), None)
    if not benefit or benefit["status"] != "INCLUDED": warnings.append("BENEFIT_NEEDS_INSURER_REVIEW")
    if claim.deadline and claim.deadline < today() and claim.status in ("DRAFT", "READY"): warnings.append("ENTERED_DEADLINE_PASSED")
    return {"id": str(claim.id), "policy_id": str(claim.policy_id), "title": claim.title, "benefit_kind": claim.benefit_kind,
            "incident_date": str(claim.incident_date), "amount": display(claim.amount, claim.currency), "currency": claim.currency,
            "description": claim.description, "deadline": str(claim.deadline) if claim.deadline else None,
            "status": claim.status, "revision": claim.revision, "policy_snapshot": snapshot, "checklist": checklist,
            "ready": all(item["complete"] for item in checklist), "attachments": [attachment_out(f) for f in files],
            "history": claim.history, "warnings": warnings, "guide_url": CLAIM_GUIDE,
            "notice": "PREPARATION ONLY — nothing is submitted to an insurer; status is user-reported. Checklist is a general guide, not your insurer's definitive requirements."}


def journal(claim, action, **facts):
    if len(claim.history) >= 200:
        raise ApiError("CLAIM_HISTORY_LIMIT", "Hồ sơ đã đạt giới hạn 200 thay đổi.", 409)
    claim.history = [*claim.history, {"at": iso(now()), "action": action, **facts}]
    claim.revision += 1


def mutable(claim):
    if claim.status not in ("DRAFT", "READY"):
        raise ApiError("CLAIM_LOCKED", "Hồ sơ đã ghi nhận gửi ngoài ứng dụng; xuất bản hiện tại để đối chiếu.", 409)


@router.get("/claims")
def claims(user=Depends(student), db=Depends(get_db, scope="function")):
    return {"items": [claim_out(c, db) for c in db.scalars(select(InsuranceClaim).where(InsuranceClaim.user_id == user.id).order_by(InsuranceClaim.created_at.desc()).limit(100))]}


@router.post("/claims")
def create_claim(body: ClaimInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    payload = body.model_dump(mode="json")
    old = repeat(db, InsuranceClaim, user, body.request_key, payload)
    if old: return claim_out(old, db)
    policy = own_policy(db, body.policy_id, user)
    if not policy.active or body.incident_date > today() or (body.deadline and body.deadline < body.incident_date):
        raise ApiError("CLAIM_INPUT_INVALID", "Chọn hợp đồng đang hoạt động, ngày sự kiện không ở tương lai và hạn hồ sơ không trước sự kiện.", 422)
    if db.scalar(select(func.count()).select_from(InsuranceClaim).where(InsuranceClaim.user_id == user.id)) >= 100:
        raise ApiError("CLAIM_LIMIT", "Tối đa 100 hồ sơ trong tài khoản.", 409)
    claim = InsuranceClaim(user_id=user.id, currency=policy.currency, policy_snapshot=policy_out(policy, db),
                           request_hash=digest(payload), **body.model_dump(exclude={"amount"}), amount=money(body.amount, policy.currency))
    db.add(claim); db.flush()
    claim.history = [{"at": iso(now()), "action": "CREATED", "policy_revision": policy.revision}]
    audit(db, user, "CLAIM_PREPARATION_CREATED", claim_id=str(claim.id))
    return claim_out(claim, db)


@router.get("/claims/{claim_id}")
def claim_detail(claim_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    return claim_out(own_claim(db, claim_id, user), db)


class ChecklistInput(RevisionInput):
    code: str = Field(min_length=2, max_length=40)
    prepared_externally: bool = Field(strict=True)


class ClaimEditInput(RevisionInput):
    title: str = Field(min_length=2, max_length=150)
    incident_date: date
    amount: str = Field(pattern=MONEY_PATTERN)
    description: str = Field(default="", max_length=2000)
    deadline: date | None = None


@router.post("/claims/{claim_id}/update")
def update_claim(claim_id: UUID, body: ClaimEditInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    claim = own_claim(db, claim_id, user); mutable(claim)
    if claim.revision != body.revision: raise ApiError("STALE_REVISION", "Hồ sơ đã thay đổi; hãy tải lại.", 409)
    if len(body.title.strip()) < 2 or body.incident_date > today() or (body.deadline and body.deadline < body.incident_date):
        raise ApiError("CLAIM_INPUT_INVALID", "Kiểm tra tên, ngày sự kiện và hạn hồ sơ.", 422)
    claim.title = body.title.strip(); claim.amount = money(body.amount, claim.currency)
    claim.incident_date = body.incident_date; claim.deadline = body.deadline; claim.description = body.description
    claim.status = "DRAFT"; journal(claim, "DETAILS_UPDATED")
    return claim_out(claim, db)


@router.post("/claims/{claim_id}/checklist")
def update_checklist(claim_id: UUID, body: ChecklistInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    claim = own_claim(db, claim_id, user); mutable(claim)
    if claim.revision != body.revision: raise ApiError("STALE_REVISION", "Hồ sơ đã thay đổi; hãy tải lại.", 409)
    if body.code not in checklist_items(claim): raise ApiError("CHECKLIST_INVALID", "Mục hồ sơ không hợp lệ.", 422)
    claim.checklist = {**claim.checklist, body.code: body.prepared_externally}
    claim.status = "DRAFT"
    journal(claim, "CHECKLIST_UPDATED", code=body.code, prepared_externally=body.prepared_externally)
    return claim_out(claim, db)


class TransitionInput(RevisionInput):
    status: Literal["READY", "DRAFT", "SUBMITTED_EXTERNALLY", "CLOSED"]
    confirmed: bool = Field(strict=True)
    note: str = Field(default="", max_length=500)


@router.post("/claims/{claim_id}/transition")
def transition(claim_id: UUID, body: TransitionInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    claim = own_claim(db, claim_id, user)
    if claim.revision != body.revision: raise ApiError("STALE_REVISION", "Hồ sơ đã thay đổi; hãy tải lại.", 409)
    allowed = {"DRAFT": {"READY"}, "READY": {"DRAFT", "SUBMITTED_EXTERNALLY"}, "SUBMITTED_EXTERNALLY": {"CLOSED"}, "CLOSED": set()}
    if not body.confirmed or body.status not in allowed[claim.status]:
        raise ApiError("CLAIM_STATE_INVALID", "Cần xác nhận rõ bước tiếp theo từ trạng thái hiện tại.", 409)
    if body.status == "READY" and not claim_out(claim, db)["ready"]:
        raise ApiError("CLAIM_INCOMPLETE", "Chưa đủ các mục trong checklist.", 422)
    if body.status == "SUBMITTED_EXTERNALLY" and not body.note.strip():
        raise ApiError("CLAIM_REFERENCE_REQUIRED", "Ghi lại ngày/kênh hoặc mã tiếp nhận đã gửi ngoài ứng dụng.", 422)
    previous = claim.status; claim.status = body.status
    journal(claim, "STATUS_USER_REPORTED", previous=previous, status=body.status, note=body.note.strip())
    audit(db, user, "CLAIM_STATUS_USER_REPORTED", claim_id=str(claim.id), status=claim.status)
    return claim_out(claim, db)


@router.post("/claims/{claim_id}/attachments")
def upload_attachment(claim_id: UUID, file: UploadFile = File(...), item_code: str = Form(...),
                      revision: int = Form(...), file_consent=Depends(require_file_consent("claim-attachments")), user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    claim = own_claim(db, claim_id, user); mutable(claim)
    if claim.revision != revision: raise ApiError("STALE_REVISION", "Hồ sơ đã thay đổi; hãy tải lại.", 409)
    if item_code not in checklist_items(claim) or item_code.endswith("_OFFLINE"):
        raise ApiError("ATTACHMENT_CATEGORY_INVALID", "Chỉ đính kèm chứng từ mẫu; giấy tờ định danh và tài khoản giữ ngoài ứng dụng.", 422)
    raw = file.file.read(5 * 1024 * 1024 + 1)
    if not raw or len(raw) > 5 * 1024 * 1024: raise ApiError("DOCUMENT_TOO_LARGE", "Tệp cần từ 1 byte đến 5 MB.", 413)
    name = PurePosixPath((file.filename or "").replace("\\", "/")).name
    name = "".join(c for c in name if ord(c) >= 32)[:180]
    suffix = name.rsplit(".", 1)[-1].lower()
    mime = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "txt": "text/plain; charset=utf-8"}.get(suffix)
    valid = ((suffix == "pdf" and raw.startswith(b"%PDF-")) or (suffix == "png" and raw.startswith(b"\x89PNG\r\n\x1a\n")) or
             (suffix in ("jpg", "jpeg") and raw.startswith(b"\xff\xd8\xff")) or suffix == "txt")
    if not mime or not valid: raise ApiError("DOCUMENT_TYPE_UNSUPPORTED", "Chứng từ cần PDF, PNG, JPG hoặc TXT hợp lệ.", 422)
    if suffix == "txt":
        try: raw.decode("utf-8-sig")
        except UnicodeDecodeError: raise ApiError("DOCUMENT_INVALID", "TXT cần mã hóa UTF-8.", 422)
    files = attachments(db, claim)
    sha = hashlib.sha256(raw).hexdigest()
    old = next((f for f in files if f.sha256 == sha), None)
    if old:
        if old.item_code != item_code: raise ApiError("ATTACHMENT_DUPLICATE", "Tệp này đã đính kèm ở mục khác.", 409)
        return claim_out(claim, db)
    if len(files) >= 8 or sum(f.byte_size for f in files) + len(raw) > 20 * 1024 * 1024:
        raise ApiError("ATTACHMENT_LIMIT", "Tối đa 8 tệp, tổng 20 MB mỗi hồ sơ.", 409)
    item = ClaimAttachment(user_id=user.id, claim_id=claim.id, item_code=item_code, filename=name,
                           content_type=mime, byte_size=len(raw), sha256=sha, original_bytes=raw)
    db.add(item); db.flush(); claim.status = "DRAFT"
    journal(claim, "ATTACHMENT_ADDED", attachment_id=str(item.id), sha256=sha, item_code=item_code, processing_consent=file_consent)
    return claim_out(claim, db)


@router.get("/claims/{claim_id}/attachments/{attachment_id}")
def download_attachment(claim_id: UUID, attachment_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    claim = own_claim(db, claim_id, user)
    item = db.scalar(select(ClaimAttachment).where(ClaimAttachment.id == attachment_id, ClaimAttachment.claim_id == claim.id, ClaimAttachment.user_id == user.id))
    if not item: raise ApiError("ATTACHMENT_NOT_FOUND", "Không tìm thấy chứng từ.", 404)
    return Response(item.original_bytes, media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="attachment-{item.id}.{item.filename.rsplit(".", 1)[-1]}"'})


@router.post("/claims/{claim_id}/attachments/{attachment_id}/remove")
def remove_attachment(claim_id: UUID, attachment_id: UUID, body: RevisionInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    claim = own_claim(db, claim_id, user); mutable(claim)
    if body.revision != claim.revision: raise ApiError("STALE_REVISION", "Hồ sơ đã thay đổi; hãy tải lại.", 409)
    item = db.scalar(select(ClaimAttachment).where(ClaimAttachment.id == attachment_id, ClaimAttachment.claim_id == claim.id, ClaimAttachment.user_id == user.id))
    if not item: raise ApiError("ATTACHMENT_NOT_FOUND", "Không tìm thấy chứng từ.", 404)
    journal(claim, "ATTACHMENT_REMOVED", attachment_id=str(item.id), sha256=item.sha256)
    db.delete(item); db.flush(); claim.status = "DRAFT"
    return claim_out(claim, db)


@router.get("/claims/{claim_id}/export")
def export_claim(claim_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    # Serialize against edits/removals so metadata and original bytes describe one case version.
    lock_user(db, user)
    claim = own_claim(db, claim_id, user)
    report = claim_out(claim, db)
    source = own_document(db, UUID(claim.policy_snapshot["document_id"]), user)
    report["source_document"] = {"id": str(source.id), "filename": source.filename, "sha256": source.sha256, "byte_size": source.byte_size}
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("claim-preparation.json", json.dumps(report, ensure_ascii=False, indent=2))
        archive.writestr("README.txt", "PREPARATION ONLY — NOT SUBMITTED TO AN INSURER\nUser-reported status; no insurer approval or payout.\nOriginal policy and attachment hashes are included for review.\nIdentity and banking details must be prepared outside Demo.\nGeneral checklist source: " + CLAIM_GUIDE)
        archive.writestr("policy-original/" + source.filename, source.original_bytes)
        for item in attachments(db, claim):
            archive.writestr("attachments/" + str(item.id) + "-" + item.filename, item.original_bytes)
    return Response(stream.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="claim-preparation-{claim.id}.zip"'})


@router.get("/overview")
def overview(user=Depends(student), db=Depends(get_db, scope="function")):
    rows = list(db.scalars(select(InsurancePolicy).where(InsurancePolicy.user_id == user.id, InsurancePolicy.active == True)))
    reminders = []
    for p in rows:
        if p.ends_on < today(): reminders.append({"kind": "EXPIRED", "title": p.name, "date": str(p.ends_on), "href": "/insurance"})
        elif p.ends_on <= today() + timedelta(days=30): reminders.append({"kind": "EXPIRING", "title": p.name, "date": str(p.ends_on), "href": "/insurance"})
        if p.premium > 0 and p.premium_due <= today() + timedelta(days=30) and not p.finance_plan_id:
            reminders.append({"kind": "PREMIUM_UNPLANNED", "title": p.name, "date": str(p.premium_due), "href": "/insurance"})
        if p.finance_plan_id and p.plan_revision != p.revision:
            reminders.append({"kind": "PLAN_SNAPSHOT_CHANGED", "title": p.name, "date": str(p.premium_due), "href": "/finance"})
    for claim in db.scalars(select(InsuranceClaim).where(InsuranceClaim.user_id == user.id, InsuranceClaim.status.in_(["DRAFT", "READY"]))):
        if claim.deadline and claim.deadline <= today() + timedelta(days=14):
            reminders.append({"kind": "CLAIM_DEADLINE", "title": claim.title, "date": str(claim.deadline), "href": f"/insurance/claims/{claim.id}"})
    return {"as_of": str(today()), "active_policies": len(rows), "reminders": sorted(reminders, key=lambda x: x["date"]),
            "notice": "Dates are user-entered; reminders are calculated when the screen is opened. No background emails or insurer notifications."}


@router.get("/sample-pack")
def sample_pack(user=Depends(student)):
    """Self-authored data, with dates relative to today so the A-Z route stays testable."""
    start = today() - timedelta(days=30)
    end = today() + timedelta(days=335)
    due = today() + timedelta(days=7)
    clauses = [
        "OUTPATIENT: Included. Limit 2000 CNY per policy year; deductible 100 CNY; reimbursement 80%; waiting 0 days. Other exclusions may apply.",
        "INPATIENT: Included. Limit 100000 CNY per policy year; deductible 500 CNY; reimbursement 90%; waiting 30 days. Other exclusions may apply.",
        "ACCIDENT: Included. Limit 10000 CNY per policy year; deductible 0 CNY; reimbursement 100%; waiting 0 days. Other exclusions may apply.",
        "EVACUATION: Excluded. Emergency evacuation is not included in this fictional test policy."]
    policy_text = "SELF-AUTHORED TEST FIXTURE — NOT AN ISSUED INSURANCE POLICY\nDemo student health plan\nInsurer: Demo Test Insurer (fictional)\nPremium: 800 CNY\nPremium due: " + str(due) + "\nPeriod: " + str(start) + " to " + str(end) + "\nTerritory: CN\n\n" + "\n\n".join(clauses) + "\n\nClaims: keep hospital invoice, medical records and claim form. Additional documents depend on the actual insurer. No real claims accepted.\n"
    benefits = [{"kind": kind, "status": "EXCLUDED" if kind == "EVACUATION" else "INCLUDED", "limit": limit,
                 "deductible": deductible, "reimbursement_percent": percent, "waiting_days": wait,
                 "source_page": 1, "evidence_quote": quote}
                for kind, limit, deductible, percent, wait, quote in zip(
                    ("OUTPATIENT", "INPATIENT", "ACCIDENT", "EVACUATION"), ("2000", "100000", "10000", None),
                    ("100", "500", "0", None), (80, 90, 100, None), (0, 30, 0, None), clauses)]
    fields = {"name": "Demo student health plan", "insurer": "Demo Test Insurer (fictional)", "currency": "CNY", "premium": "800.00", "premium_due": str(due), "starts_on": str(start), "ends_on": str(end), "territory": "CN", "notes": "SELF-AUTHORED TEST FIXTURE", "benefits": benefits}
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("demo-policy.txt", policy_text)
        archive.writestr("review-fields.json", json.dumps(fields, ensure_ascii=False, indent=2))
        for code in ("invoice", "medical-record", "claim-form", "discharge", "cost-breakdown", "accident-report"):
            archive.writestr("claim-" + code + ".txt", "SELF-AUTHORED TEST FIXTURE — NOT A REAL MEDICAL OR INSURANCE RECORD\nDocument: " + code + "\nDate: " + str(today()) + "\nTest expense: 500.00 CNY\nFictional person: Sample Student\nNo real identifying, health or banking information.\n")
        archive.writestr("README.txt", "Start at /insurance. Upload demo-policy.txt as TEST_FIXTURE. Import review-fields.json into the editable review form, verify the source and confirm. Create a CNY wallet with 1000 CNY, then plan the 800 CNY premium. Analyze evacuation and outpatient needs. Create an outpatient claim for 500 CNY, attach the three matching claim files, confirm offline identity/bank readiness, mark ready and export. External submission is a self-reported status only.\nAll files are fictional; nothing is issued, paid or submitted. Dates are generated at download time.")
    return Response(stream.getvalue(), media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="demo-insurance-cd-samples.zip"'})
