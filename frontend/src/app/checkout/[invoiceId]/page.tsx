"use client";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {use, useEffect, useRef, useState} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {ArrowLeft, LockKeyhole, Clock3, RefreshCw} from "lucide-react";
import {api, Invoice, Order, Quote, vnd, requestKey, SandboxScenario} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, ErrorBox, QuoteBreakdown} from "@/components/ui";
import {PaymentSteps, ContextHelp} from "@/components/user-guide";

export default function Checkout({params}: {params: Promise<{invoiceId: string}>}) {
  useI18n();
  const {invoiceId} = use(params); const {token, dataVersion, invalidate} = useAuth(); const router = useRouter();
  const [invoice, setInvoice] = useState<Invoice>(); const [quote, setQuote] = useState<Quote>(); const [order, setOrder] = useState<Order>(); const [consent, setConsent] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [seconds, setSeconds] = useState(0);
  const createKey = useRef(""); const confirmKey = useRef(""); const pendingQuote = useRef<Quote | null>(null);
  const [selectedScenario, setScenario] = useState<SandboxScenario>();
  const synthetic = invoice?.source_type === "SYNTHETIC";
  const scenario = selectedScenario ?? (synthetic ? "MANUAL" : "SUCCESS");
  useEffect(() => {api<Invoice>(`/invoices/${invoiceId}`, token).then(setInvoice).catch(e => setError(e.message));}, [invoiceId, token, dataVersion]);
  useEffect(() => {if (!quote) return; const tick = () => setSeconds(Math.max(0, Math.ceil((Date.parse(quote.expires_at) - Date.now()) / 1000))); tick(); const timer = setInterval(tick, 1000); return () => clearInterval(timer);}, [quote]);
  async function getQuote() {
    if (busy) return; setBusy(true); setError(""); setConsent(false);
    try {
      const current = await api<{items: Order[]}>("/orders", token);
      const existing = current.items.find(o => o.invoice_id === invoiceId && ["AWAITING_CONFIRMATION", "PROCESSING", "SUCCEEDED"].includes(o.status));
      if (existing) {const detail = await api<Order>(`/orders/${existing.id}`, token); if (existing.status !== "AWAITING_CONFIRMATION") {router.push(`/payments/${existing.id}`); return;} setOrder(detail); setQuote(detail.quote); confirmKey.current ||= requestKey(); return;}
      if (!pendingQuote.current || Date.parse(pendingQuote.current.expires_at) <= Date.now() || pendingQuote.current.source_amount_cny !== invoice?.amount_cny) {pendingQuote.current = await api<Quote>("/quotes", token, {invoice_id: invoiceId, settlement_currency: "VND"}); createKey.current = requestKey();}
      const q = pendingQuote.current;
      if (synthetic) setOrder(await api<Order>("/orders", token, {invoice_id: invoiceId, quote_id: q.id}, createKey.current));
      else setOrder(undefined);
      setQuote(q); confirmKey.current = requestKey();
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function confirm() {
    if (!quote || !consent || busy) return; setBusy(true); setError("");
    try {
      const saved = order || await api<Order>("/orders", token, {invoice_id: invoiceId, quote_id: quote.id}, createKey.current);
      setOrder(saved);
      await api<Order>(`/orders/${saved.id}/confirm`, token, {quote_id: quote.id, consent: true, consent_version: "demo-v1", expected_total_vnd: quote.total_vnd, sandbox_scenario: scenario}, confirmKey.current);
      invalidate(); router.push(`/payments/${saved.id}`);
    } catch (e) {setError((e as Error).message); setBusy(false);}
  }
  async function cancel() {if (!order || busy) return; setBusy(true); setError(""); try {await api(`/orders/${order.id}/cancel`, token, {}); invalidate(); router.push(`/payments/${order.id}`);} catch (e) {setError((e as Error).message); setBusy(false);}}
  return <><Link className="back-link" href={`/invoices/${invoiceId}`}><ArrowLeft size={16}/> {tr(" Chi tiết hóa đơn")}</Link><Heading eyebrow={tr("QUY ĐỔI & KIỂM TRA")} title={tr("Minh bạch trước mỗi quyết định")}>{synthetic ? tr("Thanh toán bảo hiểm du học – Bản mô phỏng. Không chuyển tiền thật.") : tr("Xem giá trị VND từ dữ liệu tỷ giá tham chiếu. Bạn có thể chọn thử quy trình thanh toán trong sandbox.")}</Heading><PaymentSteps current={quote ? 3 : 2}/><ContextHelp title={tr("Xem giá trị VND có tạo thanh toán không?")}><p>{tr("Với hóa đơn bạn nhập, lấy tỷ giá chỉ lưu bản tính chi phí. Bạn có thể đọc kết quả và dừng ở đây. Chỉ khi tích đồng ý và chọn Chạy thử thanh toán sandbox, app mới lưu giao dịch thử vào Lịch sử.")}</p><p>{tr("Sandbox là chế độ thử. Không có tiền được chuyển và không có bảo hiểm được kích hoạt. Tỷ giá tham chiếu theo ngày chưa phải tỷ giá được ngân hàng cam kết.")}</p></ContextHelp><ErrorBox message={error}/><div className="checkout-grid"><div>{quote ? <><QuoteBreakdown quote={quote}/><div className="next-action-note"><strong>{tr("Đã có giá trị VND để tham khảo")}</strong><p>{tr("Bạn có thể quay lại hóa đơn. Phần bên cạnh dành cho việc thử thanh toán, không bắt buộc.")}</p><Link className="text-link" href={`/invoices/${invoiceId}`}>{tr("Quay lại hóa đơn")}</Link></div></> : <div className="card detail-card"><span className={`badge ${synthetic ? "demo" : "reference"}`}>{synthetic ? "DEMO_RATE" : "FRANKFURTER REFERENCE"}</span><h2>{synthetic ? tr("Tạo báo giá từ máy chủ") : tr("Tính giá trị VND")}</h2><p>{invoice ? `${invoice.amount_cny} CNY · ${invoice.invoice_number}` : tr("Đang tải hóa đơn…")}</p><p className="muted">{synthetic ? tr("Báo giá có hiệu lực 10 phút. Giá trị hóa đơn, tỷ giá và phí được lấy từ dữ liệu máy chủ.") : tr("Lấy tỷ giá CNY/VND theo ngày từ Frankfurter, lưu lại nguồn và thời điểm. Tính toán bằng số thập phân tại máy chủ.")}</p><button className="button primary" disabled={busy || !invoice} onClick={getQuote}>{busy ? tr("Đang lấy báo giá…") : synthetic ? tr("Tạo báo giá mô phỏng") : tr("Lấy tỷ giá và tính VND")}</button></div>}</div><div className="card consent-card"><span className="square-icon"><LockKeyhole size={23}/></span><span className="badge neutral">{tr("TÙY CHỌN · SAU KHI XEM GIÁ")}</span><h2>{synthetic ? tr("Bạn là người xác nhận") : tr("Thử quy trình thanh toán")}</h2><p className="muted">{synthetic ? tr("Chỉ xác nhận sau khi đã xem đúng tổng tiền và hiểu đây là giao dịch giả lập.") : tr("Chỉ tiếp tục nếu bạn muốn xem cách một giao dịch được tạo và theo dõi. Không cần thao tác này để lưu kết quả quy đổi.")}</p>{quote && <div className={`expiry ${seconds === 0 ? "expired" : ""}`} role="timer"><Clock3 size={17}/>{seconds ? (tr("Báo giá còn ") + (Math.floor(seconds / 60)) + tr(":") + ((seconds % 60).toString().padStart(2, "0")) + tr("")) : tr("Báo giá đã hết hạn")}</div>}<label className="sandbox-method">{tr("Phương thức thử thanh toán")}<select aria-label={tr("Phương thức thử thanh toán")} value={scenario} disabled={busy} onChange={e => {setScenario(e.target.value as SandboxScenario); setConsent(false); confirmKey.current = requestKey();}}><option value="SUCCESS">{tr("Thành công tự động · sandbox")}</option><option value="DECLINED">{tr("Bị từ chối tự động · sandbox")}</option><option value="MANUAL">{tr("Chờ người vận hành · kiểm thử nâng cao")}</option></select></label><p className="small muted">{tr("Hai phương thức tự động trả kết quả sau vài giây qua sự kiện có chữ ký. Bạn không cần mã vận hành. Đây vẫn là giao dịch thử, không trừ tiền thật.")}</p><label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} disabled={!quote || seconds === 0 || busy}/><span>{tr("Tôi đã xem báo giá")}{quote ? ` ${vnd(quote.total_vnd)}` : ""} {tr(" và đồng ý thử quy trình sandbox, không chuyển tiền thật.")}</span></label><button className="button primary full" disabled={!consent || !quote || seconds === 0 || busy} onClick={confirm}>{busy ? tr("Đang xử lý yêu cầu…") : synthetic ? tr("Xác nhận thanh toán mô phỏng") : tr("Chạy thử thanh toán sandbox")}</button>{order && seconds > 0 && <button className="button secondary full" disabled={busy} onClick={cancel}>{tr("Hủy trước khi xử lý")}</button>}{quote && !order && seconds > 0 && <button className="button secondary full" disabled={busy} onClick={() => {pendingQuote.current = null; getQuote();}}><RefreshCw size={16}/> {tr(" Cập nhật báo giá")}</button>}{quote && seconds === 0 && <button className="button secondary full" disabled={busy} onClick={getQuote}><RefreshCw size={16}/> {tr(" Lấy báo giá mới")}</button>}<p className="small muted">{synthetic ? tr("Đồng ý gắn với báo giá chính xác. AI không xác nhận hay thực hiện thanh toán.") : tr("Chỉ tính giá trị tham chiếu chưa tạo giao dịch. Một giao dịch sandbox được lưu sau khi bạn chọn chạy thử.")}</p>{quote && <p className="mono small">Quote: {quote.id}</p>}</div></div></>;
}
