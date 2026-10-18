from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionRequest(Strict):
    role: Literal["STUDENT", "OPERATOR"]
    operator_code: str | None = Field(default=None, max_length=200)


class CreateQuote(Strict):
    invoice_id: UUID
    settlement_currency: Literal["VND"]


class CreateOrder(Strict):
    invoice_id: UUID
    quote_id: UUID


class ConfirmOrder(Strict):
    quote_id: UUID
    consent: bool = Field(strict=True)
    consent_version: Literal["demo-v1"]
    expected_total_vnd: str | None = Field(default=None, pattern=r"^\d{1,20}$")
    sandbox_scenario: Literal["MANUAL", "SUCCESS", "DECLINED"] = "MANUAL"


class SimulateRequest(Strict):
    outcome: Literal["SUCCEEDED", "FAILED"]
    reason: str | None = Field(default=None, max_length=200)


class WebhookEvent(Strict):
    external_event_id: str = Field(min_length=8, max_length=128)
    provider_payment_id: str = Field(min_length=8, max_length=128)
    order_id: UUID
    event_timestamp: AwareDatetime
    status: Literal["SUCCEEDED", "FAILED"]
    amount_vnd: str = Field(pattern=r"^\d{1,20}$")
    currency: str = Field(min_length=3, max_length=3)


class InvoiceOut(BaseModel):
    id: UUID
    invoice_number: str
    country_code: str
    institution_name: str
    beneficiary_name: str
    fee_type: str
    amount_cny: str
    currency: Literal["CNY"]
    due_date: str
    source_type: Literal["SYNTHETIC", "USER_ENTERED"]
    is_real_beneficiary: Literal[False]
    status: Literal["OPEN", "VOID"]
    notes: str = ""
    source_url: str | None = None


class InvoiceList(BaseModel):
    items: list[InvoiceOut]


class QuoteOut(BaseModel):
    id: UUID
    invoice_id: UUID
    source_amount_cny: str
    source_currency: Literal["CNY"]
    settlement_currency: Literal["VND"]
    vnd_per_cny: str
    converted_subtotal_vnd: str
    variable_fee_rate_percent: str
    variable_fee_vnd: str
    fixed_fee_vnd: str
    total_vnd: str
    rate_source: Literal["DEMO_FIXED", "FRANKFURTER_REFERENCE"]
    rate_date: str | None = None
    rate_fetched_at: str | None = None
    rate_is_stale: bool = False
    created_at: str
    expires_at: str
    is_simulated: bool
    purpose: Literal["SANDBOX_QUOTE", "REFERENCE_ESTIMATE"]


class OrderOut(BaseModel):
    id: UUID
    invoice_id: UUID
    quote_id: UUID
    amount_cny: str
    currency: Literal["CNY"]
    total_vnd: str
    status: Literal["AWAITING_CONFIRMATION", "PROCESSING", "SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"]
    payment_provider: Literal["MOCK"]
    confirmation_consent: bool
    consent_at: str | None
    consent_version: str | None
    created_at: str
    updated_at: str
    is_simulated: Literal[True]
    sandbox_scenario: Literal["MANUAL", "SUCCESS", "DECLINED"] = "MANUAL"
    quote: QuoteOut | None = None


class OrderList(BaseModel):
    items: list[OrderOut]


class ReceiptOut(BaseModel):
    receipt_number: str
    order_id: UUID
    is_simulated: Literal[True]
    notice: str
    issued_at: str
    amount_cny: str
    total_vnd: str
    invoice_number: str


class EventOut(BaseModel):
    external_event_id: str
    event_type: str
    provider_status: str | None
    received_at: str
    processing_outcome: Literal["APPLIED", "DUPLICATE", "IGNORED", "REJECTED"]
    signature_verified: bool
    safe_metadata: dict


class AuditOut(BaseModel):
    action: str
    actor_type: str
    created_at: str
    safe_metadata: dict


class EventList(BaseModel):
    items: list[EventOut]
    audit: list[AuditOut]
