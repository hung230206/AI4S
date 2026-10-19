"use client";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {Suspense, useEffect, useState} from "react";
import {useRouter, useSearchParams} from "next/navigation";
import Link from "next/link";
import {ArrowUpRight, Clock3, Search, Download} from "lucide-react";
import {api, Order, Status, labels, time, vnd} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, ErrorBox, StatusBadge} from "@/components/ui";
import {ContextHelp} from "@/components/user-guide";
export default function History() {
  return <Suspense><HistoryContent/></Suspense>;
}
function HistoryContent() {
  useI18n();
  const router = useRouter(); const params = useSearchParams();
  const requestedStatus = params.get("status") || ""; const status = Object.hasOwn(labels, requestedStatus) ? requestedStatus : "";
  function setStatus(value: string) {const query = new URLSearchParams(params.toString()); if (Object.hasOwn(labels, value)) query.set("status", value); else query.delete("status"); router.replace("/history" + (query.size ? "?" + query.toString() : ""), {scroll: false});}
  const {token, dataVersion, invalidate} = useAuth(); const [items, setItems] = useState<Order[]>([]); const [error, setError] = useState(""); const [loaded, setLoaded] = useState(false); const [search, setSearch] = useState("");
  useEffect(() => {api<{items: Order[]}>("/orders", token).then(r => setItems(r.items)).catch(e => setError(e.message)).finally(() => setLoaded(true));}, [token, dataVersion]);
  const filtered = items.filter(o => (!status || o.status === status) && (o.id.includes(search.trim().toLowerCase()) || o.invoice_id.includes(search.trim().toLowerCase())));
  function exportCsv() {const rows = [["order_id", "invoice_id", "created_at_utc", "total_vnd", "status", "payment_mode"], ...filtered.map(o => [o.id, o.invoice_id, o.created_at, o.total_vnd, o.status, "SANDBOX"])]; const blob = new Blob(["\uFEFF" + rows.map(row => row.join(",")).join("\n")], {type: "text/csv;charset=utf-8"}); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = "demo-sandbox-history.csv"; a.click(); URL.revokeObjectURL(url);}
  return <><div className="heading-action"><Heading eyebrow={tr("LƯU VẾT RÕ RÀNG")} title={tr("Lịch sử giao dịch")}>{tr("Các lần thử thanh toán sandbox trong tài khoản của bạn. Kết quả chưa xác nhận chuyển tiền hoặc bảo hiểm.")}</Heading><button className="button secondary" onClick={invalidate}>{tr("Làm mới")}</button><button className="button secondary" disabled={!filtered.length} onClick={exportCsv}><Download size={16}/> {tr(" Xuất CSV")}</button></div><ContextHelp title={tr("Vì sao tính VND rồi mà lịch sử vẫn trống?")}><p>{tr("Lịch sử chỉ lưu giao dịch khi bạn chọn thử quy trình thanh toán. Thêm hóa đơn và xem giá trị VND chưa tạo giao dịch. Mở Hóa đơn để tiếp tục với khoản phí đã lưu.")}</p><p>{tr("Đang xử lý: chờ người vận hành phát kết quả sandbox. Mô phỏng thành công: có biên nhận thử, không xác nhận trường hoặc doanh nghiệp bảo hiểm đã nhận tiền.")}</p></ContextHelp><div className="filter-bar"><label className="search-input"><Search size={17}/><input aria-label={tr("Tìm giao dịch")} value={search} onChange={e => setSearch(e.target.value)} placeholder={tr("Tìm mã giao dịch hoặc mã hóa đơn")}/></label><select aria-label={tr("Trạng thái giao dịch")} value={status} onChange={e => setStatus(e.target.value)}><option value="">{tr("Tất cả trạng thái")}</option>{Object.entries(labels).map(([key, value]) => <option value={key} key={key}>{value}</option>)}</select></div><ErrorBox message={error}/><div className="card">{filtered.map(o => <Link className="history-row" href={`/payments/${o.id}`} key={o.id}><div><strong>#{o.id.slice(0, 8)} {tr(" · Bảo hiểm du học")}</strong><small>{time(o.created_at)} · SANDBOX</small></div><b>{vnd(o.total_vnd)}</b><StatusBadge status={o.status as Status}/><ArrowUpRight size={18}/></Link>)}{!filtered.length && <div className="empty"><Clock3 size={30}/><h2>{loaded ? tr("Chưa có giao dịch phù hợp") : tr("Đang tải lịch sử…")}</h2><p>{items.length ? tr("Thử đổi bộ lọc hoặc mã tìm kiếm.") : tr("Chưa thử thanh toán là bình thường. Bạn vẫn có thể lưu hóa đơn và tính chi phí bằng VND.")}</p><Link href="/invoices" className="button primary">{tr("Xem hóa đơn")}</Link></div>}</div></>;
}
