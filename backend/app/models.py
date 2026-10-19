"""SQLAlchemy 2 ORM; schema invariants are also enforced by PostgreSQL."""
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index, text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Created:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Identity, Created, Base):
    __tablename__ = "demo_users"
    display_name: Mapped[str]
    role: Mapped[str]
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None]
    is_demo: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    __table_args__ = (CheckConstraint("role IN ('STUDENT','OPERATOR')"),)


class Invoice(Identity, Created, Base):
    __tablename__ = "insurance_invoices"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    invoice_number: Mapped[str]
    country_code: Mapped[str] = mapped_column(String(2), default="CN")
    institution_name: Mapped[str]
    beneficiary_name: Mapped[str]
    fee_type: Mapped[str]
    amount_cny: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(default="CNY")
    due_date: Mapped[date]
    source_type: Mapped[str] = mapped_column(default="SYNTHETIC")
    is_real_beneficiary: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(default="OPEN")
    notes: Mapped[str] = mapped_column(default="", server_default="")
    source_url: Mapped[str | None]
    __table_args__ = (UniqueConstraint("student_id", "invoice_number", name="uq_invoice_owner_number"), CheckConstraint("amount_cny > 0 AND currency = 'CNY'"), CheckConstraint("source_type IN ('SYNTHETIC','USER_ENTERED') AND is_real_beneficiary = false", name="ck_invoice_provenance"), CheckConstraint("status IN ('OPEN','VOID')"))


class Quote(Identity, Created, Base):
    __tablename__ = "fx_quotes"
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("insurance_invoices.id"))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    source_amount_cny: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    vnd_per_cny: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    converted_subtotal_vnd: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    variable_fee_rate_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    variable_fee_vnd: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    fixed_fee_vnd: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    total_vnd: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    source_currency: Mapped[str] = mapped_column(default="CNY")
    settlement_currency: Mapped[str] = mapped_column(default="VND")
    rate_source: Mapped[str] = mapped_column(default="DEMO_FIXED")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rate_date: Mapped[date | None]
    rate_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rate_is_stale: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    __table_args__ = (CheckConstraint("source_amount_cny > 0 AND vnd_per_cny > 0 AND converted_subtotal_vnd >= 0 AND variable_fee_rate_percent >= 0 AND variable_fee_vnd >= 0 AND fixed_fee_vnd >= 0"), CheckConstraint("total_vnd = converted_subtotal_vnd + variable_fee_vnd + fixed_fee_vnd"), CheckConstraint("expires_at > created_at"), CheckConstraint("source_currency='CNY' AND settlement_currency='VND' AND rate_source IN ('DEMO_FIXED','FRANKFURTER_REFERENCE')", name="ck_quote_rate_source"))


class Order(Identity, Created, Base):
    __tablename__ = "payment_orders"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("insurance_invoices.id"))
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fx_quotes.id"), unique=True)
    amount_cny: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(default="CNY")
    total_vnd: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    payment_provider: Mapped[str] = mapped_column(default="MOCK")
    status: Mapped[str] = mapped_column(default="AWAITING_CONFIRMATION")
    confirmation_consent: Mapped[bool] = mapped_column(default=False)
    consent_version: Mapped[str | None]
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sandbox_scenario: Mapped[str] = mapped_column(default="MANUAL", server_default="MANUAL")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    __table_args__ = (CheckConstraint("sandbox_scenario IN ('MANUAL','SUCCESS','DECLINED')", name="ck_order_sandbox_scenario"), CheckConstraint("amount_cny > 0 AND total_vnd > 0 AND currency='CNY' AND payment_provider='MOCK'"), CheckConstraint("status IN ('AWAITING_CONFIRMATION','PROCESSING','SUCCEEDED','FAILED','CANCELLED','EXPIRED')"), CheckConstraint("confirmation_consent=false OR (consent_at IS NOT NULL AND consent_version IS NOT NULL)"), Index("ux_active_invoice_order", "invoice_id", unique=True, postgresql_where=text("status IN ('AWAITING_CONFIRMATION','PROCESSING','SUCCEEDED')")))


class Idempotency(Identity, Created, Base):
    __tablename__ = "idempotency_records"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"))
    operation: Mapped[str]
    idempotency_key: Mapped[str]
    request_hash: Mapped[str] = mapped_column(String(64))
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_orders.id"))
    response: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = (UniqueConstraint("user_id", "operation", "idempotency_key"), CheckConstraint("length(idempotency_key) BETWEEN 8 AND 128"))


