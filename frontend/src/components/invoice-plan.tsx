"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {CalendarPlus} from "lucide-react";
import {api, Invoice} from "@/lib/api";
import {Wallet} from "@/lib/finance";
import {useAuth} from "@/components/shell";
import {ErrorBox} from "@/components/ui";
export function InvoicePlan({invoice}: {invoice: Invoice}) {
  const {token, dataVersion, invalidate} = useAuth(); const [wallets, setWallets] = useState<Wallet[]>([]); const [selected, setSelected] = useState(""); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => {let active = true; api<{items: Wallet[]}>("/finance/wallets", token).then(value => {if (active) setWallets(value.items.filter(w => w.currency === "CNY"));}).catch(e => {if (active) setError(e.message);}); return () => {active = false;};}, [token, dataVersion]);
  async function add() {setBusy(true); setError(""); try {await api("/finance/plans/from-invoice", token, {invoice_id: invoice.id, wallet_id: selected || wallets[0]?.id}); setMessage("Đã đưa số tiền và hạn hóa đơn vào kế hoạch. Chưa ghi nhận chi hoặc thanh toán."); invalidate();} catch (e) {setError((e as Error).message);} finally {setBusy(false);}}
  if (invoice.status !== "OPEN" || invoice.source_type === "SYNTHETIC") return null;
  return <section className="invoice-plan"><h3><CalendarPlus size={17}/> Đưa vào ngân sách</h3><p className="small muted">Lưu một kế hoạch chi từ số tiền và hạn hiện tại của hóa đơn. Kế hoạch là bản chụp riêng, chưa trừ số dư.</p><ErrorBox message={error}/>{message ? <p className="success-note" role="status">{message} <Link className="text-link" href="/finance">Xem dự phóng →</Link></p> : wallets.length ? <><label>Sổ CNY cho khoản phí<select aria-label="Sổ CNY cho khoản phí" value={selected || wallets[0]?.id} onChange={e => setSelected(e.target.value)}>{wallets.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select></label><button className="button secondary full" disabled={busy} onClick={add}>Đưa vào kế hoạch chi</button></> : <Link className="text-link" href="/finance">Tạo sổ CNY để lập kế hoạch →</Link>}</section>;
}
