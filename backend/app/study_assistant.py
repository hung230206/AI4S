"""One read-only conversation: server routing, source-only RAG and general Gemini."""
import re
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from . import gemini
from .accounts import throttle
from .config import settings
from .db import get_db
from .documents import Search, search_owned
from .finance import AssistantInput, assistant_evidence, workflow_reply
from .models import PolicyDocument, now
from .privacy import require_permission
from .rag import published_source
from .rag_index import normal, retrieve, tokens
from .security import ApiError, student
from .services import audit

router = APIRouter(prefix="/api/v1/study-assistant", tags=["Study-abroad assistant"])
SOURCE_TERMS = ("bao hiem", "boi thuong", "hop dong", "dieu khoan", "tai lieu", "quyen loi", "loai tru", "khau tru", "tai tuc", "thoi gian cho", "ngoai tru", "noi tru", "ho so", "luat", "quy dinh", "insurance", "policy", "policies", "claim", "claims", "coverage", "deductible", "exclusion", "renewal", "waiting period", "regulation", "law", "terms", "outpatient", "inpatient", "hospital", "reimbursement", "premium", "benefits", "khac tinh", "跨省", "异地", "门诊", "han muc", "chi tra", "nam vien", "document", "documents", "nfra", "nhsa", "iac", "picc", "保险", "医保", "理赔", "合同", "条款", "免责", "续保", "法律", "规定", "材料", "健康金福", "人保", "等待", "免赔", "保障", "医疗")
FOLLOWUP = r"^(?:vay|con |the |no |cai do|dieu do|giai thich them|noi ro hon|can nhung gi|what about|and |then|explain that|tell me more|how about|those|that |那|还有|继续|具体|为什么)"
ACTION_TERMS = ("thanh toan ngay", "hay thanh toan", "thanh toan giup", "chuyen tien", "doi tien giup", "please pay", "pay invoice", "pay the", "pay now", "pay my", "transfer money", "exchange my", "convert my", "帮我支付", "转账", "兑换")
ACCOUNT_TERMS = ("hoa don", "invoice", "den han", "du tien", "30 ngay", "so du", "ngan sach cua", "my budget", "my balance", "my wallet", "账单", "余额")
GENERIC_SOURCE_WORDS = set("dieu khoan luat quy dinh tai lieu ban goc thong tin hien tai noi dung".split())
COPY = {
    "vi": {"missing": "Kho tài liệu hiện chưa có đủ chứng cứ để trả lời câu hỏi này. Tôi không suy đoán điều khoản hoặc quyền lợi còn thiếu.", "local": "Các đoạn gốc liên quan để bạn đối chiếu:", "general": "Tôi có thể hỗ trợ câu hỏi về du học, ngân sách và bảo hiểm. Gemini hiện chưa trả lời được; bạn có thể thử lại sau.", "changed": "Nguồn đã thay đổi hoặc được gỡ. Hãy hỏi lại để dùng tài liệu hiện tại.", "notice": "Thông tin để tham khảo và đối chiếu; không thực hiện giao dịch hoặc quyết định quyền lợi."},
    "en": {"missing": "The knowledge base has insufficient evidence for this question. I cannot infer missing terms or benefits.", "local": "Relevant original passages to review:", "general": "I can help with studying abroad, budgets and insurance. Gemini is currently unavailable; please try again later.", "changed": "A source changed or was withdrawn. Ask again to use current documents.", "notice": "Guidance for review; no transaction or coverage decision is performed."},
    "zh": {"missing": "知识库中没有足够证据回答此问题，不能推测缺失条款或保障权益。", "local": "请核对以下相关原文：", "general": "可咨询留学、预算和保险。Gemini 暂不可用，请稍后重试。", "changed": "来源已更新或撤下，请重新提问。", "notice": "仅供参考核对，不执行交易或保障权益决定。"},
}


