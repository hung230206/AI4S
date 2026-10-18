"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {ArrowRight, ArrowUpRight, BookOpen, CheckCircle2, Clock3, FileText, Globe2, Plus} from "lucide-react";
import {api, Invoice, Order, ReferenceRate, time, vnd, rateText} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, InvoiceCard, ErrorBox, StatusBadge} from "@/components/ui";
import {FinanceAdvice} from "@/components/finance-advice";

export function TaskDashboard() {
  const {token, user, dataVersion} = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [fx, setFx] = useState<ReferenceRate>();
  const [fxError, setFxError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const demo = Boolean(user?.is_demo);
  useEffect(() => {
    let active = true;
    Promise.all([api<{items: Invoice[]}>("/invoices", token), api<{items: Order[]}>("/orders", token)]).then(([i, o]) => {if (active) {setInvoices(i.items); setOrders(o.items);}}).catch(e => {if (active) setError(e.message);}).finally(() => {if (active) setLoading(false);});
    if (!demo) api<ReferenceRate>("/fx/latest", token).then(value => {if (active) setFx(value);}).catch(e => {if (active) setFxError(e.message);});
    return () => {active = false;};
  }, [token, demo, dataVersion]);
  const open = invoices.filter(i => i.status === "OPEN");
  const pending = orders.find(o => o.status === "PROCESSING" || o.status === "AWAITING_CONFIRMATION");
  const recentInvoice = open[0] || invoices[0];
  return <>
    <Heading eyebrow="Demo · KHÔNG GIAN DU HỌC" title="Tài chính rõ ràng. Du học an tâm.">Theo dõi khoản phí tại Trung Quốc, tính số VND cần chuẩn bị và đọc chính sách bảo hiểm.</Heading>
    <ErrorBox message={error}/>
    <section className="lab-banner"><div><strong>Thử trọn luồng từ A đến Z</strong><p>Tải chứng từ mẫu, theo dõi từng bước và nhận kết quả thanh toán sandbox tự động.</p></div><Link className="button primary" href="/test-lab">Bắt đầu test A–Z <ArrowRight size={16}/></Link></section>
    <section className="task-start" aria-labelledby="task-start-title">
      <div className="section-heading"><div><span className="eyebrow">BẮT ĐẦU TỪ ĐÂY</span><h2 id="task-start-title">Bạn muốn làm gì hôm nay?</h2></div><span className="task-time">Chọn một việc, làm theo từng bước</span></div>
      <div className="task-grid">
        <article className="task-card task-primary"><span className="task-icon"><FileText size={24}/></span><span className="task-number">01 / KHOẢN PHÍ</span><h3>Tôi cần chuẩn bị bao nhiêu tiền?</h3><p>Nhập khoản phí CNY từ hóa đơn của bạn để xem giá trị VND và ngày tỷ giá.</p><Link className="button primary" href={invoices.length ? "/invoices" : "/invoices/new"}>{invoices.length ? "Quản lý hóa đơn" : "Thêm hóa đơn đầu tiên"}<ArrowRight size={17}/></Link><small>Cần: thông báo thu phí hoặc hóa đơn</small></article>
        <article className="task-card"><span className="task-icon"><BookOpen size={24}/></span><span className="task-number">02 / BẢO HIỂM</span><h3>Tôi muốn hiểu điều khoản bảo hiểm</h3><p>Tải tài liệu lên, tìm từ khóa và đối chiếu đoạn trích kèm số trang trong bản gốc.</p><Link className="button secondary" href="/assistant">Tra cứu tài liệu bảo hiểm<ArrowRight size={17}/></Link><small>Cần: PDF có chữ, TXT hoặc MD của bạn</small></article>
      </div>
    </section>
    <section className="card getting-started" aria-labelledby="journey-title"><div><span className="eyebrow">LUỒNG KHOẢN PHÍ</span><h2 id="journey-title">Từ hóa đơn đến giá trị VND</h2><p>Bạn có thể dừng sau bước tính VND. Thử thanh toán là lựa chọn thêm.</p></div><ol><li className={invoices.length ? "done" : ""}><span>{invoices.length ? <CheckCircle2 size={18}/> : "1"}</span><div><strong>Thêm hóa đơn</strong><small>Lưu số CNY, đơn vị và hạn trả</small></div></li><li><span>2</span><div><strong>Xem giá trị VND</strong><small>Kiểm tra tỷ giá, nguồn và tổng tiền</small></div></li><li><span>3</span><div><strong>Thử quy trình nếu cần</strong><small>Sandbox, không chuyển tiền thật</small></div></li></ol></section>
    {pending && <div className="continue-card"><Clock3 size={23}/><div><strong>{pending.status === "PROCESSING" ? "Bạn có giao dịch thử đang xử lý" : "Bạn có giao dịch thử chưa xác nhận"}</strong><p>{pending.status === "PROCESSING" ? "Mở trạng thái để theo dõi. Không cần tạo thêm một giao dịch." : "Xem lại số tiền trước khi quyết định tiếp tục hoặc hủy."}</p></div><Link className="button secondary" href={`/payments/${pending.id}`}>Tiếp tục theo dõi<ArrowRight size={16}/></Link></div>}
    <div className="finance-quick-links"><Link href="/finance"><strong>Ngân sách & thu chi</strong><span>Sổ CNY/VND · Lịch thu chi · Dự phóng 30 ngày</span><ArrowRight size={18}/></Link><Link href="/rates"><strong>Tỷ giá & ngân sách</strong><span>Lịch sử tham chiếu · Kiểm tra tác động tăng/giảm</span><ArrowRight size={18}/></Link></div><FinanceAdvice/><section className="stats-grid" aria-label="Tổng quan giao dịch">{[{label: "Hóa đơn đang mở", value: open.length, icon: FileText}, {label: "Đang xử lý sandbox", value: orders.filter(o => o.status === "PROCESSING").length, icon: Clock3}, {label: "Hoàn tất sandbox", value: orders.filter(o => o.status === "SUCCEEDED").length, icon: CheckCircle2}].map(s => <div className="stat-card" key={s.label}><span className="stat-icon"><s.icon size={20}/></span><div><span>{s.label}</span><strong>{loading ? "—" : s.value.toString().padStart(2, "0")}</strong></div></div>)}</section>
    <div className="dashboard-columns"><section><div className="section-heading"><h2>Hóa đơn của bạn</h2><Link href="/invoices/new" className="text-link"><Plus size={15}/> Thêm hóa đơn</Link></div>{loading ? <p role="status">Đang tải hóa đơn…</p> : recentInvoice ? <><InvoiceCard invoice={recentInvoice}/><Link className="button secondary full" href="/invoices">Xem tất cả {invoices.length} hóa đơn</Link></> : <div className="card empty"><FileText size={30}/><h2>Chưa có hóa đơn</h2><p>Bắt đầu bằng khoản phí bảo hiểm hoặc y tế ghi trên thông báo của trường. Lưu hóa đơn chưa tạo giao dịch.</p><Link className="text-link" href="/invoices/new">Tạo hóa đơn của tôi <ArrowRight size={15}/></Link></div>}</section>
      <section><div className="section-heading"><h2>{demo ? "Bạn đang dùng bản mẫu" : "Tỷ giá để lập kế hoạch"}</h2><Globe2 size={20}/></div><div className="card detail-card rate-overview">{demo ? <><span className="badge demo">DỮ LIỆU MẪU · SANDBOX</span><h3>Thử trước khi nhập dữ liệu của bạn</h3><p>Các hóa đơn có sẵn và tỷ giá cố định chỉ để thử quy trình. Tạo tài khoản cá nhân để lưu hóa đơn và tài liệu riêng.</p><Link className="text-link" href="/account">Mở tài khoản để đăng xuất và đăng ký <ArrowRight size={15}/></Link></> : fx ? <><span className="badge reference">FRANKFURTER · REFERENCE</span><p className="muted">1 CNY (Nhân dân tệ) tương đương</p><strong className="live-rate">{rateText(fx.rate)} <span>VND</span></strong><dl className="detail-list"><div><dt>Ngày dữ liệu</dt><dd>{fx.rate_date}</dd></div><div><dt>Đồng bộ gần nhất</dt><dd>{time(fx.fetched_at)}</dd></div></dl>{fx.is_stale && <p className="small">Đang dùng bản đã lưu do nguồn tỷ giá chưa kết nối lại.</p>}<a className="text-link" href={fx.source_url} target="_blank" rel="noreferrer">Xem nguồn Frankfurter ↗</a><p className="small muted">Tỷ giá theo ngày để ước tính chi phí; số tiền thực trả còn tùy nhà cung cấp thanh toán.</p></> : <><ErrorBox message={fxError}/>{!fxError && <p role="status">Đang lấy tỷ giá tham chiếu…</p>}</>}</div></section>
    </div>
    <section className="recent-section"><div className="section-heading"><h2>Giao dịch thử gần đây</h2><Link href="/history" className="text-link">Xem lịch sử<ArrowRight size={15}/></Link></div><div className="card">{orders.length ? orders.slice(0, 3).map(o => <Link className="history-row" href={`/payments/${o.id}`} key={o.id}><div><strong>Giao dịch #{o.id.slice(0, 8)}</strong><small>{time(o.created_at)}</small></div><b>{vnd(o.total_vnd)}</b><StatusBadge status={o.status}/><ArrowUpRight size={17}/></Link>) : <div className="empty"><Clock3 size={27}/><h3>Chưa có giao dịch</h3><p>Chỉ xem giá trị VND sẽ không xuất hiện ở đây. Lịch sử ghi nhận khi bạn chọn thử quy trình thanh toán.</p></div>}</div></section>
  </>;
}
