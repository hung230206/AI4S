"""User-declared multi-currency ledger, scheduled cash flow and bounded guidance."""
import calendar
from datetime import date, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from pydantic import Field, field_validator
from sqlalchemy import select, func
from .db import get_db
from .models import FinanceWallet, FinanceEntry, FinancePlan, Invoice, now
from .schemas import Strict
from .security import student, lock_user, ApiError
from .services import audit, digest, own_invoice
from .fx import reference_rate, public_rate

router = APIRouter(prefix="/api/v1/finance", tags=["Student finance and bounded guidance"])
Currency = Literal["CNY", "VND"]
Category = Literal["TUITION", "INSURANCE", "HOUSING", "FOOD", "TRANSPORT", "HEALTH", "SCHOLARSHIP", "FAMILY", "OTHER"]


def today():
    return now().astimezone(timezone(timedelta(hours=7))).date()


def money(value, currency, positive=True):
    number = Decimal(value)
    unit = Decimal("1") if currency == "VND" else Decimal(".01")
    if number < 0 or (positive and number == 0) or number != number.quantize(unit):
        raise ApiError("MONEY_INVALID", "VND must be integral; CNY supports two decimals and amounts must be positive", 422)
    return number.quantize(unit)


def display(number, currency):
    return format(number, ".0f" if currency == "VND" else ".2f")


class WalletInput(Strict):
    name: str = Field(min_length=2, max_length=80)
    currency: Currency
    opening_balance: str = Field(pattern=r"^\d{1,12}(\.\d{1,2})?$")
    opening_date: date

    @field_validator("name")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Name must contain at least two characters")
        return value.strip()


class EntryInput(Strict):
    wallet_id: UUID
    title: str = Field(min_length=2, max_length=200)
    kind: Literal["INCOME", "EXPENSE"]
    amount: str = Field(pattern=r"^\d{1,12}(\.\d{1,2})?$")
    category: Category = "OTHER"
    occurred_on: date
    request_key: str = Field(min_length=8, max_length=128)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Title must contain at least two characters")
        return value.strip()


class PlanInput(Strict):
    wallet_id: UUID
    title: str = Field(min_length=2, max_length=200)
    kind: Literal["INCOME", "EXPENSE"]
    amount: str = Field(pattern=r"^\d{1,12}(\.\d{1,2})?$")
    category: Category = "OTHER"
    due_date: date
    recurrence: Literal["NONE", "MONTHLY"] = "NONE"

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Title must contain at least two characters")
        return value.strip()


class InvoicePlanInput(Strict):
    wallet_id: UUID
    invoice_id: UUID


class SettleInput(Strict):
    occurrence_date: date
    request_key: str = Field(min_length=8, max_length=128)


def own_wallet(db, wallet_id, user):
    wallet = db.scalar(select(FinanceWallet).where(FinanceWallet.id == wallet_id, FinanceWallet.user_id == user.id))
    if not wallet:
        raise ApiError("WALLET_NOT_FOUND", "Finance wallet not found", 404)
    return wallet


def own_plan(db, plan_id, user):
    plan = db.scalar(select(FinancePlan).where(FinancePlan.id == plan_id, FinancePlan.user_id == user.id))
    if not plan:
        raise ApiError("PLAN_NOT_FOUND", "Scheduled item not found", 404)
    return plan


def balance(db, wallet):
    entries = db.scalars(select(FinanceEntry).where(FinanceEntry.wallet_id == wallet.id, FinanceEntry.status == "POSTED", FinanceEntry.occurred_on <= today()))
    return wallet.opening_balance + sum((entry.amount if entry.kind == "INCOME" else -entry.amount for entry in entries), Decimal("0"))


def wallet_out(db, wallet):
    return {"id": str(wallet.id), "name": wallet.name, "currency": wallet.currency, "opening_balance": display(wallet.opening_balance, wallet.currency), "opening_date": wallet.opening_date.isoformat(), "balance": display(balance(db, wallet), wallet.currency), "source": "USER_DECLARED", "holds_real_funds": False}


