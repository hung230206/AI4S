"""Public daily reference data only. No user information is sent upstream."""
import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from .config import settings
from .db import get_db
from .models import FxObservation, now
from .security import ApiError, student
from .services import iso

router = APIRouter(prefix="/api/v1/fx", tags=["Reference exchange rates"])
SOURCE_URL = "https://frankfurter.dev/"
API_URL = "https://api.frankfurter.dev/v2"


def fetch_json(path, params=None):
    response = httpx.get(API_URL + path, params=params, timeout=8, follow_redirects=False)
    response.raise_for_status()
    if len(response.content) > 200_000:
        raise ValueError("Upstream response too large")
    return json.loads(response.text, parse_float=Decimal)


def validate_row(row):
    when = date.fromisoformat(row["date"])
    rate = Decimal(str(row["rate"]))
    if row["base"] != "CNY" or row["quote"] != "VND" or not rate.is_finite() or rate <= 0 or rate > 100_000:
        raise ValueError("Invalid reference rate")
    if when > now().date() or when < now().date() - timedelta(days=40):
        raise ValueError("Reference observation date outside accepted range")
    return when, rate.quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)


def store(db, row):
    when, rate = validate_row(row)
    db.execute(insert(FxObservation).values(rate_date=when, vnd_per_cny=rate, fetched_at=now(), source="FRANKFURTER_REFERENCE").on_conflict_do_update(index_elements=["rate_date"], set_={"vnd_per_cny": rate, "fetched_at": now()}))


def reference_rate(db):
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('frankfurter-cny-vnd'))"))
    latest = db.scalar(select(FxObservation).order_by(FxObservation.rate_date.desc()).limit(1))
    refresh_due = not latest or latest.fetched_at < now() - timedelta(hours=settings.fx_reference_cache_hours)
    stale = False
    if refresh_due:
        try:
            store(db, fetch_json("/rate/CNY/VND"))
            db.flush()
            db.expire_all()
            latest = db.scalar(select(FxObservation).order_by(FxObservation.rate_date.desc()).limit(1))
        except (httpx.HTTPError, ValueError, InvalidOperation, KeyError, TypeError):
            stale = True
    if not latest or latest.rate_date < now().date() - timedelta(days=settings.fx_reference_max_age_days):
        raise ApiError("FX_UNAVAILABLE", "Reference rate unavailable; please retry later", 503)
    return latest, stale


def public_rate(row, stale=False):
    return {"base": "CNY", "quote": "VND", "rate": format(row.vnd_per_cny, ".6f"), "rate_date": row.rate_date.isoformat(), "fetched_at": iso(row.fetched_at), "source": "FRANKFURTER_REFERENCE", "source_url": SOURCE_URL, "is_stale": stale, "notice": "Daily reference rate; not an executable provider FX offer"}


@router.get("/latest")
def latest(user=Depends(student), db=Depends(get_db, scope="function")):
    row, stale = reference_rate(db)
    return public_rate(row, stale)


@router.get("/history")
def history(user=Depends(student), db=Depends(get_db, scope="function")):
    start = now().date() - timedelta(days=14)
    items = list(db.scalars(select(FxObservation).where(FxObservation.rate_date >= start).order_by(FxObservation.rate_date)))
    refresh_due = len(items) < 3 or max((i.fetched_at for i in items), default=now() - timedelta(days=1)) < now() - timedelta(hours=settings.fx_reference_cache_hours)
    stale = False
    if refresh_due:
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext('frankfurter-cny-vnd-history'))"))
        try:
            rows = fetch_json("/rates", {"from": start.isoformat(), "base": "CNY", "quotes": "VND"})
            if not isinstance(rows, list) or len(rows) > 40:
                raise ValueError("Invalid series")
            for row in rows:
                validate_row(row)
            for row in rows:
                store(db, row)
            db.flush()
            db.expire_all()
            items = list(db.scalars(select(FxObservation).where(FxObservation.rate_date >= start).order_by(FxObservation.rate_date)))
        except (httpx.HTTPError, ValueError, InvalidOperation, KeyError, TypeError):
            stale = True
    if not items:
        raise ApiError("FX_UNAVAILABLE", "Reference series unavailable; retry later", 503)
    return {"items": [{"date": i.rate_date.isoformat(), "rate": format(i.vnd_per_cny, ".6f")} for i in items], "source_url": SOURCE_URL, "is_stale": stale}
