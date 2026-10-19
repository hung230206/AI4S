
import {requestFileConsent, fileConsentHeader} from "./file-consent";
import {tr, localized, localeTag} from "@/lib/i18n";
// Same-origin by default: friends on LAN must never call their own localhost.
export const API = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export function requestKey(): string {
  // randomUUID needs HTTPS/localhost; getRandomValues also works on HTTP LAN.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
export type Invoice = {id: string; invoice_number: string; institution_name: string; beneficiary_name: string; amount_cny: string; due_date: string; country_code: string; source_type: "SYNTHETIC" | "USER_ENTERED"; status: "OPEN" | "VOID"; notes: string; source_url: string | null; fee_type: string};
export const feeLabels: Record<string, string> = localized({ANNUAL_HEALTH_INSURANCE_PREMIUM: "Bảo hiểm sức khỏe du học", MEDICAL_SERVICE_FEE: "Phí dịch vụ y tế", OTHER_INSURANCE_FEE: "Phí bảo hiểm khác", TUITION: "Học phí", ACCOMMODATION: "Phí chỗ ở", OTHER_STUDENT_FEE: "Khoản phí du học khác"});
export type Quote = {id: string; source_amount_cny: string; vnd_per_cny: string; converted_subtotal_vnd: string; variable_fee_rate_percent: string; variable_fee_vnd: string; fixed_fee_vnd: string; total_vnd: string; expires_at: string; rate_source: "DEMO_FIXED" | "FRANKFURTER_REFERENCE"; rate_date: string | null; rate_fetched_at: string | null; rate_is_stale: boolean};
export type Account = {id: string; email: string | null; display_name: string; role: string; is_demo: boolean; created_at: string};
export type AccountSession = {user: Account; csrf_token: string; expires_at: string};
export const documentKinds: Record<string, string> = localized({USER_PROVIDED: "Tài liệu do bạn cung cấp", PUBLIC_REFERENCE: "Tài liệu tham khảo công khai", TEST_FIXTURE: "Dữ liệu mẫu tự soạn"});
export type Policy = {document_kind: string; id: string; title: string; filename: string; page_count: number; byte_size: number; source_url: string | null; created_at: string};
export type ReferenceRate = {rate: string; rate_date: string; fetched_at: string; source_url: string; is_stale: boolean; base: string; quote: string};
export type Status = "AWAITING_CONFIRMATION" | "PROCESSING" | "SUCCEEDED" | "FAILED" | "CANCELLED" | "EXPIRED";
export type SandboxScenario = "SUCCESS" | "DECLINED" | "MANUAL";
export type Order = {id: string; invoice_id: string; quote_id: string; amount_cny: string; total_vnd: string; status: Status; created_at: string; consent_at: string | null; quote?: Quote; sandbox_scenario: SandboxScenario};
export type EventLog = {external_event_id: string; provider_status: string; received_at: string; processing_outcome: string; signature_verified: boolean};
export type Trace = {items: EventLog[]; audit: {action: string; actor_type: string; created_at: string}[]};
export type Receipt = {receipt_number: string; order_id: string; notice: string; issued_at: string; total_vnd: string; amount_cny: string; invoice_number: string};

export async function api<T>(path: string, token: string, body?: unknown, key?: string): Promise<T> {
  const response = await fetch(`${API}/api/v1${path}`, {method: body === undefined ? "GET" : "POST", credentials: "include", headers: {"Content-Type": "application/json", ...authHeaders(token), ...(key ? {"Idempotency-Key": key} : {})}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  const result = await response.json();
  if (!response.ok) {
    const messages: Record<string, string> = {QUOTE_EXPIRED: tr("Báo giá đã hết hạn. Hãy lấy báo giá mới."), INVOICE_NOT_PAYABLE: tr("Hóa đơn đã có giao dịch đang xử lý hoặc đã hoàn tất mô phỏng. Xem lịch sử."), ORDER_STATE_INVALID: tr("Trạng thái giao dịch không cho phép thao tác này."), FORBIDDEN: tr("Không có quyền truy cập hoặc mã vận hành không đúng."), UNAUTHORIZED: tr("Phiên demo đã hết hạn. Tải lại trang để vào phiên mới."), QUOTE_MISMATCH: tr("Báo giá không khớp. Hãy kiểm tra và lấy báo giá mới."), PROVIDER_TEMPORARILY_UNAVAILABLE: tr("Nhà cung cấp mô phỏng tạm thời gián đoạn. Có thể thử lại.")};
    Object.assign(messages, {UNAUTHORIZED: tr("Hãy đăng nhập để tiếp tục."), INVALID_CREDENTIALS: tr("Email hoặc mật khẩu chưa đúng."), EMAIL_EXISTS: tr("Email này đã được đăng ký."), RATE_LIMITED: tr("Bạn đã thử quá nhiều lần. Vui lòng thử lại sau 15 phút."), CSRF_INVALID: tr("Phiên bảo mật cần cập nhật. Hãy tải lại trang."), INVOICE_LOCKED: tr("Hãy hủy giao dịch chờ xác nhận trước khi sửa. Giao dịch đang xử lý hoặc đã thành công sẽ khóa hóa đơn."), INVOICE_NUMBER_EXISTS: tr("Mã hóa đơn này đã tồn tại trong tài khoản."), FX_UNAVAILABLE: tr("Chưa lấy được tỷ giá tham chiếu. Hãy thử lại sau."), DOCUMENT_NO_TEXT: tr("Tệp không có văn bản đọc được. Hãy dùng ảnh rõ hơn, PDF có chữ hoặc tệp TXT."), DOCUMENT_TOO_LARGE: tr("Tệp vượt giới hạn 5 MB, 50 trang hoặc 500.000 ký tự."), DOCUMENT_TYPE_UNSUPPORTED: tr("Hãy dùng PDF, ảnh PNG/JPG/WebP, TXT hoặc MD."), PAYMENT_NOT_CONFIGURED: tr("Chưa kết nối tài khoản nhà cung cấp thanh toán.")});
    Object.assign(messages, {MONEY_INVALID: tr("Số tiền chưa hợp lệ: VND dùng số nguyên, CNY tối đa 2 chữ số thập phân."), DATE_INVALID: tr("Ngày chưa hợp lệ. Ngày thực tế phải từ ngày mở sổ đến hôm nay; khoản tương lai cần lưu vào kế hoạch."), WALLET_NAME_EXISTS: tr("Tên sổ này đã tồn tại. Chọn tên khác để phân biệt."), WALLET_NOT_FOUND: tr("Không tìm thấy sổ tiền trong tài khoản của bạn."), PLAN_OCCURRENCE_INVALID: tr("Kỳ thu / chi này không còn hợp lệ. Hãy làm mới kế hoạch."), PLAN_INVOICE_INVALID: tr("Cần sổ CNY mở trước hạn hóa đơn và hóa đơn đang mở."), PLAN_ALREADY_EXISTS: tr("Hóa đơn đã có kế hoạch. Kiểm tra kế hoạch hiện có trong Ngân sách."), IDEMPOTENCY_CONFLICT: tr("Yêu cầu trước có nội dung khác. Kiểm tra lại khoản đã ghi trước khi tiếp tục."), IMPORT_REVIEW_REQUIRED: tr("Hãy đối chiếu các trường với tệp gốc và xác nhận trước khi lưu."), IMPORT_ALREADY_USED: tr("Tệp nguồn này đã được lưu thành hóa đơn."), IMPORT_NOT_FOUND: tr("Không tìm thấy tệp chứng từ trong tài khoản của bạn.")});
    Object.assign(messages, {SANDBOX_WORKER_UNAVAILABLE: tr("Máy chủ đang tắt worker trả kết quả thử. Nhờ người chạy app bật PROVIDER_WORKER_ENABLED và khởi động lại backend."), DOCUMENT_SOURCE_REQUIRED: tr("Tài liệu tham khảo công khai cần URL nguồn gốc.")});
    const code = result.error?.code || "API_ERROR";
    if (code === "FORBIDDEN" && result.error?.message === "Invalid local operator code") messages.FORBIDDEN = tr("Mã vận hành chưa đúng. Dùng DEMO_OPERATOR_CODE trong .env trên máy chủ, hoặc chọn phương thức sandbox tự động ở bước thanh toán.");
    if (code === "FORBIDDEN" && result.error?.message === "Origin is not allowed") messages.FORBIDDEN = tr("Địa chỉ truy cập chưa được máy chủ cho phép. Nhờ người chạy app cấu hình địa chỉ LAN bằng scripts/configure_lan.ps1.");
    if (code === "UNAUTHORIZED" && token && typeof window !== "undefined") window.dispatchEvent(new Event("baoan:unauthorized"));
    throw new Error(`${messages[code] || result.error?.message || tr("Không thể kết nối API")} (${code})`);
  }
  return result as T;
}

export async function downloadOwned(path: string, token: string, filename: string): Promise<void> {
  const response = await fetch(`${API}/api/v1${path}`, {credentials: "include", headers: authHeaders(token)});
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.error?.message || tr("Không tải được tệp. Hãy đăng nhập và thử lại."));
  }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; document.body.appendChild(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function authHeaders(token: string): Record<string, string> {
  return token.startsWith("csrf:") ? {"X-CSRF-Token": token.slice(5)} : token ? {Authorization: `Bearer ${token}`} : {};
}

export async function uploadPolicy(token: string, file: File, title: string, sourceUrl: string, language = "auto", documentKind = "USER_PROVIDED"): Promise<Policy> {
  if (!await requestFileConsent("documents")) return Promise.reject(new Error(tr("Đã hủy tải lên.")));
  const body = new FormData(); body.append("file", file); body.append("title", title); body.append("source_url", sourceUrl); body.append("language", language); body.append("document_kind", documentKind);
  const response = await fetch(`${API}/api/v1/documents`, {method: "POST", credentials: "include", headers: {...authHeaders(token), ...fileConsentHeader("documents")}, body});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || tr("Không tải được tài liệu"));
  return result;
}

export async function downloadPolicy(token: string, doc: Policy) {
  const response = await fetch(`${API}/api/v1/documents/${doc.id}/download`, {credentials: "include", headers: authHeaders(token)});
  if (!response.ok) throw new Error(tr("Không thể tải tài liệu"));
  const url = URL.createObjectURL(await response.blob()); const a = document.createElement("a"); a.href = url; a.download = doc.filename; a.click(); URL.revokeObjectURL(url);
}

export const vnd = (value: string) => `${BigInt(value.split(".")[0] || "0").toLocaleString(localeTag())} ₫`;
export const rateText = (value: string) => {const [whole, decimal = ""] = value.split("."); const fraction = decimal.replace(/0+$/, ""); return BigInt(whole).toLocaleString(localeTag()) + (fraction ? `${new Intl.NumberFormat(localeTag()).formatToParts(1.1).find(part => part.type === "decimal")?.value || "."}${fraction}` : "");};
export const time = (value: string) => new Date(value).toLocaleString(localeTag(), {timeZone: "Asia/Ho_Chi_Minh", dateStyle: "short", timeStyle: "short"});
export const labels: Record<Status, string> = localized({AWAITING_CONFIRMATION: "Chờ xác nhận", PROCESSING: "Đang xử lý", SUCCEEDED: "Mô phỏng thành công", FAILED: "Mô phỏng thất bại", CANCELLED: "Đã hủy", EXPIRED: "Đã hết hạn"});
