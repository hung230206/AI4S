import asyncio
import hmac
import uuid
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from typing import Annotated
from fastapi import FastAPI, Depends, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .config import settings, ROOT
from .db import get_db
from .models import User, Invoice, Quote, Order, Transaction, Event, Receipt, Audit, ProviderEvent, now
from .schemas import SessionRequest, CreateQuote, CreateOrder, ConfirmOrder, SimulateRequest, InvoiceOut, InvoiceList, QuoteOut, OrderOut, OrderList, ReceiptOut, EventList
from .security import ApiError, signer, student, operator, lock_user
from .seed import STUDENT_ID, OPERATOR_ID
from .services import serialize, own_invoice, own_order, payable, breakdown, audit, replay, remember, expire, iso
from .providers import provider, worker
from .webhooks import receive
from .accounts import router as accounts_router
from .billing import router as billing_router
from .documents import router as documents_router
from .fx import router as fx_router, reference_rate
from .finance import router as finance_router
from .ocr import router as ocr_router
from .journey import router as journey_router
from .insurance import router as insurance_router
from .privacy import router as privacy_router
from .rag import router as rag_router
from .study_assistant import router as study_assistant_router


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(worker(app)) if settings.demo_mode and settings.provider_worker_enabled else None
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Insurance Cross-border Payment • MOCK ONLY", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.frontend_origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-CSRF-Token", "X-Processing-Consent"])
app.include_router(accounts_router)
app.include_router(billing_router)
app.include_router(documents_router)
app.include_router(fx_router)
app.include_router(finance_router)
app.include_router(ocr_router)
app.include_router(journey_router)
app.include_router(insurance_router)
app.include_router(privacy_router)
app.include_router(rag_router)
app.include_router(study_assistant_router)


@app.middleware("http")
async def request_context(request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def error_response(request, code, message, status):
    return JSONResponse({"error": {"code": code, "message": message, "request_id": getattr(request.state, "request_id", "unknown")}}, status_code=status)


@app.exception_handler(ApiError)
async def api_error(request, exc):
    return error_response(request, exc.code, exc.message, exc.status)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    errors = exc.errors()
    field = str(errors[0]["loc"][-1]) if errors and errors[0].get("loc") else ""
    messages = {"email": "Email không hợp lệ.", "password": "Mật khẩu không hợp lệ. Khi đăng ký cần từ 10 đến 128 ký tự.", "new_password": "Mật khẩu mới cần từ 10 đến 128 ký tự.", "amount_cny": "Số tiền CNY phải lớn hơn 0 và tối đa 2 chữ số thập phân.", "display_name": "Tên hiển thị cần từ 2 đến 100 ký tự.", "due_date": "Ngày đến hạn không hợp lệ.", "source_url": "Nguồn phải là đường dẫn HTTP hoặc HTTPS hợp lệ."}
    return error_response(request, "VALIDATION_ERROR", messages.get(field, "Thông tin chưa hợp lệ. Hãy kiểm tra lại các trường của yêu cầu."), 422)


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return error_response(request, "RESOURCE_CONFLICT", "Conflicting operation; refresh current order before retrying", 409)


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    return error_response(request, "INTERNAL_ERROR", "Operation unavailable; use request ID to investigate", 500)


Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]


@app.get("/api/v1/health")
def health(db=Depends(get_db, scope="function")):
    import os
    db.execute(select(1))
    return {"status": "ok", "demo_mode": settings.demo_mode, "payment_provider": "MOCK", "allow_real_payments": False,
            "release": os.environ.get("RENDER_GIT_COMMIT", "local"), "insurance_workflow": "portfolio-claims-v1"}


@app.get("/api/v1/capabilities")
def capabilities():
    return {"accounts": True, "invoice_management": True, "reference_fx_provider": "Frankfurter", "reference_fx_url": "https://frankfurter.dev/", "policy_documents": True, "local_ocr": True, "multicurrency_ledger": True, "cashflow_forecast": True, "fx_scenarios": True, "insurance_portfolio": True, "coverage_comparison": True, "claim_preparation": True, "insurer_submission": False, "guidance_method": "EVIDENCE_AND_SCHEDULE_RULES", "payment_mode": "SANDBOX", "live_payments_configured": False, "sandbox_enabled": settings.demo_mode}


