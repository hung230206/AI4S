import hashlib
import hmac
import time
from decimal import Decimal
from pydantic import ValidationError
from sqlalchemy import select, text
from .config import settings
from .models import Order, Transaction, Event, Receipt, now
from .schemas import WebhookEvent
from .security import ApiError
from .services import audit


def receive(raw: bytes, headers, db):
    if len(raw) > 16384:
        raise ApiError("INVALID_EVENT", "Event too large", 422)
    ts = headers.get("X-Mock-Timestamp", "")
    signature = headers.get("X-Mock-Signature", "")
    expected = hmac.new(settings.mock_webhook_secret.encode(), ts.encode() + b"." + raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ApiError("EVENT_BAD_SIGNATURE", "Invalid mock signature", 401)
    try:
        stale = abs(int(time.time()) - int(ts)) > 300
    except ValueError:
        stale = True
    if stale:
        raise ApiError("EVENT_STALE_TIMESTAMP", "Delivery timestamp outside five-minute tolerance", 401)
    try:
        event = WebhookEvent.model_validate_json(raw)
    except ValidationError:
        raise ApiError("INVALID_EVENT", "Malformed provider event", 422)
    payload_hash = hashlib.sha256(raw).hexdigest()
    # Global lock serializes event-ID deduplication even if two events name different orders.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": event.external_event_id})
    previous = db.scalar(select(Event).where(Event.external_event_id == event.external_event_id))
    if previous:
        if previous.payload_sha256 != payload_hash:
            raise ApiError("EVENT_DATA_MISMATCH", "Event ID already used for different content")
        audit(db, "PROVIDER", "DUPLICATE_WEBHOOK", previous.order_id, external_event_id=event.external_event_id)
        return {"accepted": previous.processing_outcome != "REJECTED", "duplicate": True}
    order = db.scalar(select(Order).where(Order.id == event.order_id).with_for_update())
    transaction = db.scalar(select(Transaction).where(Transaction.order_id == event.order_id))
    if not order or not transaction:
        raise ApiError("ORDER_NOT_FOUND", "Provider intent not found", 404)
    valid = (transaction.provider_payment_id == event.provider_payment_id and Decimal(event.amount_vnd) == transaction.sent_amount_vnd and Decimal(event.amount_vnd) == order.total_vnd and event.currency == transaction.currency)
    outcome = "REJECTED" if not valid else "APPLIED" if order.status == "PROCESSING" and event.event_timestamp >= transaction.created_at and event.event_timestamp <= now() else "IGNORED"
    db.add(Event(order_id=order.id, transaction_id=transaction.id, external_event_id=event.external_event_id, event_type="MOCK_PAYMENT_STATUS", provider_status=event.status, signature_verified=True, payload_sha256=payload_hash, event_timestamp=event.event_timestamp, processing_outcome=outcome, safe_metadata={"is_simulated": True}))
    audit(db, "PROVIDER", f"WEBHOOK_{outcome}", order.id, external_event_id=event.external_event_id)
    if not valid:
        db.commit()  # Preserve verified rejection evidence; never mutate order.
        raise ApiError("EVENT_DATA_MISMATCH", "Provider amount, currency or payment ID differs from intent")
    if outcome == "APPLIED":
        order.status = event.status
        transaction.provider_status = event.status
        if event.status == "SUCCEEDED":
            db.add(Receipt(order_id=order.id, receipt_number=f"SIM-{str(order.id).upper()}"))
    db.flush()
    return {"accepted": True, "duplicate": False, "processing_outcome": outcome}
