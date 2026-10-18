"use client";
import Link from "next/link";
import {ArrowRight, FileText, ShieldCheck, AlertCircle} from "lucide-react";
import {Invoice, Quote, Status, labels, feeLabels, vnd, rateText, time} from "@/lib/api";

export function StatusBadge({status}: {status: Status}) {return <span className={`badge status-${status}`}>{labels[status]}</span>;}
export function ErrorBox({message}: {message: string}) {return message ? <div className="error" role="alert" aria-label="Lỗi thao tác"><AlertCircle size={18}/>{message}</div> : null;}
export function Heading({eyebrow, title, children}: {eyebrow: string; title: string; children?: React.ReactNode}) {return <div className="page-heading"><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{children && <p>{children}</p>}</div>;}

export function InvoiceCard({invoice}: {invoice: Invoice}) {
  const synthetic = invoice.source_type === "SYNTHETIC";
  return <article className="card invoice-card"><div className="card-top"><span className="square-icon"><FileText size={23}/></span><span className="badge neutral">{synthetic ? "SYNTHETIC DEMO DATA" : "DO BẠN NHẬP"}</span></div><h3>{feeLabels[invoice.fee_type] || "Khoản phí du học"}</h3><p className="muted">Trung Quốc · {invoice.invoice_number}</p><div className="invoice-amount">{invoice.amount_cny} <span>CNY</span></div><dl className="meta-list"><div><dt>{synthetic ? "Đơn vị giả định" : "Đơn vị phát hành"}</dt><dd>{invoice.institution_name}</dd></div><div><dt>Hạn thanh toán</dt><dd>{new Date(`${invoice.due_date}T00:00:00+07:00`).toLocaleDateString("vi-VN")}</dd></div><div><dt>Trạng thái hóa đơn</dt><dd>{invoice.status === "VOID" ? "Đã lưu trữ" : "Đang mở"}</dd></div></dl><Link href={`/invoices/${invoice.id}`} className="button primary full">Xem hóa đơn <ArrowRight size={17}/></Link></article>;
}

export function QuoteBreakdown({quote}: {quote: Quote}) {
  const reference = quote.rate_source === "FRANKFURTER_REFERENCE";
  return <div className="card quote-card"><div className="section-heading"><h2>Chi tiết báo giá</h2><span className={`badge ${reference ? "reference" : "demo"}`}>{reference ? "FRANKFURTER" : "DEMO_RATE"}</span></div><div className="currency-route"><div><span>Hóa đơn gốc</span><strong>{quote.source_amount_cny} CNY</strong></div><ArrowRight size={20}/><div><span>Giá trị tham chiếu</span><strong>VND</strong></div></div><div className="rate-note">1 CNY = {rateText(quote.vnd_per_cny)} VND · {reference ? `Ngày dữ liệu: ${quote.rate_date}` : "Tỷ giá cố định của sandbox"}</div>{reference && <p className="small muted rate-attribution"><a href="https://frankfurter.dev/" target="_blank" rel="noreferrer">Nguồn: Frankfurter ↗</a>{quote.rate_fetched_at && ` · Đồng bộ: ${time(quote.rate_fetched_at)}`}{quote.rate_is_stale && " · Đang dùng bản đã lưu, chưa đồng bộ được"}</p>}<dl className="breakdown"><div><dt>Giá trị quy đổi</dt><dd>{vnd(quote.converted_subtotal_vnd)}</dd></div><div><dt>Phí dịch vụ ({quote.variable_fee_rate_percent.replace(/0+$/, "").replace(/\.$/, "")}%)</dt><dd>{vnd(quote.variable_fee_vnd)}</dd></div><div><dt>Phí cố định</dt><dd>{vnd(quote.fixed_fee_vnd)}</dd></div><div className="total"><dt>{reference ? "Tổng tham chiếu" : "Tổng cộng mô phỏng"}</dt><dd>{vnd(quote.total_vnd)}</dd></div></dl><p className="small muted"><ShieldCheck size={14}/>{reference ? "Tỷ giá tham chiếu theo ngày. Chưa bao gồm phí của nhà cung cấp thanh toán; chưa phải cam kết đổi ngoại tệ." : "Tính toán và lưu tại máy chủ. Tỷ giá thử nghiệm của sandbox."}</p></div>;
}
