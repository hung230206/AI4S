"use client";
import {use, useEffect, useRef, useState} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {ArrowLeft, LockKeyhole, Clock3, RefreshCw} from "lucide-react";
import {api, Invoice, Order, Quote, vnd, requestKey, SandboxScenario} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, ErrorBox, QuoteBreakdown} from "@/components/ui";
import {PaymentSteps, ContextHelp} from "@/components/user-guide";

export default function Checkout({params}: {params: Promise<{invoiceId: string}>}) {
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
  return <><Link className="back-link" href={`/invoices/${invoiceId}`}><ArrowLeft size={16}/> Chi tiết hóa đơn</Link><Heading eyebrow="QUY ĐỔI & KIỂM TRA" title="Minh bạch trước mỗi quyết định">{synthetic ? "Thanh toán bảo hiểm du học – Bản mô phỏng. Không chuyển tiền thật." : "Xem giá trị VND từ dữ liệu tỷ giá tham chiếu. Bạn có thể chọn thử quy trình thanh toán trong sandbox."}</Heading><PaymentSteps current={quote ? 3 : 2}/><ContextHelp title="Xem giá trị VND có tạo thanh toán không?"><p>Với hóa đơn bạn nhập, lấy tỷ giá chỉ lưu bản tính chi phí. Bạn có thể đọc kết quả và dừng ở đây. Chỉ khi tích đồng ý và chọn Chạy thử thanh toán sandbox, app mới lưu giao dịch thử vào Lịch sử.</p><p>Sandbox là chế độ thử. Không có tiền được chuyển và không có bảo hiểm được kích hoạt. Tỷ giá tham chiếu theo ngày chưa phải tỷ giá được ngân hàng cam kết.</p></ContextHelp><ErrorBox message={error}/><div className="checkout-grid"><div>{quote ? <><QuoteBreakdown quote={quote}/><div className="next-action-note"><strong>Đã có giá trị VND để tham khảo</strong><p>Bạn có thể quay lại hóa đơn. Phần bên cạnh dành cho việc thử thanh toán, không bắt buộc.</p><Link className="text-link" href={`/invoices/${invoiceId}`}>Quay lại hóa đơn</Link></div></> : <div className="card detail-card"><span className={`badge ${synthetic ? "demo" : "reference"}`}>{synthetic ? "DEMO_RATE" : "FRANKFURTER REFERENCE"}</span><h2>{synthetic ? "Tạo báo giá từ máy chủ" : "Tính giá trị VND"}</h2><p>{invoice ? `${invoice.amount_cny} CNY · ${invoice.invoice_number}` : "Đang tải hóa đơn…"}</p><p className="muted">{synthetic ? "Báo giá có hiệu lực 10 phút. Giá trị hóa đơn, tỷ giá và phí được lấy từ dữ liệu máy chủ." : "Lấy tỷ giá CNY/VND theo ngày từ Frankfurter, lưu lại nguồn và thời điểm. Tính toán bằng số thập phân tại máy chủ."}</p><button className="button primary" disabled={busy || !invoice} onClick={getQuote}>{busy ? "Đang lấy báo giá…" : synthetic ? "Tạo báo giá mô phỏng" : "Lấy tỷ giá và tính VND"}</button></div>}</div><div className="card consent-card"><span className="square-icon"><LockKeyhole size={23}/></span><span className="badge neutral">TÙY CHỌN · SAU KHI XEM GIÁ</span><h2>{synthetic ? "Bạn là người xác nhận" : "Thử quy trình thanh toán"}</h2><p className="muted">{synthetic ? "Chỉ xác nhận sau khi đã xem đúng tổng tiền và hiểu đây là giao dịch giả lập." : "Chỉ tiếp tục nếu bạn muốn xem cách một giao dịch được tạo và theo dõi. Không cần thao tác này để lưu kết quả quy đổi."}</p>{quote && <div className={`expiry ${seconds === 0 ? "expired" : ""}`} role="timer"><Clock3 size={17}/>{seconds ? `Báo giá còn ${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, "0")}` : "Báo giá đã hết hạn"}</div>}<label className="sandbox-method">Phương thức thử thanh toán<select aria-label="Phương thức thử thanh toán" value={scenario} disabled={busy} onChange={e => {setScenario(e.target.value as SandboxScenario); setConsent(false); confirmKey.current = requestKey();}}><option value="SUCCESS">Thành công tự động · sandbox</option><option value="DECLINED">Bị từ chối tự động · sandbox</option><option value="MANUAL">Chờ người vận hành · kiểm thử nâng cao</option></select></label><p className="small muted">Hai phương thức tự động trả kết quả sau vài giây qua sự kiện có chữ ký. Bạn không cần mã vận hành. Đây vẫn là giao dịch thử, không trừ tiền thật.</p><label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} disabled={!quote || seconds === 0 || busy}/><span>Tôi đã xem báo giá{quote ? ` ${vnd(quote.total_vnd)}` : ""} và đồng ý thử quy trình sandbox, không chuyển tiền thật.</span></label><button className="button primary full" disabled={!consent || !quote || seconds === 0 || busy} onClick={confirm}>{busy ? "Đang xử lý yêu cầu…" : synthetic ? "Xác nhận thanh toán mô phỏng" : "Chạy thử thanh toán sandbox"}</button>{order && seconds > 0 && <button className="button secondary full" disabled={busy} onClick={cancel}>Hủy trước khi xử lý</button>}{quote && !order && seconds > 0 && <button className="button secondary full" disabled={busy} onClick={() => {pendingQuote.current = null; getQuote();}}><RefreshCw size={16}/> Cập nhật báo giá</button>}{quote && seconds === 0 && <button className="button secondary full" disabled={busy} onClick={getQuote}><RefreshCw size={16}/> Lấy báo giá mới</button>}<p className="small muted">{synthetic ? "Đồng ý gắn với báo giá chính xác. AI không xác nhận hay thực hiện thanh toán." : "Chỉ tính giá trị tham chiếu chưa tạo giao dịch. Một giao dịch sandbox được lưu sau khi bạn chọn chạy thử."}</p>{quote && <p className="mono small">Quote: {quote.id}</p>}</div></div></>;
}