@app.post("/api/v1/demo/session")
def session(body: SessionRequest, db=Depends(get_db, scope="function")):
    if not settings.demo_mode:
        raise ApiError("FORBIDDEN", "Demo sign-in disabled", 403)
    if body.role == "OPERATOR" and not hmac.compare_digest(body.operator_code or "", settings.demo_operator_code):
        raise ApiError("FORBIDDEN", "Invalid local operator code", 403)
    user = db.get(User, STUDENT_ID if body.role == "STUDENT" else OPERATOR_ID)
    if not user:
        raise ApiError("DEMO_NOT_SEEDED", "Run python -m app.seed first", 503)
    return {"access_token": signer.dumps({"sub": str(user.id), "role": user.role, "jti": str(uuid.uuid4())}), "token_type": "bearer", "expires_in": 3600, "role": user.role}


@app.get("/api/v1/invoices", response_model=InvoiceList)
def invoices(q: str = "", status: str = "", user=Depends(student), db=Depends(get_db, scope="function")):
    query = select(Invoice).where(Invoice.student_id == user.id)
    if status in ("OPEN", "VOID"):
        query = query.where(Invoice.status == status)
    if q:
        term = q[:100]
        query = query.where(Invoice.invoice_number.icontains(term, autoescape=True) | Invoice.institution_name.icontains(term, autoescape=True) | Invoice.beneficiary_name.icontains(term, autoescape=True))
    return {"items": [serialize(i) for i in db.scalars(query.order_by(Invoice.created_at))]}


