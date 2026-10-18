"""Create an additional wholly fictional invoice for browser tests; no deletion/reset."""
import sys
import uuid
from pathlib import Path
from decimal import Decimal
from datetime import timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db import SessionLocal
from app.models import Invoice, now
from app.seed import STUDENT_ID

with SessionLocal.begin() as db:
    obj = Invoice(student_id=STUDENT_ID, invoice_number=f"UI-SMOKE-{uuid.uuid4().hex[:8]}", institution_name="Demo International University (fictional)", beneficiary_name="Demo Student Coverage Center (fictional)", fee_type="ANNUAL_HEALTH_INSURANCE_PREMIUM", amount_cny=Decimal("800.00"), due_date=now().date() + timedelta(days=30))
    db.add(obj)
    db.flush()
    print(obj.id)