class Transaction(Identity, Created, Base):
    __tablename__ = "payment_transactions"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_orders.id"), unique=True)
    provider_payment_id: Mapped[str] = mapped_column(unique=True)
    provider_status: Mapped[str] = mapped_column(default="PROCESSING")
    sent_amount_vnd: Mapped[Decimal] = mapped_column(Numeric(20, 0))
    currency: Mapped[str] = mapped_column(default="VND")
    is_simulated: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    __table_args__ = (CheckConstraint("sent_amount_vnd > 0 AND currency='VND' AND is_simulated=true"),)


class Event(Identity, Base):
    __tablename__ = "payment_events"
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payment_orders.id"), index=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payment_transactions.id"))
    external_event_id: Mapped[str] = mapped_column(unique=True)
    event_type: Mapped[str]
    provider_status: Mapped[str | None]
    signature_verified: Mapped[bool]
    payload_sha256: Mapped[str] = mapped_column(String(64))
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    processing_outcome: Mapped[str]
    safe_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (CheckConstraint("processing_outcome IN ('APPLIED','DUPLICATE','IGNORED','REJECTED')"),)


class Receipt(Identity, Base):
    __tablename__ = "payment_receipts"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_orders.id"), unique=True)
    receipt_number: Mapped[str] = mapped_column(unique=True)
    is_simulated: Mapped[bool] = mapped_column(default=True)
    notice: Mapped[str] = mapped_column(default="SIMULATED TRANSACTION — NO REAL FUNDS MOVED")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("is_simulated=true"),)


class Audit(Identity, Created, Base):
    __tablename__ = "audit_logs"
    actor_type: Mapped[str]
    actor_id: Mapped[str | None]
    action: Mapped[str]
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payment_orders.id"), index=True)
    safe_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (CheckConstraint("actor_type IN ('STUDENT','OPERATOR','SYSTEM','PROVIDER')"),)


class ProviderEvent(Identity, Created, Base):
    """Durable mock-provider outbox. Never included in student API responses."""
    __tablename__ = "mock_provider_outbox"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_orders.id"))
    external_event_id: Mapped[str] = mapped_column(unique=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    delivered: Mapped[bool] = mapped_column(default=False)
    attempts: Mapped[int] = mapped_column(default=0)
    last_http_status: Mapped[int | None]
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, server_default=text("now()"))


class AuthSession(Identity, Created, Base):
    __tablename__ = "account_sessions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_token: Mapped[str]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(default=False)


class AuthThrottle(Base):
    __tablename__ = "auth_throttle"
    bucket: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int]
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AiPermission(Base):
    """Optional cloud AI permission, bound to one authenticated session, never a shared user."""
    __tablename__ = "ai_permissions"
    subject: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    revision: Mapped[int] = mapped_column(default=1)
    notice_version: Mapped[str]
    active: Mapped[bool] = mapped_column(default=False)
    scopes: Mapped[list] = mapped_column(JSONB, default=list)
    data_mode: Mapped[str]
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint("revision > 0"), CheckConstraint("data_mode IN ('DEMO_ONLY','PAID_PRIVATE')"),)


class FxObservation(Identity, Created, Base):
    __tablename__ = "fx_observations"
    rate_date: Mapped[date] = mapped_column(unique=True)
    vnd_per_cny: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    source: Mapped[str] = mapped_column(default="FRANKFURTER_REFERENCE")
    __table_args__ = (CheckConstraint("vnd_per_cny > 0 AND source='FRANKFURTER_REFERENCE'"),)


class PolicyDocument(Identity, Created, Base):
    __tablename__ = "policy_documents"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    title: Mapped[str]
    filename: Mapped[str]
    content_type: Mapped[str]
    byte_size: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    pages: Mapped[list] = mapped_column(JSONB)
    source_url: Mapped[str | None]
    document_kind: Mapped[str] = mapped_column(default="USER_PROVIDED", server_default="USER_PROVIDED")
    __table_args__ = (UniqueConstraint("user_id", "sha256", name="uq_document_owner_hash"), CheckConstraint("document_kind IN ('USER_PROVIDED','PUBLIC_REFERENCE','TEST_FIXTURE')", name="ck_policy_document_kind"))


