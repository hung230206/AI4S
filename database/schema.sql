-- Logical PostgreSQL 16 schema; implement matching Alembic migration.
-- Zero real funds and no real insurance beneficiary.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS demo_users (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 display_name TEXT NOT NULL,
 role TEXT NOT NULL CHECK (role IN ('STUDENT','OPERATOR')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS insurance_invoices (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 student_id UUID NOT NULL REFERENCES demo_users(id),
 invoice_number TEXT NOT NULL UNIQUE,
 country_code CHAR(2) NOT NULL DEFAULT 'CN',
 institution_name TEXT NOT NULL,
 beneficiary_name TEXT NOT NULL,
 fee_type TEXT NOT NULL,
 amount_cny NUMERIC(20,2) NOT NULL CHECK (amount_cny > 0),
 currency CHAR(3) NOT NULL DEFAULT 'CNY' CHECK (currency = 'CNY'),
 due_date DATE NOT NULL,
 source_type TEXT NOT NULL DEFAULT 'SYNTHETIC' CHECK (source_type = 'SYNTHETIC'),
 is_real_beneficiary BOOLEAN NOT NULL DEFAULT false CHECK (is_real_beneficiary = false),
 status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','VOID')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_invoice_student ON insurance_invoices(student_id);
CREATE TABLE IF NOT EXISTS fx_quotes (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 invoice_id UUID NOT NULL REFERENCES insurance_invoices(id),
 student_id UUID NOT NULL REFERENCES demo_users(id),
 source_amount_cny NUMERIC(20,2) NOT NULL CHECK (source_amount_cny > 0),
 vnd_per_cny NUMERIC(20,6) NOT NULL CHECK (vnd_per_cny > 0),
 converted_subtotal_vnd NUMERIC(20,0) NOT NULL CHECK (converted_subtotal_vnd >= 0),
 variable_fee_rate_percent NUMERIC(8,4) NOT NULL CHECK (variable_fee_rate_percent >= 0),
 variable_fee_vnd NUMERIC(20,0) NOT NULL CHECK (variable_fee_vnd >= 0),
 fixed_fee_vnd NUMERIC(20,0) NOT NULL CHECK (fixed_fee_vnd >= 0),
 total_vnd NUMERIC(20,0) NOT NULL CHECK (total_vnd = converted_subtotal_vnd + variable_fee_vnd + fixed_fee_vnd),
 source_currency CHAR(3) NOT NULL DEFAULT 'CNY' CHECK (source_currency = 'CNY'),
 settlement_currency CHAR(3) NOT NULL DEFAULT 'VND' CHECK (settlement_currency = 'VND'),
 rate_source TEXT NOT NULL DEFAULT 'DEMO_FIXED' CHECK (rate_source = 'DEMO_FIXED'),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 expires_at TIMESTAMPTZ NOT NULL,
 CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS idx_quotes_student ON fx_quotes(student_id, expires_at);
CREATE TABLE IF NOT EXISTS payment_orders (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 student_id UUID NOT NULL REFERENCES demo_users(id),
 invoice_id UUID NOT NULL REFERENCES insurance_invoices(id),
 quote_id UUID NOT NULL UNIQUE REFERENCES fx_quotes(id),
 amount_cny NUMERIC(20,2) NOT NULL CHECK (amount_cny > 0),
 currency CHAR(3) NOT NULL DEFAULT 'CNY' CHECK (currency = 'CNY'),
 total_vnd NUMERIC(20,0) NOT NULL CHECK (total_vnd > 0),
 payment_provider TEXT NOT NULL DEFAULT 'MOCK' CHECK (payment_provider = 'MOCK'),
 status TEXT NOT NULL DEFAULT 'AWAITING_CONFIRMATION' CHECK (status IN ('AWAITING_CONFIRMATION','PROCESSING','SUCCEEDED','FAILED','CANCELLED','EXPIRED')),
 confirmation_consent BOOLEAN NOT NULL DEFAULT false,
 consent_version TEXT,
 consent_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CHECK (confirmation_consent = false OR (consent_at IS NOT NULL AND consent_version IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_orders_student ON payment_orders(student_id,created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_invoice_order ON payment_orders(invoice_id)
 WHERE status IN ('AWAITING_CONFIRMATION','PROCESSING','SUCCEEDED');
CREATE TABLE IF NOT EXISTS idempotency_records (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES demo_users(id),
 operation TEXT NOT NULL,
 idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 128),
 request_hash CHAR(64) NOT NULL,
 order_id UUID REFERENCES payment_orders(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(user_id,operation,idempotency_key)
);
CREATE TABLE IF NOT EXISTS payment_transactions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 order_id UUID NOT NULL UNIQUE REFERENCES payment_orders(id),
 provider_payment_id TEXT NOT NULL UNIQUE,
 provider_status TEXT NOT NULL DEFAULT 'PROCESSING',
 sent_amount_vnd NUMERIC(20,0) NOT NULL CHECK(sent_amount_vnd > 0),
 currency CHAR(3) NOT NULL DEFAULT 'VND' CHECK(currency='VND'),
 is_simulated BOOLEAN NOT NULL DEFAULT true CHECK(is_simulated=true),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS payment_events (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 order_id UUID REFERENCES payment_orders(id),
 transaction_id UUID REFERENCES payment_transactions(id),
 external_event_id TEXT NOT NULL UNIQUE,
 event_type TEXT NOT NULL,
 provider_status TEXT,
 signature_verified BOOLEAN NOT NULL,
 payload_sha256 CHAR(64) NOT NULL,
 event_timestamp TIMESTAMPTZ NOT NULL,
 received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 processing_outcome TEXT NOT NULL CHECK(processing_outcome IN ('APPLIED','DUPLICATE','IGNORED','REJECTED')),
 safe_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_event_order ON payment_events(order_id,received_at);
CREATE TABLE IF NOT EXISTS payment_receipts (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 order_id UUID NOT NULL UNIQUE REFERENCES payment_orders(id),
 receipt_number TEXT NOT NULL UNIQUE,
 is_simulated BOOLEAN NOT NULL DEFAULT true CHECK(is_simulated=true),
 notice TEXT NOT NULL DEFAULT 'SIMULATED TRANSACTION - NO REAL FUNDS MOVED',
 issued_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 actor_type TEXT NOT NULL CHECK(actor_type IN ('STUDENT','OPERATOR','SYSTEM','PROVIDER')),
 actor_id TEXT, action TEXT NOT NULL,
 order_id UUID REFERENCES payment_orders(id),
 safe_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_order ON audit_logs(order_id,created_at);
