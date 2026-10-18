from datetime import date
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import Field, AnyHttpUrl, field_validator
from sqlalchemy import select
from .db import get_db
from .models import Invoice, Order, now, InvoiceImport
from .schemas import Strict, InvoiceOut
from .security import student, lock_user, ApiError
from .services import serialize, own_invoice, audit, expire

router = APIRouter(prefix="/api/v1", tags=["Invoice management"])


class InvoiceInput(Strict):
    invoice_number: str = Field(min_length=1, max_length=100)
    institution_name: str = Field(min_length=2, max_length=200)
    beneficiary_name: str = Field(min_length=2, max_length=200)
    amount_cny: str = Field(pattern=r"^\d{1,12}(\.\d{1,2})?$")
    due_date: date
    fee_type: str = Field(default="ANNUAL_HEALTH_INSURANCE_PREMIUM", min_length=1, max_length=100)
    notes: str = Field(default="", max_length=5000)
    source_url: AnyHttpUrl | None = None
    import_id: UUID | None = None
    import_reviewed: bool = Field(default=False, strict=True)

    @field_validator("invoice_number", "institution_name", "beneficiary_name", "fee_type")
    @classmethod
    def strip_required(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Required value is blank")
        return value

    @field_validator("amount_cny")
    @classmethod
    def positive(cls, value):
        if Decimal(value) <= 0:
            raise ValueError("Invoice amount must be positive")
        return value


def values(body):
    result = body.model_dump(exclude={"amount_cny", "source_url", "import_id", "import_reviewed"})
    result["amount_cny"] = Decimal(body.amount_cny).quantize(Decimal(".01"))
    result["source_url"] = str(body.source_url) if body.source_url else None
    return result


@router.post("/invoices", response_model=InvoiceOut)
def create(body: InvoiceInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    source = None
    if body.import_id:
        source = db.scalar(select(InvoiceImport).where(InvoiceImport.id == body.import_id, InvoiceImport.user_id == user.id))
        if not source:
            raise ApiError("IMPORT_NOT_FOUND", "Invoice source not found", 404)
        if not body.import_reviewed:
            raise ApiError("IMPORT_REVIEW_REQUIRED", "Review the source document and confirm the fields before saving", 422)
        if source.invoice_id:
            raise ApiError("IMPORT_ALREADY_USED", "This source has already been saved as an invoice", 409)
    if db.scalar(select(Invoice.id).where(Invoice.student_id == user.id, Invoice.invoice_number == body.invoice_number)):
        raise ApiError("INVOICE_NUMBER_EXISTS", "This invoice number already exists in your account")
    obj = Invoice(student_id=user.id, source_type="USER_ENTERED", is_real_beneficiary=False, **values(body))
    db.add(obj)
    db.flush()
    if source:
        source.invoice_id = obj.id
        audit(db, user, "OCR_FIELDS_HUMAN_REVIEWED", invoice_id=str(obj.id), import_id=str(source.id))
    audit(db, user, "INVOICE_CREATED", invoice_id=str(obj.id))
    db.refresh(obj)
    return serialize(obj)


def editable(db, invoice):
    active = list(db.scalars(select(Order).where(Order.invoice_id == invoice.id, Order.status.in_(["AWAITING_CONFIRMATION", "PROCESSING", "SUCCEEDED"])).with_for_update()))
    for order in active:
        expire(db, order)
    if any(o.status in ("AWAITING_CONFIRMATION", "PROCESSING", "SUCCEEDED") for o in active):
        raise ApiError("INVOICE_LOCKED", "Cancel the awaiting order first; processing/succeeded invoices cannot be changed")


@router.post("/invoices/{invoice_id}/update", response_model=InvoiceOut)
def update_invoice(invoice_id: UUID, body: InvoiceInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    invoice = own_invoice(db, invoice_id, user)
    editable(db, invoice)
    if invoice.source_type != "USER_ENTERED" or invoice.status == "VOID":
        raise ApiError("INVOICE_LOCKED", "This invoice cannot be edited")
    if db.scalar(select(Invoice.id).where(Invoice.student_id == user.id, Invoice.invoice_number == body.invoice_number, Invoice.id != invoice.id)):
        raise ApiError("INVOICE_NUMBER_EXISTS", "This invoice number already exists")
    for key, value in values(body).items():
        setattr(invoice, key, value)
    db.flush()
    audit(db, user, "INVOICE_UPDATED", invoice_id=str(invoice.id))
    return serialize(invoice)


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceOut)
def void(invoice_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    invoice = own_invoice(db, invoice_id, user)
    editable(db, invoice)
    invoice.status = "VOID"
    audit(db, user, "INVOICE_VOIDED", invoice_id=str(invoice.id))
    db.flush()
    return serialize(invoice)
