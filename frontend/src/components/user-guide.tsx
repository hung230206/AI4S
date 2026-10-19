"use client";
import {tr, localized} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {useRef, useState, type KeyboardEvent} from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {ArrowRight, BookOpen, CircleHelp, FileText, History, X} from "lucide-react";

const guides = localized([
  {name: "Bắt đầu", title: "Bạn muốn làm gì trước?", text: "Demo giúp bạn theo dõi khoản phí du học và đọc tài liệu bảo hiểm. Chọn một việc để bắt đầu.", steps: []},
  {name: "Hóa đơn & tỷ giá", title: "Biết cần chuẩn bị bao nhiêu VND", text: "Chuẩn bị hóa đơn hoặc thông báo thu phí có số tiền CNY, tên đơn vị và ngày đến hạn.", steps: ["Tải ảnh/PDF để tự điền, hoặc nhập tay từ thông báo thu phí. Kiểm tra số tiền, bên nhận và hạn trước khi lưu.", "Mở hóa đơn → Xem giá trị VND → Lấy tỷ giá và tính VND.", "Đối chiếu số tiền, ngày tỷ giá và tổng VND. Đến đây bạn có thể dừng; chưa có giao dịch được tạo."]},
  {name: "Tài liệu bảo hiểm", title: "Tìm điều khoản trong tài liệu của bạn", text: "Dùng hợp đồng hoặc chính sách bảo hiểm bạn đã nhận. Đây là luồng riêng, không bắt buộc có hóa đơn.", steps: ["Tải PDF, ảnh, TXT hoặc MD lên trang Tài liệu bảo hiểm. Với bản quét, app nhận dạng chữ cục bộ; hãy kiểm tra toàn văn.", "Nhập từ khóa có trong tài liệu, chẳng hạn hồ sơ bồi thường hoặc exclusions.", "Đọc đoạn trích và số trang, rồi mở toàn văn để kiểm tra ngữ cảnh. Kết quả không xác nhận quyền lợi bảo hiểm."]},
  {name: "Giao dịch thử", title: "Hiểu quy trình thanh toán bằng sandbox", text: "Sandbox là chế độ thử, không chuyển tiền và không kích hoạt bảo hiểm.", steps: ["Sau khi xem báo giá, chỉ tích đồng ý nếu bạn muốn thử quy trình.", "Chọn Chạy thử thanh toán sandbox để tạo giao dịch thử.", "Theo dõi trong Lịch sử giao dịch. Chọn phương thức tự động để nhận kết quả sau vài giây. Chế độ nâng cao mới cần người vận hành; không bấm thanh toán lại khi đang xử lý."]},
  {name: "Ngân sách", title: "Lập kế hoạch tiền cho kỳ du học", text: "Khai báo số dư riêng theo CNY/VND. Kế hoạch giúp xem trước khả năng thiếu hụt; chưa trừ tiền thật.", steps: ["Thêm sổ tiền với số dư đã đối chiếu và ngày bắt đầu theo dõi.", "Ghi thu/chi thực tế hoặc lên lịch tiền nhà, học phí và trợ cấp. Có thể đưa hóa đơn vào kế hoạch từ trang chi tiết.", "Xem Dự phóng 30/60/90 ngày. Chỉ chọn Ghi nhận đã thu/chi khi khoản đó đã xảy ra ngoài thực tế; có bước xác nhận riêng."]},
  {name: "Tác động tỷ giá", title: "Kiểm tra khoản phí có vượt ngân sách", text: "Dùng tỷ giá tham chiếu theo ngày, không dự đoán thị trường hoặc tự đổi tiền.", steps: ["Mở Tỷ giá & ngân sách để xem lịch sử CNY/VND.", "Chọn hóa đơn hoặc nhập số CNY, thêm ngân sách VND nếu có.", "Chọn Phân tích ngân sách để xem chi phí hiện tại và kịch bản tăng/giảm 5%. Phí nhà cung cấp chưa được tính."]},
]);

