"""Read-only app navigation proposals. Destinations never come from model output."""
import re
from .rag_index import normal


def has(value, terms):
    return any(term in value if re.search(r"[\u4e00-\u9fff]", term) else re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", value) for term in terms)


TITLES = {
    "vi": {"history": "Lịch sử giao dịch", "new_invoice": "Thêm hóa đơn", "invoices": "Hóa đơn", "finance": "Ngân sách", "rates": "Tỷ giá", "documents": "Tài liệu của tôi", "insurance": "Bảo hiểm", "account": "Cài đặt tài khoản"},
    "en": {"history": "Transaction history", "new_invoice": "Add invoice", "invoices": "Invoices", "finance": "Budget", "rates": "Exchange rates", "documents": "My documents", "insurance": "Insurance", "account": "Account settings"},
    "zh": {"history": "交易记录", "new_invoice": "添加账单", "invoices": "账单", "finance": "预算", "rates": "汇率", "documents": "我的文件", "insurance": "保险", "account": "账户设置"},
}
PATHS = {"history": "/history", "new_invoice": "/invoices/new", "invoices": "/invoices", "finance": "/finance", "rates": "/rates", "documents": "/assistant", "insurance": "/insurance", "account": "/account"}
STATUSES = (
    ("SUCCEEDED", ("thanh cong", "successful", "succeeded", "成功")),
    ("FAILED", ("that bai", "failed", "失败")),
    ("PROCESSING", ("dang xu ly", "processing", "处理中")),
    ("CANCELLED", ("da huy", "cancelled", "canceled", "已取消")),
    ("EXPIRED", ("het han", "expired", "已过期")),
    ("AWAITING_CONFIRMATION", ("cho xac nhan", "awaiting confirmation", "待确认")),
)


def navigation_proposal(message, language):
    value = normal(message)
    # Questions about evidence, concepts and negative requests stay in chat.
    if has(value, ("khong", "dung mo", "dung chuyen", "chua muon", "do not", "don't", "dont", "not", "不要", "不想", "别打开")):
        return None
    if has(value, ("la gi", "nghia la", "giai thich", "cach", "lam sao", "what is", "what are", "how do", "how can", "explain", "是什么意思", "什么是", "如何", "解释", "theo luat", "theo quy dinh", "doi chieu", "dieu khoan", "quyen loi", "boi thuong", "tai tuc", "under chinese law", "under the law", "coverage", "renewal", "claim", "条款", "续保", "理赔")):
        return None
    wants = has(value, ("muon", "can", "xem", "mo", "them", "tao", "tai len", "quan ly", "kiem tra", "cho toi", "cho minh", "cho t", "want", "need", "show", "open", "view", "add", "upload", "manage", "check", "想", "需要", "查看", "打开", "添加", "上传", "管理"))
    key = None
    if has(value, ("giao dich", "lich su thanh toan", "transaction", "transactions", "payment history", "交易", "支付记录")) and (wants or has(value, ("nao", "which", "what", "哪些"))):
        key = "history"
    elif wants:
        if has(value, ("thanh toan hoc phi", "dong hoc phi", "pay tuition", "支付学费")):
            key = "invoices"
        elif has(value, ("hoa don", "invoice", "invoices", "账单")):
            key = "new_invoice" if has(value, ("them", "tao", "tai len", "nhap", "add", "create", "upload", "new", "添加", "上传", "新建")) else "invoices"
        elif has(value, ("ngan sach", "thu chi", "so theo doi", "budget", "ledger", "预算", "记账")):
            key = "finance"
        elif has(value, ("ty gia", "exchange rate", "exchange rates", "汇率")):
            key = "rates"
        elif has(value, ("tai lieu", "tep", "document", "documents", "file", "files", "文件", "资料")):
            key = "documents"
        elif has(value, ("cai dat", "tai khoan", "thu hoi quyen", "settings", "account", "withdraw consent", "账户", "设置", "撤回同意")):
            key = "account"
        elif has(value, ("bao hiem", "insurance", "保险")) and has(value, ("mua", "quan ly", "mo", "buy", "manage", "open", "购买", "管理", "打开")):
            key = "insurance"
    if not key:
        return None
    href = PATHS[key]
    if key == "history":
        statuses = [status for status, terms in STATUSES if has(value, terms)]
        if len(statuses) == 1:
            href += "?status=" + statuses[0]
    title = TITLES[language][key]
    reason = {
        "vi": f"Bạn có thể tiếp tục nhu cầu này tại trang {title}.",
        "en": f"You can continue this task on the {title} page.",
        "zh": f"您可以在“{title}”页面继续操作。",
    }[language]
    return {"href": href, "title": title, "reason": reason}


def navigation_reply(proposal, language):
    answer = {"vi": "Bạn muốn mở trang này để tiếp tục không?", "en": "Would you like to open this page to continue?", "zh": "要打开此页面继续吗？"}[language]
    return {"route": "WORKFLOW", "provider": "RULES", "method": "NAVIGATION_SUGGESTION", "intent": "OPEN_APP_PAGE", "answer": proposal["reason"] + " " + answer,
            "navigation": proposal, "actions": [{"title": proposal["title"], "href": proposal["href"]}], "citations": [], "executed_actions": []}
