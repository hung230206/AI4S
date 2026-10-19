import json
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.dialects.postgresql import insert
from .config import ROOT
from .db import SessionLocal
from .models import User, Invoice

STUDENT_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
OPERATOR_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")


def seed(db):
    for uid, name, role in [(STUDENT_ID, "Demo Student", "STUDENT"), (OPERATOR_ID, "Demo Operator", "OPERATOR")]:
        db.execute(insert(User).values(id=uid, display_name=name, role=role, is_demo=True).on_conflict_do_nothing(index_elements=["id"]))
    for item in json.loads((ROOT / "fixtures/demo_invoices.json").read_text(encoding="utf-8")):
        values = {k: item[k] for k in ("invoice_number", "country_code", "institution_name", "beneficiary_name", "fee_type", "currency", "source_type", "is_real_beneficiary")}
        values.update(id=uuid.UUID(item["id"]), student_id=STUDENT_ID, amount_cny=Decimal(item["amount"]), due_date=date.fromisoformat(item["due_date"]), status="OPEN")
        db.execute(insert(Invoice).values(**values).on_conflict_do_nothing(index_elements=["id"]))
    from .rag_seed import seed_rag
    from .rag_admin import provision_configured
    seed_rag(db)
    provision_configured(db)


if __name__ == "__main__":
    with SessionLocal.begin() as session:
        seed(session)
    print("Seed complete: synthetic invoice + student/operator; existing data preserved.")