def entry_out(entry, wallet):
    return {"id": str(entry.id), "wallet_id": str(entry.wallet_id), "wallet_name": wallet.name, "currency": wallet.currency, "title": entry.title, "kind": entry.kind, "amount": display(entry.amount, wallet.currency), "category": entry.category, "occurred_on": entry.occurred_on.isoformat(), "status": entry.status, "source": "USER_CONFIRMED_PLAN" if entry.plan_id else "USER_ENTERED", "plan_id": str(entry.plan_id) if entry.plan_id else None}


def plan_out(plan, wallet):
    return {"id": str(plan.id), "wallet_id": str(plan.wallet_id), "wallet_name": wallet.name, "currency": wallet.currency, "title": plan.title, "kind": plan.kind, "amount": display(plan.amount, wallet.currency), "category": plan.category, "due_date": plan.due_date.isoformat(), "recurrence": plan.recurrence, "active": plan.active, "invoice_id": str(plan.invoice_id) if plan.invoice_id else None, "source": "INVOICE_SNAPSHOT" if plan.invoice_id else "USER_PLANNED"}


def occurrence_dates(plan, until):
    when = plan.due_date
    while when <= until:
        yield when
        if plan.recurrence == "NONE":
            break
        month = when.month % 12 + 1
        year = when.year + (when.month == 12)
        when = date(year, month, min(plan.due_date.day, calendar.monthrange(year, month)[1]))


@router.get("/wallets")
def wallets(user=Depends(student), db=Depends(get_db, scope="function")):
    return {"items": [wallet_out(db, w) for w in db.scalars(select(FinanceWallet).where(FinanceWallet.user_id == user.id).order_by(FinanceWallet.created_at))]}


