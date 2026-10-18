"use client";
import {useCallback, useEffect, useState} from "react";
import Link from "next/link";
import {CheckCircle2, Circle, Download, RefreshCw, ExternalLink, FlaskConical} from "lucide-react";
import {api, downloadOwned} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, ErrorBox} from "@/components/ui";

type Sample = {id: string; title: string; kind: string; language: string; expected: unknown};
type Catalog = {samples: Sample[]; public_sources: {id: string; title: string; url: string; language: string; notice: string}[]};
type Progress = {invoice: {id: string; number: string; amount_cny: string} | null; order: {id: string; status: string; scenario: string} | null; steps: Record<string, boolean>; readiness: {ocr: boolean; payment_worker: boolean; real_payments: boolean}};
const languages: Record<string, string> = {en: "Tiếng Anh", vi: "Tiếng Việt và Anh", zh: "Tiếng Trung và Anh"};

export default function TestLab() {
  const {token, dataVersion, user, logout} = useAuth();
  const [catalog, setCatalog] = useState<Catalog>();
  const [progress, setProgress] = useState<Progress>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const load = useCallback(async () => {
    try {
      const selected = new URLSearchParams(window.location.search).get("invoice");
      const [c, p] = await Promise.all([api<Catalog>("/test-lab/catalog", token), api<Progress>(`/test-lab/status${selected ? `?invoice_id=${encodeURIComponent(selected)}` : ""}`, token)]);
      setCatalog(c); setProgress(p); setError("");
    } catch (e) {setError((e as Error).message);}
  }, [token]);
  useEffect(() => {
    let active = true;
    const selected = new URLSearchParams(window.location.search).get("invoice");
    Promise.all([api<Catalog>("/test-lab/catalog", token), api<Progress>(`/test-lab/status${selected ? `?invoice_id=${encodeURIComponent(selected)}` : ""}`, token)])
      .then(([c, p]) => {if (active) {setCatalog(c); setProgress(p); setError("");}})
      .catch(e => {if (active) setError((e as Error).message);});
    return () => {active = false;};
  }, [token, dataVersion]);
  async function download(path: string, name: string) {
    setBusy(path); setError("");
    try {await downloadOwned(path, token, name);} catch (e) {setError((e as Error).message);} finally {setBusy("");}
  }
  const invoice = progress?.invoice;
  const steps = [
    {key: "reviewed_invoice", title: "1. Đọc chứng từ và lưu hóa đơn", text: "Tải mẫu hóa đơn ở dưới. Chọn đúng ngôn ngữ, đọc 5 trường, đối chiếu với bản gốc rồi tích xác nhận và lưu. Không tải nguyên ZIP vào app.", href: "/invoices/new", action: "Tải lên hóa đơn"},
    {key: "budget_plan", title: "2. Chuẩn bị ngân sách và kế hoạch", text: "Tạo sổ CNY có 1.000 CNY. Mở hóa đơn 800 CNY và Đưa vào kế hoạch chi. Dự phóng 30 ngày còn 200 CNY; số dư hiện tại vẫn 1.000 CNY.", href: invoice ? `/invoices/${invoice.id}` : "/finance", action: invoice ? "Mở hóa đơn để lập kế hoạch" : "Tạo sổ CNY"},
    {key: "reference_estimate", title: "3. Kiểm tra số VND cần chuẩn bị", text: "Mở Xem giá trị VND → Lấy tỷ giá và tính VND. Kiểm tra nguồn, ngày, số tiền và hạn báo giá. Có thể xem kịch bản ±5% trong Tỷ giá & ngân sách.", href: invoice ? `/checkout/${invoice.id}` : "/rates", action: "Xem giá trị VND"},
    {key: "policy_uploaded", title: "4. Đối chiếu tài liệu bảo hiểm", text: "Tải mẫu bảo hiểm Việt 3 trang hoặc tài liệu gốc công khai. Tìm hồ sơ bồi thường hoặc exclusions; mở trang nguồn. Tài liệu công khai là tham khảo, chưa chứng minh bảo hiểm cá nhân.", href: "/assistant", action: "Tải và tìm điều khoản"},
    {key: "sandbox_complete", title: "5. Thử thanh toán đến kết quả cuối", text: "Chọn Thành công tự động · sandbox, xem tổng, tích đồng ý rồi Chạy thử. Sau vài giây trang nhận sự kiện có chữ ký và cho mở biên nhận. Không cần mã vận hành. Dùng hóa đơn khác hoặc giao dịch mới để thử Bị từ chối tự động.", href: progress?.order?.status === "PROCESSING" ? `/payments/${progress.order.id}` : invoice ? `/checkout/${invoice.id}` : "/invoices", action: progress?.order?.status === "PROCESSING" ? "Theo dõi kết quả" : "Mở bước thanh toán thử"},
    {key: "ledger_recorded", title: "6. Ghi sổ và xuất bằng chứng", text: "Sandbox không tự trừ tiền trong sổ. Để test ghi sổ, vào Dự phóng, chọn Ghi nhận đã chi và xác nhận riêng cho kỳ hóa đơn. Số dư còn 200 CNY và kế hoạch không bị trừ hai lần. Tải hồ sơ ZIP ở trang giao dịch để team kiểm tra nguồn, consent, sự kiện và nhật ký.", href: "/finance", action: "Mở sổ để đối chiếu"},
  ];
  return <>
    <Heading eyebrow="CHẠY THỬ CÓ KẾT QUẢ KIỂM TRA" title="Test trọn luồng từ A đến Z">{user?.is_demo ? "Bạn đang dùng workspace dữ liệu mẫu chung." : "Tài khoản hiện tại dùng dữ liệu riêng."} Các tệp mẫu do nhóm tự soạn; thanh toán không chuyển tiền thật.</Heading>
    {user?.is_demo && <section className="info-note"><div><strong>Nên tạo tài khoản riêng để test độc lập</strong><p>Dữ liệu trong workspace mẫu được dùng chung. Đăng xuất rồi chọn Tạo tài khoản để bắt đầu với hóa đơn, sổ và tài liệu riêng.</p><button className="button secondary" onClick={() => logout().catch(e => setError((e as Error).message))}>Đăng xuất để tạo tài khoản riêng</button></div></section>}
    <ErrorBox message={error}/>
    <div className="lab-toolbar"><button className="button secondary" onClick={() => void load()}><RefreshCw size={16}/> Cập nhật tiến độ</button><button className="button primary" disabled={!!busy} onClick={() => download("/test-lab/download", "Demo_Upload_Test.zip")}><Download size={16}/> Tải toàn bộ dữ liệu mẫu ZIP</button></div>
    {progress && <section className="card lab-readiness"><FlaskConical size={23}/><div><strong>Kiểm tra máy chủ</strong><p>OCR: {progress.readiness.ocr ? "sẵn sàng" : "chưa cài đủ model/Node; vẫn nhập tay được"} · Provider thử: {progress.readiness.payment_worker ? "sẵn sàng trả kết quả" : "worker đang tắt; cần người chạy máy chủ bật PROVIDER_WORKER_ENABLED"}</p><small>{invoice ? `Đang theo dõi: ${invoice.number} · ${invoice.amount_cny} CNY. Tiến độ lấy từ bản ghi của bạn.` : "Chưa có hóa đơn. Bắt đầu bằng mẫu 01_en_800.png để đối chiếu ví dụ 1.000 → 200 CNY."}</small></div></section>}
    <section className="lab-steps" aria-label="Các bước kiểm thử A đến Z">{steps.map(step => <article className="card lab-step" key={step.key}>{progress?.steps[step.key] ? <CheckCircle2 className="lab-done" size={24}/> : <Circle size={24}/>}<div><h2>{step.title}</h2><p>{step.text}</p><span className={`badge ${progress?.steps[step.key] ? "reference" : "neutral"}`}>{progress?.steps[step.key] ? "Có bản ghi tương ứng" : "Chưa ghi nhận bước này"}</span><Link className="button secondary" href={step.href}>{step.action}</Link></div></article>)}</section>
    {progress?.order && <section className="card detail-card"><h2>Hồ sơ của giao dịch vừa thử</h2><p>Trạng thái: {progress.order.status}. ZIP chứa chứng từ gốc của bạn nếu có; xem trước khi chia sẻ cho team.</p><div className="actions"><Link className="button secondary" href={`/payments/${progress.order.id}`}>Mở giao dịch</Link><button className="button primary" disabled={!!busy} onClick={() => download(`/orders/${progress.order!.id}/evidence`, `demo-case-${progress.order!.id}.zip`)}>Tải hồ sơ kiểm thử ZIP</button></div></section>}
    <section className="card detail-card"><h2>Tệp để tải lên thử</h2><p>Giải nén hoặc tải từng tệp. Thư mục lỗi dùng để kiểm tra cảnh báo; đừng dùng chúng cho luồng thành công.</p>{["invoice", "policy", "error"].map(kind => <div key={kind}><h3>{kind === "invoice" ? "Hóa đơn và OCR" : kind === "policy" ? "Tài liệu bảo hiểm" : "Trường hợp lỗi có chủ đích"}</h3><div className="lab-samples">{catalog?.samples.filter(s => s.kind === kind).map(item => <article key={item.id}><div><strong>{item.title}</strong><small>Chọn ngôn ngữ: {languages[item.language]}</small></div><button className="button secondary" disabled={!!busy} onClick={() => download(`/test-lab/samples/${item.id}`, item.title)}><Download size={15}/> Tải mẫu</button></article>)}</div></div>)}</section>
    <section className="card detail-card"><h2>Tài liệu gốc công khai để thử dữ liệu thực</h2><p>Tải bản gốc ở website của trường rồi tự upload vào Tài liệu bảo hiểm. Giữ URL nguồn khi tải lên. Các bản này không phải chứng từ cá nhân của bạn.</p>{catalog?.public_sources.map(source => <article className="lab-public" key={source.id}><h3>{source.title}</h3><p>{source.notice}</p><p>Ngôn ngữ gợi ý: {languages[source.language]}</p><a className="text-link" href={source.url} target="_blank" rel="noopener noreferrer">Mở nguồn gốc <ExternalLink size={14}/></a></article>)}</section>
  </>;
}
