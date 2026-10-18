"""The mock is the only payment implementation. No network payment API exists."""
import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Protocol
import httpx
from sqlalchemy import select
from .config import settings
from .db import SessionLocal
from .models import Transaction, ProviderEvent, now


class PaymentProvider(Protocol):
    def create_payment(self, *, order_id: uuid.UUID, amount_minor: int, currency: str, idempotency_key: str) -> Transaction: ...
    def queue_outcome(self, db, transaction: Transaction, outcome: str) -> ProviderEvent: ...


def signed(payload, timestamp=None):
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ts = str(int(time.time()) if timestamp is None else timestamp)
    signature = hmac.new(settings.mock_webhook_secret.encode(), ts.encode() + b"." + raw, hashlib.sha256).hexdigest()
    return raw, {"X-Mock-Timestamp": ts, "X-Mock-Signature": signature, "Content-Type": "application/json"}


class MockPaymentProvider:
    def create_payment(self, *, order_id, amount_minor, currency, idempotency_key):
        if currency != "VND" or amount_minor <= 0:
            raise ValueError("Mock provider only accepts positive VND minor units")
        return Transaction(order_id=order_id, provider_payment_id=f"mock_{order_id}", sent_amount_vnd=amount_minor)

    def queue_outcome(self, db, transaction, outcome):
        event_id = f"evt_{uuid.uuid4()}"
        payload = dict(external_event_id=event_id, provider_payment_id=transaction.provider_payment_id, order_id=str(transaction.order_id), event_timestamp=now().isoformat(), status=outcome, amount_vnd=format(transaction.sent_amount_vnd, ".0f"), currency=transaction.currency)
        event = ProviderEvent(order_id=transaction.order_id, external_event_id=event_id, payload=payload)
        db.add(event)
        return event


provider: PaymentProvider = MockPaymentProvider()


async def deliver_pending(app):
    """Persisted provider events enter the actual public webhook route, HMAC included."""
    with SessionLocal() as db:
        ids = list(db.scalars(select(ProviderEvent.id).where(ProviderEvent.delivered == False, ProviderEvent.available_at <= now()).order_by(ProviderEvent.available_at).limit(20)))  # noqa: E712
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
        for event_id in ids:
            with SessionLocal.begin() as db:
                event = db.get(ProviderEvent, event_id)
                if event.delivered:
                    continue
                payload = dict(event.payload)
                # A retry signs a fresh delivery timestamp; event time remains the original.
                raw, headers = signed(payload)
                response = await client.post("/api/v1/webhooks/mock", content=raw, headers=headers)
                event.attempts += 1
                event.last_http_status = response.status_code
                event.delivered = response.is_success or response.status_code in (409, 422)


async def worker(app):
    while True:
        try:
            await deliver_pending(app)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Do not log raw payloads, credentials, or DSNs.
            logging.getLogger(__name__).warning("Mock delivery deferred; retrying")
        await asyncio.sleep(0.5)