class StudyChatInput(AssistantInput):
    use_gemini: bool = True


def contains(value, terms):
    return any(term in value if re.search(r"[\u4e00-\u9fff]", term) else re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", value) for term in terms)


def route_question(message, history):
    value = normal(message)
    if contains(value, ACTION_TERMS): return "WORKFLOW", message
    if contains(value, ("cach tai len", "lam sao tai len", "how to upload", "how do i upload", "dang nhap", "上传文件", "登录")): return "GEMINI", message
    if contains(value, SOURCE_TERMS) and not re.search(FOLLOWUP, value): return "RAG", message
    if re.search(FOLLOWUP, value):
        previous = next((turn.content for turn in reversed(history) if turn.role == "user"), "")
        if contains(normal(previous), SOURCE_TERMS):
            # Keep the current question intact; bound combined retrieval context.
            return "RAG", (message + " " + previous)[:1000]
    return ("RAG" if contains(value, SOURCE_TERMS) else "GEMINI"), message


def context(body, request, user, db):
    cloud = body.use_gemini and gemini.configured()
    permission = require_permission(db, request, user, body.privacy_revision) if cloud else None
    history = body.history if permission and "history" in permission.scopes else []
    route, query = route_question(body.message, history)
    if route == "RAG" and cloud and "documents" not in permission.scopes:
        raise ApiError("AI_CONSENT_REQUIRED", "Cần đồng ý quyền dùng đoạn tài liệu trước khi gửi tới Gemini.", 403)
    evidence = []; citations = []
    if route == "RAG":
        allowed = ["TEST_FIXTURE", "PUBLIC_REFERENCE"] if cloud and settings.gemini_data_mode == "DEMO_ONLY" else None
        owned = search_owned(Search(question=query[:500]), user, db, allowed)["matches"][:3]
        shared, _ = retrieve(db, query)
        specific = set(tokens(query)) - GENERIC_SOURCE_WORDS
        # A match on generic words such as 'clause' is not evidence about an
        # otherwise unknown subject. Avoid sending irrelevant search hits.
        if specific:
            shared = [item for item in shared if specific.intersection(item["matched_terms"])]
            owned = [item for item in owned if specific.intersection(tokens(item["excerpt"]))]
        # Private files never enter the shared index. Only allowed owned results
        # and published, current shared revisions may enter this request.
        for item in owned:
            doc = db.get(PolicyDocument, UUID(item["document_id"]))
            citations.append({**item, "sha256": doc.sha256, "origin": "OWNED", "href": "/assistant"})
        citations.extend({**item, "origin": "SHARED", "href": f"/knowledge/{item['document_id']}?revision={item['revision']}#page-{item['page']}"} for item in shared[:3 - len(citations)])
        for index, item in enumerate(citations):
            item["source_id"] = f"R{index + 1}"
            evidence.append({"id": item["source_id"], "kind": "ORIGINAL_DOCUMENT_EXCERPT", "data": {key: item[key] for key in ("title", "page", "excerpt", "document_kind")}})
    elif route == "GEMINI" and permission:
        scopes = {"finance"} & set(permission.scopes) if contains(normal(body.message), ACCOUNT_TERMS) else set()
        evidence, indexed = assistant_evidence(body.message, user, db, scopes)
        citations = list(indexed.values())
    return route, permission, history, evidence, citations


def revalidate(db, request, user, body, citations):
    db.expire_all()
    session = getattr(request.state, "account_session", None)
    if session and (session.revoked or session.expires_at <= now()):
        raise ApiError("UNAUTHORIZED", "Phiên đăng nhập đã hết hiệu lực.", 401)
    require_permission(db, request, user, body.privacy_revision)
    for item in citations:
        if item.get("origin") == "SHARED":
            try: published_source(db, UUID(item["document_id"]), item["revision"])
            except ApiError: return False
        elif item.get("origin") == "OWNED":
            doc = db.get(PolicyDocument, UUID(item["document_id"]))
            if not doc or doc.user_id != user.id or doc.sha256 != item["sha256"]: return False
    return True


@router.post("/preview")
def preview(body: StudyChatInput, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    require_permission(db, request, user, body.privacy_revision)
    route, permission, history, evidence, citations = context(body, request, user, db)
    gemini.ensure_non_sensitive({"question": body.message, "history": [turn.model_dump() for turn in history], "server_evidence": evidence})
    return {"route": route, "recipient": "Google Gemini", "question": body.message, "conversation": [turn.model_dump() for turn in history], "server_evidence": evidence, "sent": False}


@router.post("/chat")
def chat(body: StudyChatInput, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    # Guard execution requests before retrieving or sending any context.
    if contains(normal(body.message), ACTION_TERMS):
        return {**workflow_reply(body, user, db), "route": "WORKFLOW", "provider": "RULES", "fallback_reason": "READ_ONLY_GUARD"}
    route, permission, history, evidence, citations = context(body, request, user, db)
    text = COPY[body.language]
    base = {"route": route, "intent": "DOCUMENT_EVIDENCE" if route == "RAG" else "STUDY_GUIDANCE", "executed_actions": [], "actions": [], "notice": text["notice"]}
    if route == "RAG":
        fallback = {**base, "provider": "EXTRACTIVE", "method": "AUTOMATIC_RAG", "status": "EVIDENCE_FOUND" if citations else "INSUFFICIENT_INFORMATION", "citations": citations,
                    "answer": text["local"] + "\n\n" + "\n\n".join(f"[{item['source_id']}] {item['excerpt']}" for item in citations) if citations else text["missing"]}
        if not citations: return fallback
    else:
        fallback = {**base, "provider": "RULES", "method": "LOCAL_GUIDANCE", "answer": text["general"], "citations": []}
        if contains(normal(body.message), ACCOUNT_TERMS):
            fallback = {**fallback, **workflow_reply(body, user, db)}
            if not permission or "finance" not in permission.scopes or settings.gemini_data_mode == "DEMO_ONLY":
                return {**fallback, "route": "WORKFLOW", "fallback_reason": "ACCOUNT_LOCAL_ONLY"}
    if not permission: return {**fallback, "fallback_reason": "NOT_CONFIGURED" if body.use_gemini else "LOCAL_ONLY"}
    allowed_history = [turn.model_dump() for turn in history]
    gemini.ensure_non_sensitive({"question": body.message, "history": allowed_history, "server_evidence": evidence})
    throttle(db, request, str(user.id), "GEMINI_USER", limit=20)
    throttle(db, request, "all", "GEMINI_APP", limit=60)
    audit(db, user, "AI_REQUEST_DISPATCHED", purpose="UNIFIED_STUDY_ASSISTANT", route=route, notice_version=permission.notice_version, revision=permission.revision, evidence_count=len(evidence), model=settings.gemini_model)
    db.commit()
    try:
        result = gemini.generate(body.message, allowed_history, body.language, evidence)
        selected = set(result.source_ids)
        if not selected <= {item["id"] for item in evidence} or (route == "RAG" and not selected):
            raise gemini.GeminiFailure("UNGROUNDED_RESPONSE")
        reply = {**base, "provider": "GEMINI", "method": "RAG_GEMINI" if route == "RAG" else "GEMINI_GENERAL", "answer": result.answer, "model": result.model_used,
                 "citations": [item for item in citations if item["source_id"] in selected]}
    except gemini.GeminiFailure as error:
        reply = {**fallback, "fallback_reason": error.code}
    if not revalidate(db, request, user, body, citations):
        return {**base, "provider": "EXTRACTIVE", "method": "AUTOMATIC_RAG", "status": "SOURCES_CHANGED", "answer": text["changed"], "citations": [], "fallback_reason": "SOURCES_CHANGED"}
    return reply