@router.post("/wallets")
def create_wallet(body: WalletInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    if not today() - timedelta(days=730) <= body.opening_date <= today():
        raise ApiError("DATE_INVALID", "Opening date must be within the past two years", 422)
    if db.scalar(select(FinanceWallet).where(FinanceWallet.user_id == user.id, FinanceWallet.name == body.name)):
        raise ApiError("WALLET_NAME_EXISTS", "Wallet name already exists", 409)
    if db.scalar(select(func.count()).select_from(FinanceWallet).where(FinanceWallet.user_id == user.id)) >= 20:
        raise ApiError("WALLET_LIMIT", "Maximum 20 finance wallets", 409)
    wallet = FinanceWallet(user_id=user.id, name=body.name, currency=body.currency, opening_balance=money(body.opening_balance, body.currency, False), opening_date=body.opening_date)
    db.add(wallet); db.flush()
    audit(db, user, "FINANCE_WALLET_CREATED", wallet_id=str(wallet.id))
    return wallet_out(db, wallet)


@router.get("/entries")
def entries(user=Depends(student), db=Depends(get_db, scope="function")):
    rows = db.execute(select(FinanceEntry, FinanceWallet).join(FinanceWallet, FinanceEntry.wallet_id == FinanceWallet.id).where(FinanceEntry.user_id == user.id).order_by(FinanceEntry.occurred_on.desc(), FinanceEntry.created_at.desc()).limit(1000))
    return {"items": [entry_out(e, w) for e, w in rows]}


def replay_entry(db, user, key, request_hash):
    old = db.scalar(select(FinanceEntry).where(FinanceEntry.user_id == user.id, FinanceEntry.request_key == key))
    if old and old.request_hash != request_hash:
        raise ApiError("IDEMPOTENCY_CONFLICT", "Request key was used for different entry data", 409)
    return old


@router.post("/entries")
def create_entry(body: EntryInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    wallet = own_wallet(db, body.wallet_id, user)
    request_hash = digest(body.model_dump(mode="json"))
    old = replay_entry(db, user, body.request_key, request_hash)
    if old:
        return entry_out(old, wallet)
    if not wallet.opening_date <= body.occurred_on <= today():
        raise ApiError("DATE_INVALID", "Actual entry date must be between opening date and today; use a plan for future items", 422)
    values = body.model_dump(exclude={"request_key", "amount"})
    entry = FinanceEntry(user_id=user.id, **values, amount=money(body.amount, wallet.currency), status="POSTED", request_key=body.request_key, request_hash=request_hash)
    db.add(entry); db.flush()
    audit(db, user, "FINANCE_ENTRY_POSTED", entry_id=str(entry.id))
    return entry_out(entry, wallet)


@router.post("/entries/{entry_id}/void")
def void_entry(entry_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    entry = db.scalar(select(FinanceEntry).where(FinanceEntry.id == entry_id, FinanceEntry.user_id == user.id))
    if not entry:
        raise ApiError("ENTRY_NOT_FOUND", "Entry not found", 404)
    entry.status = "VOID"
    audit(db, user, "FINANCE_ENTRY_VOIDED", entry_id=str(entry.id))
    return entry_out(entry, own_wallet(db, entry.wallet_id, user))


@router.get("/plans")
def plans(user=Depends(student), db=Depends(get_db, scope="function")):
    rows = db.execute(select(FinancePlan, FinanceWallet).join(FinanceWallet, FinancePlan.wallet_id == FinanceWallet.id).where(FinancePlan.user_id == user.id).order_by(FinancePlan.due_date))
    return {"items": [plan_out(p, w) for p, w in rows]}


@router.post("/plans")
def create_plan(body: PlanInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    wallet = own_wallet(db, body.wallet_id, user)
    if not wallet.opening_date <= body.due_date <= today() + timedelta(days=730):
        raise ApiError("DATE_INVALID", "Plan date is outside wallet lifetime / two-year planning range", 422)
    if db.scalar(select(func.count()).select_from(FinancePlan).where(FinancePlan.user_id == user.id, FinancePlan.active == True)) >= 100:
        raise ApiError("PLAN_LIMIT", "Maximum 100 active plans", 409)
    values = body.model_dump(exclude={"amount"})
    plan = FinancePlan(user_id=user.id, **values, amount=money(body.amount, wallet.currency))
    db.add(plan); db.flush()
    audit(db, user, "FINANCE_PLAN_CREATED", plan_id=str(plan.id))
    return plan_out(plan, wallet)


@router.post("/plans/from-invoice")
def invoice_plan(body: InvoicePlanInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    wallet = own_wallet(db, body.wallet_id, user)
    invoice = own_invoice(db, body.invoice_id, user)
    if wallet.currency != "CNY" or invoice.status != "OPEN" or invoice.due_date < wallet.opening_date:
        raise ApiError("PLAN_INVOICE_INVALID", "Choose a CNY wallet opened before the due date and an open invoice", 422)
    old = db.scalar(select(FinancePlan).where(FinancePlan.invoice_id == invoice.id))
    if old:
        if old.wallet_id != wallet.id or not old.active:
            raise ApiError("PLAN_ALREADY_EXISTS", "This invoice already has a plan; view the existing plan", 409)
        return plan_out(old, wallet)
    plan = FinancePlan(user_id=user.id, wallet_id=wallet.id, title=f"Hóa đơn {invoice.invoice_number}", kind="EXPENSE", amount=invoice.amount_cny, category="INSURANCE" if "INSURANCE" in invoice.fee_type else "OTHER", due_date=invoice.due_date, recurrence="NONE", invoice_id=invoice.id)
    db.add(plan); db.flush()
    audit(db, user, "INVOICE_PLANNED", invoice_id=str(invoice.id), plan_id=str(plan.id))
    return plan_out(plan, wallet)


@router.post("/plans/{plan_id}/stop")
def stop_plan(plan_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    plan = own_plan(db, plan_id, user)
    plan.active = False
    audit(db, user, "FINANCE_PLAN_STOPPED", plan_id=str(plan.id))
    return plan_out(plan, own_wallet(db, plan.wallet_id, user))


@router.post("/plans/{plan_id}/settle")
def settle_plan(plan_id: UUID, body: SettleInput, user=Depends(student), db=Depends(get_db, scope="function")):
    lock_user(db, user)
    plan = own_plan(db, plan_id, user)
    wallet = own_wallet(db, plan.wallet_id, user)
    request_hash = digest({"plan_id": str(plan_id), **body.model_dump(mode="json")})
    old = replay_entry(db, user, body.request_key, request_hash)
    if old:
        return entry_out(old, wallet)
    if not plan.active or body.occurrence_date > today() + timedelta(days=90) or body.occurrence_date not in occurrence_dates(plan, body.occurrence_date):
        raise ApiError("PLAN_OCCURRENCE_INVALID", "Invalid scheduled occurrence", 422)
    posted = db.scalar(select(FinanceEntry).where(FinanceEntry.plan_id == plan.id, FinanceEntry.scheduled_date == body.occurrence_date, FinanceEntry.status == "POSTED"))
    if posted:
        return entry_out(posted, wallet)
    entry = FinanceEntry(user_id=user.id, wallet_id=wallet.id, title=plan.title, kind=plan.kind, amount=plan.amount, category=plan.category, occurred_on=today(), plan_id=plan.id, scheduled_date=body.occurrence_date, status="POSTED", request_key=body.request_key, request_hash=request_hash)
    db.add(entry); db.flush()
    audit(db, user, "PLANNED_CASHFLOW_USER_CONFIRMED", entry_id=str(entry.id), plan_id=str(plan.id))
    return entry_out(entry, wallet)


@router.get("/forecast")
def forecast(days: int = Query(default=30, ge=7, le=90), user=Depends(student), db=Depends(get_db, scope="function")):
    start = today(); end = start + timedelta(days=days)
    wallets = list(db.scalars(select(FinanceWallet).where(FinanceWallet.user_id == user.id).order_by(FinanceWallet.created_at)))
    rates = None; rate_error = None
    try:
        row, stale = reference_rate(db)
        rates = public_rate(row, stale)
    except ApiError:
        rate_error = "Chưa có tỷ giá đủ mới. Vẫn hiển thị dự phóng theo nguyên tệ."
    settled = {(e.plan_id, e.scheduled_date) for e in db.scalars(select(FinanceEntry).where(FinanceEntry.user_id == user.id, FinanceEntry.plan_id.is_not(None), FinanceEntry.status == "POSTED"))}
    events = []
    by_wallet = {w.id: w for w in wallets}
    for plan in db.scalars(select(FinancePlan).where(FinancePlan.user_id == user.id, FinancePlan.active == True)):
        wallet = by_wallet[plan.wallet_id]
        for due in occurrence_dates(plan, end):
            if (plan.id, due) not in settled:
                events.append({"plan_id": str(plan.id), "wallet_id": str(wallet.id), "wallet_name": wallet.name, "title": plan.title, "kind": plan.kind, "amount": display(plan.amount, wallet.currency), "currency": wallet.currency, "due_date": due.isoformat(), "effective_date": max(start, due).isoformat(), "overdue": due < start, "source": "INVOICE_SNAPSHOT" if plan.invoice_id else "USER_PLANNED"})
    events.sort(key=lambda e: (e["effective_date"], e["kind"] == "INCOME", e["title"]))
    result = []; totals = {"CNY": Decimal("0"), "VND": Decimal("0")}
    for wallet in wallets:
        current = balance(db, wallet); running = current; points = []; first_negative = None; minimum = current
        for offset in range(days + 1):
            when = start + timedelta(days=offset)
            for event in events:
                if event["wallet_id"] == str(wallet.id) and event["effective_date"] == when.isoformat():
                    running += Decimal(event["amount"]) * (1 if event["kind"] == "INCOME" else -1)
            minimum = min(minimum, running)
            if running < 0 and first_negative is None:
                first_negative = when.isoformat()
            points.append({"date": when.isoformat(), "balance": display(running, wallet.currency)})
        totals[wallet.currency] += running
        result.append({"wallet_id": str(wallet.id), "name": wallet.name, "currency": wallet.currency, "current_balance": display(current, wallet.currency), "projected_balance": display(running, wallet.currency), "minimum_balance": display(minimum, wallet.currency), "first_shortfall_date": first_negative, "points": points})
    value_vnd = None
    if rates:
        value_vnd = format((totals["VND"] + totals["CNY"] * Decimal(rates["rate"])).quantize(Decimal("1"), rounding=ROUND_HALF_UP), ".0f")
    advice = []
    if not wallets:
        advice.append({"code": "ADD_WALLET", "title": "Khai báo số dư để bắt đầu", "detail": "Thêm sổ CNY hoặc VND và số dư bạn đang theo dõi.", "href": "/finance", "severity": "info"})
    for wallet in result:
        if wallet["first_shortfall_date"]:
            advice.append({"code": "CASH_SHORTFALL", "title": f"{wallet['name']}: có thể thiếu tiền từ {wallet['first_shortfall_date']}", "detail": f"Số dư thấp nhất dự phóng: {wallet['minimum_balance']} {wallet['currency']}. Đối chiếu lịch thu/chi hoặc bổ sung nguồn tiền; app không tự đổi hay chuyển tiền.", "href": "/finance", "severity": "warning"})
    if any(e["overdue"] for e in events):
        advice.append({"code": "OVERDUE_PLAN", "title": "Có khoản đã đến hạn chưa được ghi nhận", "detail": "Kiểm tra thực tế trước khi đánh dấu đã thu/chi. Các khoản quá hạn đang được đưa vào ngày đầu dự phóng.", "href": "/finance", "severity": "warning"})
    if wallets and not events:
        advice.append({"code": "ADD_PLANS", "title": "Bổ sung lịch thu và khoản phải trả", "detail": "Nhập tiền nhà, học phí, trợ cấp hoặc đưa hóa đơn đã lưu vào kế hoạch để có dự phóng hữu ích.", "href": "/finance", "severity": "info"})
    return {"from": start.isoformat(), "to": end.isoformat(), "days": days, "wallets": result, "events": events, "totals": {currency: display(value, currency) for currency, value in totals.items()}, "projected_value_vnd": value_vnd, "reference_rate": rates, "rate_error": rate_error, "recommendations": advice, "method": "SCHEDULED_CASHFLOW", "notice": "Dự phóng từ số dư và lịch thu/chi bạn khai báo, không phải dự đoán tỷ giá. Không tự cộng hóa đơn hoặc thanh toán sandbox vào sổ."}


class FxAnalysisInput(Strict):
    amount_cny: str = Field(pattern=r"^\d{1,12}(\.\d{1,2})?$")
    budget_vnd: str | None = Field(default=None, pattern=r"^\d{1,15}$")


@router.post("/fx-analysis")
def fx_analysis(body: FxAnalysisInput, user=Depends(student), db=Depends(get_db, scope="function")):
    amount = money(body.amount_cny, "CNY")
    budget = Decimal(body.budget_vnd) if body.budget_vnd else None
    row, stale = reference_rate(db)
    scenarios = []
    for change in (-5, 0, 5):
        rate = (row.vnd_per_cny * (Decimal("1") + Decimal(change) / 100)).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        cost = (amount * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        scenarios.append({"change_percent": change, "rate": format(rate, ".6f"), "cost_vnd": format(cost, ".0f"), "remaining_budget_vnd": format(budget - cost, ".0f") if budget is not None else None})
    return {"amount_cny": display(amount, "CNY"), "budget_vnd": body.budget_vnd, "reference_rate": public_rate(row, stale), "scenarios": scenarios, "budget_rate_threshold": format((budget / amount).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP), ".6f") if budget is not None else None, "notice": "Kịch bản tác động ±5%, không phải dự báo hoặc khuyến nghị đổi tiền. Chưa gồm phí nhà cung cấp."}


class ChatTurn(Strict):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AssistantInput(Strict):
    message: str = Field(min_length=2, max_length=500)
    use_gemini: bool = False
    language: Literal["vi", "en", "zh"] = "vi"
    history: list[ChatTurn] = Field(default_factory=list, max_length=6)
    privacy_revision: int | None = Field(default=None, ge=1)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Question must contain at least two characters")
        return value.strip()


def workflow_reply(body, user, db):
    from .documents import normalize, search, Search
    message = normalize(body.message)
    response = {"method": "GROUNDED_WORKFLOW", "executed_actions": [], "citations": [], "actions": [], "notice": "Trả lời từ dữ liệu đã lưu và quy tắc có thể kiểm tra; không dùng mô hình sinh văn bản. Không thực hiện hành động tài chính."}
    if any(term in message for term in ("thanh toan", "chuyen tien", "doi tien", "pay ", "transfer", "exchange my", "convert my", "支付", "付款", "转账", "兑换")):
        response.update({"intent": "PAYMENT_REVIEW", "answer": "Tôi có thể giúp bạn kiểm tra hóa đơn và số tiền. Hãy mở hóa đơn, xem báo giá rồi tự xác nhận nếu muốn thử sandbox. Tôi không tự chuyển tiền, đổi tiền hoặc xác nhận thay bạn.", "actions": [{"title": "Mở hóa đơn để kiểm tra", "href": "/invoices"}, {"title": "Theo dõi giao dịch đã tạo", "href": "/history"}]})
    elif any(term in message for term in ("ty gia", "exchange", "vnd", "ngoai te")):
        row, stale = reference_rate(db)
        response.update({"intent": "REFERENCE_FX", "answer": f"Tham chiếu ngày {row.rate_date}: 1 CNY = {format(row.vnd_per_cny, '.6f')} VND. Bạn có thể nhập khoản phí và ngân sách để xem tác động tăng/giảm 5%. Đây không phải dự báo hoặc cam kết đổi tiền.", "citations": [{"title": "Frankfurter · " + row.rate_date.isoformat(), "url": "https://frankfurter.dev/", "is_stale": stale}], "actions": [{"title": "Phân tích khoản phí với tỷ giá", "href": "/rates"}]})
    elif any(term in message for term in ("bao hiem", "boi thuong", "loai tru", "claim", "policy", "coverage", "理赔", "保险", "ho so")):
        result = search(Search(question=body.message), user, db)
        citations = [{"title": item["title"], "filename": item["filename"], "page": item["page"], "excerpt": item["excerpt"], "document_id": item["document_id"]} for item in result["matches"]]
        from .insurance import overview
        portfolio = overview(user, db)
        summary = f" Bạn có {portfolio['active_policies']} bản tóm tắt hợp đồng đang hoạt động và {len(portfolio['reminders'])} mục cần xem lại."
        response.update({"intent": "POLICY_EVIDENCE", "answer": ("Tôi tìm thấy các đoạn liên quan dưới đây. Đọc toàn văn tại trang được dẫn trước khi kết luận; đây không phải quyết định quyền lợi hay bồi thường." if citations else "Chưa có chứng cứ phù hợp trong tài liệu của bạn. Tải chính sách lên hoặc thử từ khóa xuất hiện trong bản gốc; tôi không suy đoán quyền lợi còn thiếu.") + summary, "citations": citations, "actions": [{"title": "Kiểm tra quyền lợi và chuẩn bị hồ sơ", "href": "/insurance"}, {"title": "Mở tài liệu bảo hiểm", "href": "/assistant"}]})
    elif any(term in message for term in ("den han", "hoa don", "invoice", "hoc phi")):
        invoices = list(db.scalars(select(Invoice).where(Invoice.student_id == user.id, Invoice.status == "OPEN").order_by(Invoice.due_date).limit(5)))
        response.update({"intent": "DUE_INVOICES", "answer": "Các hóa đơn đang mở gần hạn nhất trong dữ liệu bạn đã lưu:" if invoices else "Bạn chưa có hóa đơn đang mở. Có thể tải ảnh/PDF để đọc thông tin rồi kiểm tra trước khi lưu.", "citations": [{"title": f"{i.invoice_number}: {display(i.amount_cny, 'CNY')} CNY · hạn {i.due_date}", "href": f"/invoices/{i.id}"} for i in invoices], "actions": [{"title": "Đọc hoặc thêm hóa đơn", "href": "/invoices/new"}]})
    else:
        data = forecast(30, user, db)
        shortfalls = [w for w in data["wallets"] if w["first_shortfall_date"]]
        answer = "Chưa có số dư để phân tích. Hãy khai báo sổ CNY/VND, sau đó thêm lịch thu/chi."
        if data["wallets"]:
            answer = "Trong lịch 30 ngày đã nhập, " + ("có thể thiếu hụt ở: " + "; ".join(f"{w['name']} từ {w['first_shortfall_date']} (thấp nhất {w['minimum_balance']} {w['currency']})" for w in shortfalls) if shortfalls else "chưa thấy số dư âm vào cuối ngày. Kết quả chỉ bao gồm những khoản bạn đã khai báo; kiểm tra xem đã nhập đủ chi phí chưa.")
        response.update({"intent": "BUDGET_NEXT_STEP", "answer": answer, "recommendations": data["recommendations"], "citations": [{"title": f"{w['name']}: hiện {w['current_balance']} {w['currency']}, cuối kỳ {w['projected_balance']} {w['currency']}", "href": "/finance"} for w in data["wallets"]], "actions": [{"title": "Kiểm tra ngân sách và lịch thu chi", "href": "/finance"}, {"title": "Thêm khoản phí từ chứng từ", "href": "/invoices/new"}]})
    return response


@router.get("/assistant/status")
def assistant_status(user=Depends(student)):
    from .gemini import configured
    from .config import settings
    return {"gemini_configured": configured(), "model": settings.gemini_model if configured() else None, "read_only": True, "history_stored": False}


def assistant_evidence(question, user, db, scopes=None):
    from .documents import search, Search
    from .config import settings
    scopes = set(scopes or [])
    if settings.gemini_data_mode == "DEMO_ONLY":
        scopes -= {"finance", "insurance"}
    data = forecast(30, user, db) if "finance" in scopes else None
    evidence = []; citations = {}

    def add(source_id, kind, facts, citation):
        evidence.append({"id": source_id, "kind": kind, "data": facts})
        citations[source_id] = {"source_id": source_id, **citation}

    add("G1", "APP_GUIDE", {"description": "Demo: read-only student finance and insurance guidance; original files, health records, identifiers and credentials are never sent to the model.", "sandbox_only": True}, {"title": "Hướng dẫn Demo", "href": "/copilot"})
    for index, wallet in enumerate(data["wallets"][:8] if data else []):
        facts = {key: wallet[key] for key in ("name", "currency", "current_balance", "projected_balance", "minimum_balance", "first_shortfall_date")}
        facts.update({"from": data["from"], "to": data["to"], "basis": "User-declared ledger and schedules; no bank connection"})
        add(f"B{index + 1}", "BUDGET", facts, {"title": f"{wallet['name']}: {wallet['current_balance']} → {wallet['projected_balance']} {wallet['currency']}", "href": "/finance"})
    if data:
        add("A1", "ACCOUNT_DATA_AVAILABILITY", {"wallet_count": len(data["wallets"]), "budget_days": 30, "notice": data["notice"], "upcoming_events": [{key: item[key] for key in ("title", "kind", "amount", "currency", "due_date")} for item in data["events"][:5]]}, {"title": "Ngân sách · dữ liệu do bạn khai báo", "href": "/finance"})
    if data and data["reference_rate"]:
        rate = data["reference_rate"]
        add("F1", "DAILY_REFERENCE_FX", {key: rate[key] for key in ("rate", "rate_date", "is_stale", "notice")}, {"title": "Frankfurter · " + rate["rate_date"], "url": "https://frankfurter.dev/"})
    invoices = list(db.scalars(select(Invoice).where(Invoice.student_id == user.id, Invoice.status == "OPEN").order_by(Invoice.due_date).limit(5))) if "finance" in scopes else []
    for index, invoice in enumerate(invoices):
        add(f"I{index + 1}", "OPEN_INVOICE", {"amount_cny": display(invoice.amount_cny, "CNY"), "due_date": invoice.due_date.isoformat(), "fee_type": invoice.fee_type, "source_type": invoice.source_type}, {"title": f"{invoice.invoice_number}: {display(invoice.amount_cny, 'CNY')} CNY · {invoice.due_date}", "href": f"/invoices/{invoice.id}"})
    from .documents import search_owned
    from .config import settings
    result = search_owned(Search(question=question), user, db, ["TEST_FIXTURE", "PUBLIC_REFERENCE"] if settings.gemini_data_mode == "DEMO_ONLY" or not {"finance", "insurance"} & set(scopes) else None) if "documents" in scopes else {"matches": []}
    for index, item in enumerate(result["matches"][:3]):
        add(f"D{index + 1}", "ORIGINAL_DOCUMENT_EXCERPT", {"title": item["title"][:160], "page": item["page"], "excerpt": item["excerpt"], "document_kind": item["document_kind"]}, {key: item[key] for key in ("title", "filename", "page", "excerpt", "document_id", "document_kind")})
    from .models import InsurancePolicy
    policies = db.scalars(select(InsurancePolicy).where(InsurancePolicy.user_id == user.id, InsurancePolicy.active == True).order_by(InsurancePolicy.created_at.desc()).limit(3)) if "insurance" in scopes else []
    for index, policy in enumerate(policies):
        add(f"P{index + 1}", "USER_REVIEWED_POLICY_SUMMARY", {"starts_on": str(policy.starts_on), "ends_on": str(policy.ends_on), "premium": display(policy.premium, policy.currency), "currency": policy.currency, "premium_due": str(policy.premium_due), "territory": policy.territory, "benefits": policy.benefits, "revision": policy.revision, "notice": "User-reviewed summary, not verified insurance cover or claim approval."}, {"title": "Bản tóm tắt hợp đồng · " + str(policy.ends_on), "href": "/insurance"})
    return evidence, citations


def cloud_context(body, request, user, db):
    from .privacy import require_permission
    from .gemini import ensure_non_sensitive
    row = require_permission(db, request, user, body.privacy_revision)
    history = [turn.model_dump() for turn in body.history] if "history" in row.scopes else []
    previous = [turn["content"] for turn in history if turn["role"] == "user"]
    question = " ".join([body.message, *previous[-1:]])[:500]
    evidence, citations = assistant_evidence(question, user, db, row.scopes)
    ensure_non_sensitive({"question": body.message, "conversation": history, "server_evidence": evidence})
    return row, history, evidence, citations


@router.post("/assistant/preview")
def preview_assistant(body: AssistantInput, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    row, history, evidence, _ = cloud_context(body, request, user, db)
    return {"recipient": "Google Gemini", "privacy_revision": row.revision, "scopes": row.scopes,
            "question": body.message, "conversation": history, "server_evidence": evidence,
            "notice": "Xem trước tại thời điểm này; không gọi Gemini. Dữ liệu có thể đổi nếu bạn chỉnh sửa trước khi gửi."}


@router.post("/assistant")
def assistant(body: AssistantInput, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    from . import gemini
    from .accounts import throttle
    from .config import settings
    try:
        fallback = workflow_reply(body, user, db)
    except ApiError as exc:
        if exc.code != "FX_UNAVAILABLE":
            raise
        fallback = {"method": "GROUNDED_WORKFLOW", "intent": "REFERENCE_FX", "answer": "Chưa có tỷ giá đủ mới để đối chiếu. Hãy mở trang tỷ giá và thử lại sau.", "citations": [], "actions": [{"title": "Mở tỷ giá", "href": "/rates"}], "executed_actions": [], "notice": "Không thực hiện hành động tài chính."}
    if not body.use_gemini:
        return fallback
    # A request to act never reaches the language model or payment/ledger write APIs.
    if fallback["intent"] == "PAYMENT_REVIEW":
        return {**fallback, "provider": "RULES", "fallback_reason": "READ_ONLY_GUARD"}
    if not gemini.configured():
        return {**fallback, "provider": "RULES", "fallback_reason": "NOT_CONFIGURED"}
    row, history, evidence, citations = cloud_context(body, request, user, db)
    throttle(db, request, str(user.id), "GEMINI_USER", limit=20)
    throttle(db, request, "all", "GEMINI_APP", limit=60)
    audit(db, user, "AI_REQUEST_DISPATCHED", notice_version=row.notice_version, revision=row.revision,
          scopes=row.scopes, data_mode=row.data_mode, model=settings.gemini_model, evidence_count=len(evidence))
    # Release DB/advisory locks before waiting on the external model. Only bounded
    # usage counters and reference-rate cache writes have been made here.
    db.commit()
    try:
        result = gemini.generate(body.message, history, body.language, evidence)
        selected = list(dict.fromkeys(result.source_ids))
        return {"method": "GEMINI_GROUNDED", "provider": "GEMINI", "model": settings.gemini_model, "intent": fallback["intent"], "answer": result.answer,
                "citations": [citations[source_id] for source_id in selected], "actions": fallback["actions"], "executed_actions": [],
                "notice": "Gemini diễn giải dữ liệu tham chiếu; hãy đối chiếu nguồn. Không thực hiện hành động tài chính."}
    except gemini.GeminiFailure as exc:
        return {**fallback, "provider": "RULES", "fallback_reason": exc.code}