class InsurancePolicy(Identity, Created, Base):
    """Reviewed personal summary. A source document is not proof of issued cover."""
    __tablename__ = "insurance_portfolio"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policy_documents.id"))
    name: Mapped[str]
    insurer: Mapped[str]
    currency: Mapped[str]
    premium: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    premium_due: Mapped[date]
    starts_on: Mapped[date]
    ends_on: Mapped[date]
    territory: Mapped[str]
    benefits: Mapped[list] = mapped_column(JSONB)
    notes: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
    revision: Mapped[int] = mapped_column(default=1)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finance_plan_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("finance_plans.id"), unique=True)
    plan_revision: Mapped[int | None]
    premium_invoice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("insurance_invoices.id"), unique=True)
    request_key: Mapped[str]
    request_hash: Mapped[str]
    __table_args__ = (UniqueConstraint("user_id", "request_key"), CheckConstraint("currency IN ('CNY','VND') AND premium >= 0 AND ends_on >= starts_on AND revision > 0", name="ck_portfolio_values"), CheckConstraint("territory IN ('CN','VN','WORLD')", name="ck_portfolio_territory"))


class InsuranceClaim(Identity, Created, Base):
    """Preparation workspace; all insurer communication happens outside this app."""
    __tablename__ = "insurance_claim_cases"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("insurance_portfolio.id"))
    title: Mapped[str]
    benefit_kind: Mapped[str]
    incident_date: Mapped[date]
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str]
    description: Mapped[str]
    deadline: Mapped[date | None]
    status: Mapped[str] = mapped_column(default="DRAFT")
    revision: Mapped[int] = mapped_column(default=1)
    checklist: Mapped[dict] = mapped_column(JSONB, default=dict)
    policy_snapshot: Mapped[dict] = mapped_column(JSONB)
    history: Mapped[list] = mapped_column(JSONB, default=list)
    request_key: Mapped[str]
    request_hash: Mapped[str]
    __table_args__ = (UniqueConstraint("user_id", "request_key"), CheckConstraint("amount > 0 AND currency IN ('CNY','VND') AND revision > 0", name="ck_claim_values"), CheckConstraint("status IN ('DRAFT','READY','SUBMITTED_EXTERNALLY','CLOSED')", name="ck_claim_status"), CheckConstraint("benefit_kind IN ('OUTPATIENT','INPATIENT','ACCIDENT','EVACUATION')", name="ck_claim_kind"))


class ClaimAttachment(Identity, Created, Base):
    __tablename__ = "insurance_claim_attachments"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("insurance_claim_cases.id"), index=True)
    item_code: Mapped[str]
    filename: Mapped[str]
    content_type: Mapped[str]
    byte_size: Mapped[int]
    sha256: Mapped[str]
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    __table_args__ = (UniqueConstraint("claim_id", "sha256"), CheckConstraint("byte_size > 0 AND byte_size <= 5242880", name="ck_claim_attachment_size"))


class FinanceWallet(Identity, Created, Base):
    __tablename__ = "finance_wallets"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    name: Mapped[str]
    currency: Mapped[str]
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    opening_date: Mapped[date]
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_wallet_owner_name"), CheckConstraint("currency IN ('CNY','VND') AND opening_balance >= 0", name="ck_wallet_money"))


class FinancePlan(Identity, Created, Base):
    __tablename__ = "finance_plans"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("finance_wallets.id"))
    title: Mapped[str]
    kind: Mapped[str]
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    category: Mapped[str]
    due_date: Mapped[date]
    recurrence: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("insurance_invoices.id"), unique=True)
    __table_args__ = (CheckConstraint("amount > 0 AND kind IN ('INCOME','EXPENSE') AND recurrence IN ('NONE','MONTHLY')", name="ck_plan_values"),)


class FinanceEntry(Identity, Created, Base):
    __tablename__ = "finance_entries"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("finance_wallets.id"))
    title: Mapped[str]
    kind: Mapped[str]
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    category: Mapped[str]
    occurred_on: Mapped[date]
    status: Mapped[str] = mapped_column(default="POSTED")
    plan_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("finance_plans.id"))
    scheduled_date: Mapped[date | None]
    request_key: Mapped[str]
    request_hash: Mapped[str]
    __table_args__ = (UniqueConstraint("user_id", "request_key", name="uq_entry_owner_key"), CheckConstraint("amount > 0 AND kind IN ('INCOME','EXPENSE') AND status IN ('POSTED','VOID')", name="ck_entry_values"), Index("uq_plan_posted_occurrence", "plan_id", "scheduled_date", unique=True, postgresql_where=text("status='POSTED' AND plan_id IS NOT NULL")))


class InvoiceImport(Identity, Created, Base):
    __tablename__ = "invoice_imports"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("demo_users.id"), index=True)
    filename: Mapped[str]
    content_type: Mapped[str]
    sha256: Mapped[str] = mapped_column(String(64))
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    pages: Mapped[list] = mapped_column(JSONB)
    suggestions: Mapped[dict] = mapped_column(JSONB)
    method: Mapped[str]
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("insurance_invoices.id"), unique=True)
