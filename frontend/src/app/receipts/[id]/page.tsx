"use client";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {use, useEffect, useState} from "react";
import Link from "next/link";
import {Printer, ShieldCheck} from "lucide-react";
import {api, Receipt, time, vnd} from "@/lib/api";
import {useToken} from "@/components/shell";
import {Heading, ErrorBox} from "@/components/ui";
export default function ReceiptPage({params}: {params: Promise<{id: string}>}) {
  useI18n();const {id} = use(params); const token = useToken(); const [receipt, setReceipt] = useState<Receipt>(); const [error, setError] = useState(""); useEffect(() => {api<Receipt>(`/orders/${id}/receipt`, token).then(setReceipt).catch(e => setError(e.message));}, [id, token]); return <><div className="no-print"><Heading eyebrow={tr("CHỨNG TỪ GIẢ LẬP")} title={tr("Biên nhận mô phỏng")}>{tr("Không có giá trị chứng minh thanh toán hay bảo hiểm.")}</Heading><ErrorBox message={error}/></div>{receipt && <article className="card receipt"><div className="receipt-watermark">SIMULATED</div><div className="receipt-head"><ShieldCheck size={36}/><span className="badge demo">MOCK PROVIDER</span></div><h2>{tr("Biên nhận giao dịch mô phỏng")}</h2><div className="receipt-warning">{receipt.notice}<strong>DEMO - NOT AN ACTUAL PAYMENT</strong></div><dl className="detail-list"><div><dt>{tr("Số biên nhận")}</dt><dd className="mono">{receipt.receipt_number}</dd></div><div><dt>{tr("Mã hóa đơn")}</dt><dd>{receipt.invoice_number}</dd></div><div><dt>{tr("Mã giao dịch")}</dt><dd className="mono">{receipt.order_id}</dd></div><div><dt>{tr("Ngày lập (Việt Nam)")}</dt><dd>{time(receipt.issued_at)}</dd></div><div><dt>{tr("Giá trị hóa đơn")}</dt><dd>{receipt.amount_cny} CNY</dd></div><div><dt>{tr("Tổng VND mô phỏng")}</dt><dd className="receipt-total">{vnd(receipt.total_vnd)}</dd></div></dl><p>{tr("Không chuyển tiền thật. Biên nhận này chỉ ghi nhận việc hoàn tất luồng API mô phỏng; không kích hoạt bảo hiểm và không xác nhận bên nhận được thanh toán.")}</p><div className="actions no-print"><button className="button primary" onClick={() => window.print()}><Printer size={17}/> {tr(" In biên nhận")}</button><Link className="button secondary" href={`/payments/${id}`}>{tr("Xem nhật ký")}</Link></div></article>}</>;}