export function UserGuide({userId}: {userId: string}) {
  useI18n();
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const path = usePathname();
  const [tab, setTab] = useState(0);
  const storageKey = `baoan.guide.v1.${userId}`;
  function remember() {try {localStorage.setItem(storageKey, "seen");} catch { /* Optional browser preference. */ }}
  function close() {remember(); dialog.current?.close(); trigger.current?.focus();}
  function keepFocus(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== "Tab") return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], [tabindex="0"]')).filter(element => element.getClientRects().length);
    const first = controls[0]; const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last?.focus();}
    else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
  }
  function open() {
    setTab(path === "/finance" || path === "/copilot" ? 4 : path === "/rates" ? 5 : path.startsWith("/assistant") ? 2 : path.startsWith("/payments") || path === "/history" ? 3 : path.startsWith("/invoices") || path.startsWith("/checkout") ? 1 : 0);
    dialog.current?.showModal();
  }
  const guide = guides[tab];
  return <>
    <button ref={trigger} className="guide-trigger" aria-label={tr("Mở hướng dẫn sử dụng")} onClick={open}><CircleHelp size={18}/><span>{tr("Hướng dẫn")}</span></button>
    <dialog ref={dialog} className="guide-dialog" aria-labelledby="guide-title" aria-describedby="guide-description" onKeyDown={keepFocus} onCancel={event => {event.preventDefault(); close();}}>
      <div className="guide-header"><span className="eyebrow">{tr("LÀM QUEN TRONG 1 PHÚT")}</span><button className="icon-button" aria-label={tr("Đóng hướng dẫn")} onClick={close} autoFocus><X size={20}/></button></div>
      <h2 id="guide-title">{tr("Bắt đầu cùng Demo")}</h2>
      <div className="guide-topics" role="group" aria-label={tr("Chủ đề hướng dẫn")}>{guides.map((item, index) => <button aria-pressed={tab === index} className={tab === index ? "selected" : ""} key={item.name} onClick={() => setTab(index)}>{item.name}</button>)}</div>
      <div className="guide-content"><h3>{guide.title}</h3><p id="guide-description">{guide.text}</p>
        {tab === 0 ? <div className="guide-choices"><Link href="/invoices/new" onClick={close}><FileText size={24}/><strong>{tr("Tính chi phí bằng VND")}</strong><span>{tr("Nhập khoản phí CNY rồi xem giá trị quy đổi.")}</span><b>{tr("Bắt đầu với hóa đơn ")}<ArrowRight size={15}/></b></Link><Link href="/assistant" onClick={close}><BookOpen size={24}/><strong>{tr("Hiểu tài liệu bảo hiểm")}</strong><span>{tr("Tải tài liệu, tìm điều khoản và đọc trích dẫn.")}</span><b>{tr("Mở tài liệu bảo hiểm ")}<ArrowRight size={15}/></b></Link></div> : <ol className="guide-instructions">{guide.steps.map(step => <li key={step}>{step}</li>)}</ol>}
        <div className="guide-boundary"><History size={18}/><span><strong>{tr("Thanh toán hiện là thử nghiệm.")}</strong> {tr(" Xem tỷ giá và đọc tài liệu có thể dùng ngay. Giao dịch sandbox không chuyển tiền thật.")}</span></div>
      </div>
      <div className="guide-footer"><button className="text-link" onClick={close}>{tr("Để sau")}</button>{tab > 0 ? <Link className="button primary" href={tab === 4 ? "/finance" : tab === 5 ? "/rates" : tab === 2 ? "/assistant" : tab === 3 ? "/history" : "/invoices/new"} onClick={close}>{tab === 4 ? tr("Mở ngân sách") : tab === 5 ? tr("Xem tác động tỷ giá") : tab === 2 ? tr("Mở tài liệu bảo hiểm") : tab === 3 ? tr("Xem lịch sử giao dịch") : tr("Thêm hóa đơn")}<ArrowRight size={16}/></Link> : <button className="button primary" onClick={() => setTab(1)}>{tr("Xem cách dùng ")}<ArrowRight size={16}/></button>}</div>
      <p className="guide-reopen">{tr("Bạn có thể mở lại bằng nút Hướng dẫn ở đầu mỗi trang.")}</p>
    </dialog>
  </>;
}

export function PaymentSteps({current}: {current: number}) {
  useI18n();
  return <nav className="flow-steps" aria-label={tr("Các bước xử lý khoản phí")}><ol>{[tr("Hóa đơn"), tr("Giá trị VND"), tr("Xác nhận thử"), tr("Theo dõi")].map((label, index) => <li key={label} className={index + 1 < current ? "complete" : index + 1 === current ? "current" : ""} aria-current={index + 1 === current ? "step" : undefined}><span>{index + 1}</span><b>{label}</b></li>)}</ol></nav>;
}

export function ContextHelp({title, children}: {title: string; children: React.ReactNode}) {
  useI18n();
  return <details className="context-help"><summary><CircleHelp size={17}/>{title}</summary><div>{children}</div></details>;
}
