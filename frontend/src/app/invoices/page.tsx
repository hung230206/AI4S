"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {Plus, Search} from "lucide-react";
import {api, Invoice} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, InvoiceCard, ErrorBox} from "@/components/ui";
export default function Invoices() {
  const {token, dataVersion} = useAuth(); const [items, setItems] = useState<Invoice[]>([]); const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  useEffect(() => {let active = true; const timer = setTimeout(() => {api<{items: Invoice[]}>(`/invoices?q=${encodeURIComponent(search)}&status=${status}`, token).then(r => {if (active) {setItems(r.items); setError("");}}).catch(e => {if (active) setError(e.message);}).finally(() => {if (active) setLoading(false);});}, 200); return () => {active = false; clearTimeout(timer);};}, [token, search, status, dataVersion]);
  return <><div className="heading-action"><Heading eyebrow="THEO DÕI KHOẢN PHÍ" title="Hóa đơn của bạn">Lưu thông tin, kiểm tra hạn thanh toán và xem giá trị tham chiếu bằng VND.</Heading><Link href="/invoices/new" className="button primary"><Plus size={16}/> Thêm hóa đơn</Link></div><div className="filter-bar"><label className="search-input"><Search size={17}/><input aria-label="Tìm hóa đơn" value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm mã hóa đơn, đơn vị hoặc bên nhận"/></label><select aria-label="Trạng thái hóa đơn" value={status} onChange={e => setStatus(e.target.value)}><option value="">Tất cả trạng thái</option><option value="OPEN">Đang mở</option><option value="VOID">Đã lưu trữ</option></select></div><ErrorBox message={error}/>{loading ? <p role="status">Đang tải hóa đơn…</p> : items.length ? <div className="invoice-grid">{items.map(i => <InvoiceCard invoice={i} key={i.id}/>)}</div> : <div className="card empty"><h2>Chưa có hóa đơn phù hợp</h2><p>Thêm hóa đơn đầu tiên hoặc thay đổi điều kiện tìm kiếm.</p><Link href="/invoices/new" className="button primary">Thêm hóa đơn</Link></div>}</>;
}
