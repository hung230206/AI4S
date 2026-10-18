import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta, datetime, timezone
from uuid import UUID
from sqlalchemy import select
from .config import settings
from .models import Invoice, Quote, Order, Idempotency, Audit, now
from .security import ApiError

ACTIVE = ("AWAITING_CONFIRMATION", "PROCESSING", "SUCCEEDED")


def iso(value):
    if isinstance(value, datetime):
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def serialize(obj):
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, Decimal):
            value = format(value, "f")
        elif isinstance(value, UUID):
            value = str(value)
        elif hasattr(value, "isoformat"):
            value = iso(value)
        result[column.name] = value
    if isinstance(obj, Order):
        result["is_simulated"] = True
    if isinstance(obj, Quote):
        result["is_simulated"] = obj.rate_source == "DEMO_FIXED"
        result["purpose"] = "SANDBOX_QUOTE" if obj.rate_source == "DEMO_FIXED" else "REFERENCE_ESTIMATE"
    if isinstance(obj, Invoice):
        result["amount"] = format(obj.amount_cny, ".2f")
    return result


def audit(db, actor, action, order_id=None, **metadata):
    db.add(Audit(actor_type=actor.role if hasattr(actor, "role") else actor, actor_id=str(actor.id) if hasattr(actor, "id") else None, action=action, order_id=order_id, safe_metadata=metadata))


def own_invoice(db, invoice_id, user):
    obj = db.scalar(select(Invoice).where(Invoice.id == invoice_id, Invoice.student_id == user.id))
    if not obj:
        raise ApiError("INVOICE_NOT_FOUND", "Invoice not found", 404)
    return obj


def payable(invoice):
    if invoice.status != "OPEN" or invoice.due_date < now().date():
        raise ApiError("INVOICE_NOT_PAYABLE", "Invoice is void or past its due date")


def expire(db, order):
    if order.status == "AWAITING_CONFIRMATION" and db.get(Quote, order.quote_id).expires_at <= now():
        order.status = "EXPIRED"
        audit(db, "SYSTEM", "QUOTE_EXPIRED", order.id)
        db.flush()


def own_order(db, order_id, user, lock=False):
    query = select(Order).where(Order.id == order_id, Order.student_id == user.id)
    if lock:
        query = query.with_for_update()
    obj = db.scalar(query)
    if not obj:
        raise ApiError("ORDER_NOT_FOUND", "Order not found", 404)
    expire(db, obj)
    return obj


def breakdown(amount, rate=None, fee_percent=None, fixed_fee=None):
    rate = settings.fx_demo_vnd_per_cny if rate is None else rate
    fee_percent = settings.fx_demo_variable_fee_percent if fee_percent is None else fee_percent
    fixed_fee = settings.fx_demo_fixed_fee_vnd if fixed_fee is None else fixed_fee
    principal = (amount * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    fee = (principal * fee_percent / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return dict(source_amount_cny=amount, vnd_per_cny=rate.quantize(Decimal(".000001")), converted_subtotal_vnd=principal, variable_fee_rate_percent=fee_percent.quantize(Decimal(".0001")), variable_fee_vnd=fee, fixed_fee_vnd=fixed_fee, total_vnd=principal + fee + fixed_fee)


def digest(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def replay(db, user, operation, key, body):
    record = db.scalar(select(Idempotency).where(Idempotency.user_id == user.id, Idempotency.operation == operation, Idempotency.idempotency_key == key))
    if record:
        if record.request_hash != digest(body):
            raise ApiError("IDEMPOTENCY_CONFLICT", "Key already used for a different request")
        return record.response
    return None


def remember(db, user, operation, key, body, order):
    db.flush()
    db.refresh(order)
    response = serialize(order)
    db.add(Idempotency(user_id=user.id, operation=operation, idempotency_key=key, request_hash=digest(body), order_id=order.id, response=response))
    return response