@app.get("/api/v1/invoices/{invoice_id}", response_model=InvoiceOut)
def invoice(invoice_id: uuid.UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    return serialize(own_invoice(db, invoice_id, user))


def expire_invoice_orders(db, invoice_id):
    for order in db.scalars(select(Order).where(Order.invoice_id == invoice_id, Order.status == "AWAITING_CONFIRMATION").with_for_update()):
        expire(db, order)


@app.post("/api/v1/quotes", response_model=QuoteOut)
def quote(body: CreateQuote, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    invoice = own_invoice(db, body.invoice_id, user)
    payable(invoice)
    expire_invoice_orders(db, invoice.id)
    reference = {}
    if body.demo_rate and not settings.demo_mode:
        raise ApiError("QUOTE_DEMO_DISABLED", "Demo quotes are disabled", 403)
    if invoice.source_type == "USER_ENTERED" and not body.demo_rate:
        rate, stale = reference_rate(db)
        money = breakdown(invoice.amount_cny, rate.vnd_per_cny, settings.service_fee_percent, settings.service_fixed_fee_vnd)
        reference = {"rate_source": "FRANKFURTER_REFERENCE", "rate_date": rate.rate_date, "rate_fetched_at": rate.fetched_at, "rate_is_stale": stale}
    else:
        money = breakdown(invoice.amount_cny)
    obj = Quote(invoice_id=invoice.id, student_id=user.id, expires_at=now() + timedelta(seconds=settings.fx_quote_ttl_seconds), **money, **reference)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return serialize(obj)


@app.post("/api/v1/orders", response_model=OrderOut)
def create_order(body: CreateOrder, idempotency_key: Key, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    data = body.model_dump(mode="json")
    previous = replay(db, user, "create", idempotency_key, data)
    if previous is not None:
        return previous
    invoice = own_invoice(db, body.invoice_id, user)
    payable(invoice)
    quote = db.get(Quote, body.quote_id)
    if not quote or quote.student_id != user.id:
        raise ApiError("QUOTE_NOT_FOUND", "Quote not found", 404)
    if quote.invoice_id != invoice.id or quote.source_amount_cny != invoice.amount_cny:
        raise ApiError("QUOTE_MISMATCH", "Quote does not match the current invoice")
    if quote.expires_at <= now():
        raise ApiError("QUOTE_EXPIRED", "Quote expired; request a new quote")
    expire_invoice_orders(db, invoice.id)
    if db.scalar(select(Order.id).where(Order.invoice_id == invoice.id, Order.status.in_(["AWAITING_CONFIRMATION", "PROCESSING", "SUCCEEDED"]))):
        raise ApiError("INVOICE_NOT_PAYABLE", "Invoice already has an active or succeeded simulated order")
    order = Order(student_id=user.id, invoice_id=invoice.id, quote_id=quote.id, amount_cny=quote.source_amount_cny, total_vnd=quote.total_vnd)
    db.add(order)
    db.flush()
    audit(db, user, "ORDER_CREATED", order.id)
    return remember(db, user, "create", idempotency_key, data, order)


@app.get("/api/v1/orders", response_model=OrderList)
def orders(user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    items = list(db.scalars(select(Order).where(Order.student_id == user.id).order_by(Order.created_at.desc()).with_for_update()))
    for item in items:
        expire(db, item)
    db.flush()
    return {"items": [serialize(i) for i in items]}


@app.get("/api/v1/orders/{order_id}", response_model=OrderOut)
def order_detail(order_id: uuid.UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    order = own_order(db, order_id, user, lock=True)
    return {**serialize(order), "quote": serialize(db.get(Quote, order.quote_id))}


@app.post("/api/v1/orders/{order_id}/confirm", response_model=OrderOut)
def confirm(order_id: uuid.UUID, body: ConfirmOrder, idempotency_key: Key, user=Depends(student), db=Depends(get_db, scope="function")):
    if not settings.demo_mode:
        raise ApiError("PAYMENT_NOT_CONFIGURED", "No payment provider account is configured", 503)
    lock_user(db, user)
    operation = f"confirm:{order_id}"
    data = body.model_dump(mode="json")
    if body.sandbox_scenario == "MANUAL":
        data.pop("sandbox_scenario")  # Preserve retries made before this additive field existed.
    previous = replay(db, user, operation, idempotency_key, data)
    if previous is not None:
        return previous
    order = own_order(db, order_id, user, lock=True)
    if not body.consent:
        raise ApiError("CONSENT_REQUIRED", "Explicit human consent required", 422)
    if body.quote_id != order.quote_id or (body.expected_total_vnd is not None and body.expected_total_vnd != format(order.total_vnd, ".0f")):
        raise ApiError("QUOTE_MISMATCH", "Confirmation differs from the reviewed quote")
    if order.status == "EXPIRED":
        db.commit()
        raise ApiError("QUOTE_EXPIRED", "Quote expired; create a new quote and order")
    if order.status != "AWAITING_CONFIRMATION":
        raise ApiError("ORDER_STATE_INVALID", "Order cannot be confirmed in its current state")
    invoice = own_invoice(db, order.invoice_id, user)
    payable(invoice)
    if invoice.amount_cny != order.amount_cny:
        raise ApiError("QUOTE_MISMATCH", "Invoice changed; obtain a fresh quote")
    if body.sandbox_scenario != "MANUAL" and not settings.provider_worker_enabled:
        raise ApiError("SANDBOX_WORKER_UNAVAILABLE", "Enable PROVIDER_WORKER_ENABLED before using automatic sandbox methods", 503)
    try:
        transaction = provider.create_payment(order_id=order.id, amount_minor=int(order.total_vnd), currency="VND", idempotency_key=str(order.id))
    except (ConnectionError, TimeoutError):
        raise ApiError("PROVIDER_TEMPORARILY_UNAVAILABLE", "Mock provider unavailable; retry using the same key", 503)
    db.add(transaction)
    order.status, order.confirmation_consent = "PROCESSING", True
    order.consent_at, order.consent_version = now(), body.consent_version
    order.sandbox_scenario = body.sandbox_scenario
    audit(db, user, "HUMAN_CONSENT_RECORDED", order.id, quote_id=str(order.quote_id), total_vnd=format(order.total_vnd, ".0f"), consent_version=body.consent_version)
    if body.sandbox_scenario != "MANUAL":
        # Test methods are chosen BEFORE consent; only the signed provider event settles the order.
        db.flush()
        outcome = "SUCCEEDED" if body.sandbox_scenario == "SUCCESS" else "FAILED"
        event = provider.queue_outcome(db, transaction, outcome)
        event.available_at = now() + timedelta(seconds=3)
        audit(db, "PROVIDER", "SANDBOX_METHOD_SELECTED", order.id, scenario=body.sandbox_scenario, external_event_id=event.external_event_id)
    return remember(db, user, operation, idempotency_key, data, order)


@app.post("/api/v1/orders/{order_id}/cancel", response_model=OrderOut)
def cancel(order_id: uuid.UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    order = own_order(db, order_id, user, lock=True)
    if order.status == "CANCELLED":
        return serialize(order)
    if order.status != "AWAITING_CONFIRMATION":
        raise ApiError("ORDER_STATE_INVALID", "Only unconfirmed orders may be cancelled")
    order.status = "CANCELLED"
    audit(db, user, "ORDER_CANCELLED", order.id)
    db.flush()
    return serialize(order)


@app.get("/api/v1/orders/{order_id}/events", response_model=EventList)
def events(order_id: uuid.UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    own_order(db, order_id, user, lock=True)
    items = [{k: value for k, value in serialize(e).items() if k not in ("payload_sha256", "transaction_id")} for e in db.scalars(select(Event).where(Event.order_id == order_id).order_by(Event.received_at))]
    logs = [{"action": a.action, "actor_type": a.actor_type, "created_at": iso(a.created_at), "safe_metadata": a.safe_metadata} for a in db.scalars(select(Audit).where(Audit.order_id == order_id).order_by(Audit.created_at))]
    return {"items": items, "audit": logs}


@app.get("/api/v1/orders/{order_id}/receipt", response_model=ReceiptOut)
def receipt(order_id: uuid.UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    order = own_order(db, order_id, user, lock=True)
    obj = db.scalar(select(Receipt).where(Receipt.order_id == order_id))
    if order.status != "SUCCEEDED" or not obj:
        raise ApiError("ORDER_STATE_INVALID", "Simulated receipt is available only after verified success")
    return {**serialize(obj), "amount_cny": format(order.amount_cny, ".2f"), "total_vnd": format(order.total_vnd, ".0f"), "invoice_number": db.get(Invoice, order.invoice_id).invoice_number}


@app.post("/api/v1/demo/orders/{order_id}/simulate")
def simulate(order_id: uuid.UUID, body: SimulateRequest, user=Depends(operator), db=Depends(get_db, scope="function")):
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if not order:
        raise ApiError("ORDER_NOT_FOUND", "Order not found", 404)
    if order.status != "PROCESSING":
        raise ApiError("ORDER_STATE_INVALID", "A consented processing order is required")
    transaction = db.scalar(select(Transaction).where(Transaction.order_id == order.id))
    event = provider.queue_outcome(db, transaction, body.outcome)
    audit(db, user, "PROVIDER_OUTCOME_REQUESTED", order.id, outcome=body.outcome)
    db.flush()
    return {"queued": True, "external_event_id": event.external_event_id}


@app.post("/api/v1/demo/events/{external_event_id}/replay")
def replay_event(external_event_id: str, user=Depends(operator), db=Depends(get_db, scope="function")):
    event = db.scalar(select(ProviderEvent).where(ProviderEvent.external_event_id == external_event_id).with_for_update())
    if not event:
        raise ApiError("EVENT_NOT_FOUND", "Mock-provider event not found", 404)
    event.delivered = False
    audit(db, user, "PROVIDER_REDELIVERY_REQUESTED", event.order_id, external_event_id=external_event_id)
    return {"queued": True, "external_event_id": external_event_id}


@app.post("/api/v1/webhooks/mock")
async def webhook(request: Request, db=Depends(get_db, scope="function")):
    if not settings.demo_mode:
        raise ApiError("FORBIDDEN", "Mock webhook disabled", 403)
    raw = await request.body()
    return await run_in_threadpool(receive, raw, request.headers, db)


@app.get("/api/v1/policy")
def policy(user=Depends(student)):
    if not user.is_demo:
        raise ApiError("POLICY_NOT_AVAILABLE", "Upload and search your own policy documents", 404)
    return {"source": "fixtures/demo_policy.md", "source_type": "SYNTHETIC", "content": (ROOT / "fixtures/demo_policy.md").read_text(encoding="utf-8"), "notice": "Fictional policy; not insurance advice. Benefits/exclusions/claims: Insufficient policy information."}
